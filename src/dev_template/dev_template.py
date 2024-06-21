import argparse
import configparser
import os
import platform
import shutil
import subprocess
import sys
from typing import List

from colorama import Fore, Style, init
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.formatted_text import HTML
from pydantic import BaseModel, DirectoryPath, ValidationError, field_validator
from tqdm import tqdm

""" TODO:
- find way to deploy /templates directory with package -> use pkg_resources? -> copies templates to config/dev_template/templates
- utilize default_project_path from config.ini
- utilize skip_setup from config.ini
- utilize skip_pyproject from config.ini
- if pytest is not installed, don't import to test_main.py
- if pydantic is not installed, don't import to main.py
- split test_install_packages_and_verify_imports into test_base_install and test_package_install
"""

CYAN = Fore.CYAN
PURPLE = Fore.MAGENTA
YELLOW = Fore.YELLOW
RED = Fore.RED
WHITE = Fore.WHITE
RESET = Style.RESET_ALL

RESERVED_FILE_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


class ProjectConfig(BaseModel):
    project_path: DirectoryPath
    project_name: str
    additional_packages: List[str]

    @field_validator("project_name")
    def project_name_valid(cls, project_name):
        if project_name.upper() in RESERVED_FILE_NAMES:
            raise ValueError("Project name is reserved on Windows")
        return project_name


def create_project_structure(config: ProjectConfig) -> None:
    init(autoreset=True)

    full_project_path = os.path.join(config.project_path, config.project_name)

    print(f"{CYAN}Creating project directory...{RESET}")
    create_project_directory(full_project_path)
    print(f"{PURPLE}Creating project directory - Done{RESET}\n")

    print(f"{CYAN}Creating subdirectories...{RESET}")
    create_subdirectories(full_project_path, config.project_name)
    print(f"{PURPLE}Creating subdirectories - Done{RESET}\n")

    create_basic_files(full_project_path, config.project_name)

    create_virtualenv(full_project_path, config.project_name)

    install_packages(full_project_path, config.project_name, config.additional_packages)


def create_project_directory(full_project_path: str) -> None:
    try:
        os.makedirs(full_project_path, exist_ok=True)
    except Exception as e:
        raise ValueError(f"Could not create project directory: {e}")


def create_subdirectories(full_project_path: str, project_name: str) -> None:
    os.makedirs(os.path.join(full_project_path, "src", project_name), exist_ok=True)
    os.makedirs(os.path.join(full_project_path, "tests"), exist_ok=True)


def create_basic_files(full_project_path: str, project_name: str) -> None:
    config_path = get_config_path()
    config = configparser.ConfigParser()
    config.read(os.path.join(config_path, "config.ini"))

    skip_setup = config.getboolean("DEFAULT", "skip_setup", fallback=False)
    skip_pyproject = config.getboolean("DEFAULT", "skip_pyproject", fallback=False)

    template_dir = os.path.join(config_path, "templates")

    files_to_create = {
        "README.md": "README.md",
        ".gitignore": ".gitignore",
        "requirements.txt": "requirements.txt",
        "src/{project_name}/__init__.py": os.path.join("src", "__init__.py"),
        "src/{project_name}/main.py": os.path.join("src", "main.py"),
        "tests/__init__.py": os.path.join("tests", "__init__.py"),
        "tests/test_main.py": os.path.join("tests", "test_main.py"),
    }

    if not skip_setup:
        files_to_create["setup.py"] = "setup.py"

    if not skip_pyproject:
        files_to_create["pyproject.toml"] = "pyproject.toml"

    with tqdm(
        total=len(files_to_create),
        desc=f"{CYAN}Creating basic files{RESET}",
        ncols=100,
        leave=True,
    ) as progress_bar:
        for dest_template, src_template in files_to_create.items():
            dest_file = os.path.join(
                full_project_path, dest_template.format(project_name=project_name)
            )
            src_file = os.path.join(template_dir, src_template)

            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            shutil.copyfile(src_file, dest_file)
            progress_bar.update(1)
    print(f"{PURPLE}Creating basic files - Done{RESET}\n")


def create_virtualenv(full_project_path: str, project_name: str) -> None:
    venv_path = os.path.join(full_project_path, f"{project_name}_venv")
    with tqdm(
        total=1,
        desc=f"{CYAN}Creating virtual environment{RESET}",
        ncols=100,
        leave=True,
    ) as progress_bar:
        subprocess.check_call([sys.executable, "-m", "venv", venv_path])
        progress_bar.update(1)
    print(f"{PURPLE}Creating virtual environment - Done{RESET}\n")


def install_packages(
    full_project_path: str, project_name: str, additional_packages: list
) -> None:
    default_packages = read_default_packages()
    venv_path = os.path.join(full_project_path, f"{project_name}_venv")
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    all_packages = default_packages + additional_packages

    if not all_packages:
        print(f"{YELLOW}No packages to install. Skipping...{RESET}")
        return

    successful_packages = []
    failed_packages = []

    with tqdm(
        total=len(all_packages),
        desc=f"{CYAN}Installing packages{RESET}",
        ncols=100,
        leave=True,
    ) as progress_bar:
        for package in all_packages:
            try:
                subprocess.check_call(
                    [os.path.join(venv_path, bin_dir, "pip"), "install", package],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                successful_packages.append(package)
            except subprocess.CalledProcessError:
                failed_packages.append(package)
            progress_bar.update(1)

    if successful_packages:
        cyan_packages = ", ".join(
            [f"{CYAN}{package}{RESET}" for package in successful_packages]
        )
        print(f"{PURPLE}Successfully installed packages{WHITE}: {cyan_packages}{RESET}")

    if failed_packages:
        white_packages = ", ".join(
            [f"{WHITE}{package}{RESET}" for package in failed_packages]
        )
        print(f"{RED}Failed to install packages{WHITE}: {white_packages}{RESET}")

    with open(os.path.join(full_project_path, "requirements.txt"), "a") as f:
        for package in additional_packages:
            if package in successful_packages:
                f.write(f"{package}\n")

    main_py_path = os.path.join(full_project_path, f"src/{project_name}/main.py")
    with open(main_py_path, "r") as f:
        main_py_content = f.read()

    with open(main_py_path, "w") as f:
        for package in additional_packages:
            if package in successful_packages:
                f.write(f"import {package}\n")
        f.write(main_py_content)

    pyproject_toml_path = os.path.join(full_project_path, "pyproject.toml")
    with open(pyproject_toml_path, "a") as f:
        for package in additional_packages:
            if package in successful_packages:
                f.write(f'{package} = "*"\n')

    print(f"{PURPLE}Installing packages - Done{RESET}\n")


def get_config_path() -> str:
    if platform.system() == "Windows":
        config_path = os.path.join(
            os.getenv("LOCALAPPDATA"), "dev_template", "config.ini"
        )
    else:
        config_path = os.path.join(
            os.path.expanduser("~"), ".config", "dev_template", "config.ini"
        )
    return config_path


def read_default_packages() -> list:
    config_path = get_config_path()
    config_file = os.path.join(config_path, "config.ini")
    if not os.path.exists(config_file):
        print(f"{RED}Configuration file not found at {config_file}{RESET}")
        return []

    config = configparser.ConfigParser()
    config.read(config_file)

    default_packages = config.get("DEFAULT", "default_packages", fallback="").split(",")
    return [package.strip() for package in default_packages if package.strip()]


def prompt_with_path_completion(prompt_text: str) -> str:
    session = PromptSession()
    return session.prompt(HTML(prompt_text), completer=PathCompleter())


def prompt_with_simple_completion(prompt_text: str) -> str:
    session = PromptSession()
    return session.prompt(HTML(prompt_text))


def initialize_config() -> None:
    config_path = get_config_path()
    config_dir = os.path.dirname(config_path)

    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    if not os.path.exists(config_path):
        config = configparser.ConfigParser()
        config["DEFAULT"] = {
            "default_packages": "",
            "default_project_path": "",
            "skip_setup": "0",
            "skip_pyproject": "0",
        }

        with open(config_path, "w") as f:
            config.write(f)


def setup_config() -> None:
    initialize_config()
    config_path = get_config_path()
    config = configparser.ConfigParser()
    config.read(config_path)

    default_packages = prompt_with_simple_completion(
        "<yellow>Enter default packages to install (comma separated): </yellow>"
    )
    default_project_dir = prompt_with_path_completion(
        "<yellow>Enter default project directory: </yellow>"
    )

    def get_bool_input(prompt_text: str) -> str:
        while True:
            value = prompt_with_simple_completion(prompt_text).strip().lower()
            if value in {"yes", "y", "no", "n"}:
                return "1" if value in {"yes", "y"} else "0"
            else:
                print(f"{RED}Invalid input. Please enter Yes/Y or No/N.{RESET}")

    skip_setup = get_bool_input("<yellow>Skip setup prompt? (Yes/Y or No/N): </yellow>")
    skip_pyproject = get_bool_input(
        "<yellow>Skip pyproject.toml prompt? (Yes/Y or No/N): </yellow>"
    )

    config["DEFAULT"]["default_packages"] = default_packages
    config["DEFAULT"]["default_project_path"] = default_project_dir
    config["DEFAULT"]["skip_setup"] = skip_setup
    config["DEFAULT"]["skip_pyproject"] = skip_pyproject

    with open(config_path, "w") as f:
        config.write(f)
    print(f"\n{PURPLE}Configuration updated at {config_path}{RESET}")


def display_help() -> None:
    help_text = """
    Usage: dev_template [OPTIONS]

    Options:
      --config, -c      Setup configuration
      --help, -h        Show this help message and exit
    """
    print(help_text)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--config", "-c", action="store_true", help="Setup configuration"
    )
    parser.add_argument("--help", "-h", action="store_true", help="Show help message")
    args = parser.parse_args()

    if args.config:
        setup_config()
        return
    if args.help:
        display_help()
        return

    initialize_config()
    while True:
        try:
            init(autoreset=True)
            print_formatted_text(
                HTML(
                    f"<cyan>{'='*33}</cyan>\n<cyan>{'| setting up new Python project |':^30}</cyan>\n<cyan>{'='*33}</cyan>"
                )
            )

            while True:
                project_name = prompt_with_simple_completion(
                    "<yellow>Enter the project name: </yellow>"
                )
                if not project_name.strip():
                    print_formatted_text(
                        HTML("<red>Error: Project name cannot be empty</red>")
                    )
                    continue
                try:
                    _ = ProjectConfig(
                        project_name=project_name,
                        project_path="/",
                        additional_packages=[],
                    )
                    break
                except ValidationError as e:
                    print_formatted_text(
                        HTML(f"<red>Error: {e.errors()[0]['msg']}</red>")
                    )

            while True:
                project_path = prompt_with_path_completion(
                    "<yellow>Enter the fully qualified path to create the project: </yellow>"
                )
                if not project_path:
                    print_formatted_text(
                        HTML("<red>Error: Fully qualified path cannot be empty</red>")
                    )
                    continue
                if not os.path.exists(project_path):
                    print_formatted_text(
                        HTML(
                            f"<red>Error: The path '{project_path}' does not exist</red>"
                        )
                    )
                    continue
                if not os.access(project_path, os.W_OK):
                    print_formatted_text(
                        HTML(
                            f"<red>Error: You do not have write permissions for the path '{project_path}'</red>"
                        )
                    )
                    continue
                try:
                    _ = ProjectConfig(
                        project_name=project_name,
                        project_path=project_path,
                        additional_packages=[],
                    )
                    break
                except ValidationError as e:
                    print_formatted_text(
                        HTML(f"<red>Error: {e.errors()[0]['msg']}</red>")
                    )

            additional_packages = prompt_with_simple_completion(
                "<yellow>Enter additional packages to install (comma separated): </yellow>"
            ).split(",")
            additional_packages = [
                package.strip() for package in additional_packages if package.strip()
            ]

            config = ProjectConfig(
                project_name=project_name,
                project_path=project_path,
                additional_packages=additional_packages,
            )

            if not project_path.endswith("/"):
                project_path += "/"

            full_project_path = os.path.join(project_path, project_name)

            print_formatted_text(
                HTML(
                    f"\n<purple>Setting up project '<cyan>{project_name}</cyan>' at '<cyan>{full_project_path}</cyan>'</purple>\n"
                )
            )

            create_project_structure(config)

            print_formatted_text(
                HTML(
                    f"\n<purple>Project '<cyan>{project_name}</cyan>' created successfully at '<cyan>{full_project_path}</cyan>'.</purple>"
                )
            )
            break

        except (ValidationError, ValueError) as e:
            print_formatted_text(HTML(f"<red>Error: {str(e)}</red>"))
            input(f"{YELLOW}Press Enter to try again...{RESET}")
        except KeyboardInterrupt:
            print(f"\n{RED}Operation cancelled by user. Exiting...{RESET}")
            sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{RED}Operation cancelled by user. Exiting...{RESET}")
        sys.exit(0)