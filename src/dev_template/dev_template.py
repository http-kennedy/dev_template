import argparse
import configparser
import importlib.resources as package_resources
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

from colorama import Fore, Style, init
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.formatted_text import HTML
from pydantic import BaseModel, DirectoryPath, ValidationError, validator
from tqdm import tqdm

""" TODO:
- update setup.py template
- update pyproject.toml template
- pyproject.toml still gets made if skipped due to additional packages
- split test_install_packages_and_verify_imports into test_base_install and test_package_install
- duplicate packages listed as successful
"""

CYAN = Fore.CYAN
PURPLE = Fore.MAGENTA
GREEN = Fore.GREEN
YELLOW = Fore.YELLOW
RED = Fore.RED
WHITE = Fore.WHITE
RESET = Style.RESET_ALL

CONFIG = {}
DEFAULT_PACKAGES = []
DEFAULT_PROJECT_PATH = ""
SKIP_SETUP = False
SKIP_PYPROJECT = False
TEMPLATES_COPIED = False
RESERVED_FILE_NAMES = set()


class ProjectConfig(BaseModel):
    project_path: DirectoryPath
    project_name: str
    successful_packages: List[str]

    @validator("project_name")
    def project_name_valid(cls, project_name):
        if project_name.upper() in RESERVED_FILE_NAMES:
            raise ValueError(
                f"Project name '{project_name}' is reserved... Please choose a different name.\n"
            )
        return project_name


def format_text(text: str, color: str) -> str:
    return f"<{color}>{text}</{color}>"


def initialize_globals() -> None:
    global \
        CONFIG, \
        DEFAULT_PACKAGES, \
        DEFAULT_PROJECT_PATH, \
        SKIP_SETUP, \
        SKIP_PYPROJECT, \
        TEMPLATES_COPIED, \
        RESERVED_FILE_NAMES

    CONFIG["config_dir"] = get_config_path()
    CONFIG["config_path"] = os.path.join(CONFIG["config_dir"], "config.ini")

    config_path = CONFIG["config_path"]
    if not os.path.exists(config_path):
        initialize_config()

    config = configparser.ConfigParser()
    config.read(config_path)

    DEFAULT_PACKAGES = config.get("DEFAULT", "default_packages", fallback="").split(",")
    DEFAULT_PROJECT_PATH = config.get("DEFAULT", "default_project_path", fallback="")
    SKIP_SETUP = config.getboolean("DEFAULT", "skip_setup", fallback=False)
    SKIP_PYPROJECT = config.getboolean("DEFAULT", "skip_pyproject", fallback=False)
    TEMPLATES_COPIED = config.getboolean("DEFAULT", "templates_copied", fallback=False)
    RESERVED_FILE_NAMES = set(
        name.strip().upper()
        for name in config.get("DEFAULT", "reserved_file_names", fallback="").split(",")
    )


def get_config_path() -> str:
    if platform.system() == "Windows":
        config_dir = os.path.join(os.getenv("LOCALAPPDATA"), "dev_template")
    else:
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "dev_template")
    return config_dir


def initialize_config() -> None:
    config_dir = CONFIG["config_dir"]
    config_path = CONFIG["config_path"]

    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    if not os.path.exists(config_path):
        config = configparser.ConfigParser()
        config["DEFAULT"] = {
            "default_packages": "",
            "default_project_path": "",
            "skip_setup": "0",
            "skip_pyproject": "0",
            "templates_copied": "0",
            "reserved_file_names": "CON, PRN, AUX, NUL, COM1, COM2, COM3, COM4, COM5, COM6, COM7, COM8, COM9, LPT1, LPT2, LPT3, LPT4, LPT5, LPT6, LPT7, LPT8, LPT9, bin, boot, dev, etc, lib, lib64, proc, run, sbin, srv, sys, tmp, var",
        }

        with open(config_path, "w") as f:
            config.write(f)


def setup_config() -> None:
    """
    Sets up the configuration by prompting the user for input and updating the config.ini file.
    """
    initialize_config()
    config_path = CONFIG["config_path"]
    config = configparser.ConfigParser()
    config.read(config_path)

    default_packages = prompt_with_simple_completion(
        "<yellow>Enter default packages to install (comma delimited): </yellow>"
    )

    session = PromptSession()
    prompt_message = HTML("<yellow>Enter default project directory: </yellow>")

    while True:
        response = session.prompt(prompt_message, completer=PathCompleter())
        default_project_dir = response.strip()
        if default_project_dir or default_project_dir == "":
            break
        print_formatted_text(
            HTML(format_text("Error: Path cannot be empty...\n", "red"))
        )

    def get_bool_input(prompt_text: str) -> str:
        while True:
            value = prompt_with_simple_completion(prompt_text).strip().lower()
            if value in {"yes", "y", "no", "n"}:
                return "1" if value in {"yes", "y"} else "0"
            print(f"{RED}Invalid input. Please enter Yes/Y or No/N.{RESET}")

    skip_setup = get_bool_input(
        "<yellow>Skip setup.py creation? (Yes/Y or No/N): </yellow>"
    )
    skip_pyproject = get_bool_input(
        "<yellow>Skip pyproject.toml creation? (Yes/Y or No/N): </yellow>"
    )

    config["DEFAULT"]["default_packages"] = default_packages
    config["DEFAULT"]["default_project_path"] = default_project_dir
    config["DEFAULT"]["skip_setup"] = skip_setup
    config["DEFAULT"]["skip_pyproject"] = skip_pyproject

    with open(config_path, "w") as f:
        config.write(f)
    print(f"\n{PURPLE}Configuration updated at {config_path}{RESET}")


def copy_templates() -> None:
    template_dest_path = Path(CONFIG["config_dir"]) / "templates"

    if not template_dest_path.exists():
        template_dest_path.mkdir(parents=True)

    with package_resources.path("dev_template", "templates") as template_src_path:
        for item in template_src_path.rglob("*"):
            relative_path = item.relative_to(template_src_path)
            dest_path = template_dest_path / relative_path
            if item.is_dir():
                dest_path.mkdir(parents=True, exist_ok=True)
            else:
                shutil.copy2(item, dest_path)

    config_path = CONFIG["config_path"]
    config = configparser.ConfigParser()
    config.read(config_path)
    config.set("DEFAULT", "templates_copied", "1")
    with open(config_path, "w") as configfile:
        config.write(configfile)


def prompt_with_path_completion(prompt_text: str, default_value: str = "") -> str:
    session = PromptSession()
    prompt_message = HTML(
        f"{prompt_text} \n[Press Enter to use default: <green>{default_value}</green>]: "
        if default_value
        else prompt_text
    )

    while True:
        response = session.prompt(prompt_message, completer=PathCompleter())
        path = response.strip() if response.strip() else default_value
        if path:
            return path

        print_formatted_text(
            HTML(format_text("Error: Path cannot be empty...\n", "red"))
        )


def prompt_with_simple_completion(prompt_text: str) -> str:
    session = PromptSession()
    return session.prompt(HTML(prompt_text))


def run_setup():
    if not TEMPLATES_COPIED:
        copy_templates()
        print("Templates copied successfully")


def get_project_name() -> str:
    while True:
        project_name = prompt_with_simple_completion(
            format_text("Enter the project name: ", "yellow")
        )
        if project_name.strip():
            try:
                _ = ProjectConfig(
                    project_name=project_name,
                    project_path="/",
                    successful_packages=[],
                )
                return project_name
            except ValidationError as e:
                print_formatted_text(
                    HTML(format_text(f"Error: {e.errors()[0]['msg']}", "red"))
                )
        else:
            print_formatted_text(
                HTML(format_text("Error: Project name cannot be empty...\n", "red"))
            )


def get_project_path(default_project_path: str, allow_empty: bool = False) -> str:
    session = PromptSession()
    if default_project_path:
        prompt_message = f"<yellow>Press Enter to use default path</yellow> '<green>{default_project_path}</green>' <yellow>or enter new absolute path: </yellow>"
    else:
        prompt_message = "<yellow>Enter absolute path to create the project: </yellow>"

    while True:
        print_formatted_text(HTML(prompt_message))
        response = session.prompt(completer=PathCompleter())
        project_path = response.strip() if response.strip() else default_project_path
        print(f"Project path: {project_path}")

        if project_path or allow_empty:
            if project_path and (
                os.path.exists(project_path) and os.access(project_path, os.W_OK)
            ):
                return project_path
            elif allow_empty:
                return project_path

        error_message = (
            f"Error: The path '{project_path}' does not exist"
            if not os.path.exists(project_path)
            else f"Error: You do not have write permissions for the path... '{project_path}'"
        )
        print_formatted_text(HTML(format_text(error_message, "red")))


def get_packages() -> List[str]:
    default_packages_str = ", ".join(package.strip() for package in DEFAULT_PACKAGES)
    prompt_text = "Enter successful packages to install (comma delimited): "

    session = PromptSession()
    successful_packages = session.prompt(
        HTML(format_text(prompt_text, "yellow")), default=default_packages_str
    ).split(",")

    return [package.strip() for package in successful_packages if package.strip()]


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

    successful_packages = install_packages(
        full_project_path, config.project_name, config.successful_packages
    )

    if successful_packages:
        write_successful_packages_to_files(
            full_project_path,
            config.project_name,
            successful_packages,
        )


def create_project_directory(full_project_path: str) -> None:
    try:
        os.makedirs(full_project_path, exist_ok=True)
    except Exception as e:
        raise ValueError(f"Could not create project directory: {e}")


def create_subdirectories(full_project_path: str, project_name: str) -> None:
    os.makedirs(os.path.join(full_project_path, "src", project_name), exist_ok=True)
    os.makedirs(os.path.join(full_project_path, "tests"), exist_ok=True)


def create_basic_files(full_project_path: str, project_name: str) -> None:
    template_dir = os.path.join(CONFIG["config_dir"], "templates")

    files_to_create = {
        "README.md": "README.md",
        ".gitignore": ".gitignore",
        "requirements.txt": "requirements.txt",
        "src/{project_name}/__init__.py": os.path.join("src", "__init__.py"),
        "src/{project_name}/main.py": os.path.join("src", "main.py"),
        "tests/__init__.py": os.path.join("tests", "__init__.py"),
        "tests/test_main.py": os.path.join("tests", "test_main.py"),
    }

    if not SKIP_SETUP:
        files_to_create["setup.py"] = "setup.py"

    if not SKIP_PYPROJECT:
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
    full_project_path: str, project_name: str, packages: list
) -> List[str]:
    venv_path = os.path.join(full_project_path, f"{project_name}_venv")
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    packages = list(set(packages))

    if not packages:
        print(f"{YELLOW}No packages to install. Skipping...{RESET}")
        return []

    successful_packages = []
    failed_packages = []

    with tqdm(
        total=len(packages),
        desc=f"{CYAN}Installing packages{RESET}",
        ncols=100,
        leave=True,
    ) as progress_bar:
        for package in packages:
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
        installed_packages_str = ", ".join(
            [f"{CYAN}{package}{RESET}" for package in successful_packages]
        )
        print(
            f"{PURPLE}Successfully installed packages: {installed_packages_str}{RESET}"
        )

    if failed_packages:
        failed_packages_str = ", ".join(
            [f"{RED}{package}{RESET}" for package in failed_packages]
        )
        print(f"{RED}Failed to install packages: {failed_packages_str}{RESET}")

    print(f"{PURPLE}Installing packages - Done{RESET}")
    return successful_packages


def get_installed_packages(venv_path: str) -> Dict[str, str]:
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    freeze_output = subprocess.check_output(
        [os.path.join(venv_path, bin_dir, "pip"), "freeze"], text=True
    )
    return dict(line.split("==") for line in freeze_output.splitlines())


def write_successful_packages_to_files(
    full_project_path: str,
    project_name: str,
    successful_packages: List[str],
) -> None:
    venv_path = os.path.join(full_project_path, f"{project_name}_venv")
    package_versions = get_installed_packages(venv_path)

    files_to_update = {
        "requirements.txt": lambda: successful_packages,
        "pyproject.toml": lambda: successful_packages if not SKIP_PYPROJECT else None,
        f"src/{project_name}/main.py": lambda: [
            f"import {package}\n" for package in successful_packages
        ],
    }

    print()
    with tqdm(
        total=len(files_to_update),
        desc=f"{CYAN}Updating files{RESET}",
        ncols=100,
        leave=True,
    ) as progress_bar:
        for file, packages in files_to_update.items():
            package_lines = packages()
            if package_lines:
                file_path = os.path.join(full_project_path, file)
                with open(file_path, "a") as f:
                    if file == "requirements.txt":
                        for package in successful_packages:
                            if package in package_versions:
                                f.write(f"{package}=={package_versions[package]}\n")
                    else:
                        f.writelines(package_lines)
            progress_bar.update(1)

    print(f"{PURPLE}Writing successful packages to files - Done{RESET}\n")


def display_help() -> None:
    help_text = """
    Usage: dev_template [OPTIONS]

    Options:
      --config, -c      Setup configuration
      --help, -h        Show this help message and exit
    """
    print(help_text)


def main():
    initialize_globals()
    print("Globals initialized")

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

    run_setup()

    print(f"Default project path: {DEFAULT_PROJECT_PATH}")

    while True:
        try:
            init(autoreset=True)
            print_formatted_text(
                HTML(
                    format_text("=" * 33, "cyan")
                    + "\n"
                    + format_text("| setting up new Python project |", "cyan")
                    + "\n"
                    + format_text("=" * 33, "cyan")
                )
            )

            project_name = get_project_name()
            project_path = get_project_path(DEFAULT_PROJECT_PATH)
            packages = get_packages()

            config = ProjectConfig(
                project_name=project_name,
                project_path=project_path,
                successful_packages=packages,
            )

            if not project_path.endswith("/"):
                project_path += "/"

            full_project_path = os.path.join(project_path, project_name)
            print(f"Full project path: {full_project_path}")

            print_formatted_text(
                HTML(
                    format_text(
                        f"\nSetting up project '<cyan>{project_name}</cyan>' at '<cyan>{full_project_path}</cyan>'\n",
                        "purple",
                    )
                )
            )

            create_project_structure(config)

            print_formatted_text(
                HTML(
                    format_text(
                        f"\nProject '<cyan>{project_name}</cyan>' created successfully at '<cyan>{full_project_path}</cyan>'.",
                        "purple",
                    )
                )
            )
            break

        except (ValidationError, ValueError) as e:
            print_formatted_text(HTML(format_text(f"Error: {str(e)}", "red")))
            input(format_text("Press Enter to try again...", "yellow"))
        except KeyboardInterrupt:
            print(f"{RED}Operation cancelled by user. Exiting...{RESET}")
            sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"{RED}Operation cancelled by user. Exiting...{RESET}")
        sys.exit(0)
