# src/module/dev_template.py

import os
import subprocess
import sys
from typing import List

from colorama import Fore, Style, init
from pydantic import BaseModel, DirectoryPath, ValidationError, field_validator
from tqdm import tqdm

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
    create_subdirectories(full_project_path)
    print(f"{PURPLE}Creating subdirectories - Done{RESET}\n")

    create_basic_files(full_project_path, config.project_name)

    create_virtualenv(full_project_path, config.project_name)

    install_packages(full_project_path, config.project_name, config.additional_packages)


def create_project_directory(full_project_path: str) -> None:
    try:
        os.makedirs(full_project_path, exist_ok=True)
    except Exception as e:
        raise ValueError(f"Could not create project directory: {e}")


def create_subdirectories(full_project_path: str) -> None:
    os.makedirs(os.path.join(full_project_path, "src"), exist_ok=True)
    os.makedirs(os.path.join(full_project_path, "tests"), exist_ok=True)


def create_basic_files(full_project_path: str, project_name: str) -> None:
    files_content = {
        "README.md": f"# {project_name.capitalize()}\n",
        ".gitignore": f"__pycache__/\n*.pyc\n.env\n{project_name}_venv/\n",
        "requirements.txt": "pydantic\npytest\n",
        "setup.py": f"""from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={{"": "src"}},
    install_requires=[],
    entry_points={{
        "console_scripts": [
            "{project_name} = src.main:main",
        ],
    }},
)
""",
        "src/__init__.py": """# src/__init__.py
# This file is intentionally left blank.
""",
        "src/main.py": """import pydantic

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
""",
        "tests/__init__.py": """# tests/__init__.py
# This file is intentionally left blank.
""",
        "tests/test_main.py": """import pytest

def test_example():
    assert True
""",
    }

    with tqdm(
        total=len(files_content),
        desc=f"{CYAN}Creating basic files{RESET}",
        ncols=100,
        leave=True,
    ) as pbar:
        for filename, content in files_content.items():
            with open(os.path.join(full_project_path, filename), "w") as f:
                f.write(content)
            pbar.update(1)
    print(f"{PURPLE}Creating basic files - Done{RESET}\n")


def create_virtualenv(full_project_path: str, project_name: str) -> None:
    venv_path = os.path.join(full_project_path, f"{project_name}_venv")
    with tqdm(
        total=1,
        desc=f"{CYAN}Creating virtual environment{RESET}",
        ncols=100,
        leave=True,
    ) as pbar:
        subprocess.check_call([sys.executable, "-m", "venv", venv_path])
        pbar.update(1)
    print(f"{PURPLE}Creating virtual environment - Done{RESET}\n")


def install_packages(
    full_project_path: str, project_name: str, additional_packages: list
) -> None:
    venv_path = os.path.join(full_project_path, f"{project_name}_venv")
    all_packages = ["pydantic", "pytest"] + additional_packages
    successful_packages = []
    failed_packages = []

    with tqdm(
        total=len(all_packages),
        desc=f"{CYAN}Installing packages{RESET}",
        ncols=100,
        leave=True,
    ) as pbar:
        for package in all_packages:
            try:
                subprocess.check_call(
                    [os.path.join(venv_path, "bin", "pip"), "install", package],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                successful_packages.append(package)
            except subprocess.CalledProcessError:
                failed_packages.append(package)
            pbar.update(1)

    if successful_packages:
        cyan_packages = ", ".join(
            [f"{CYAN}{pkg}{RESET}" for pkg in successful_packages]
        )
        print(f"{PURPLE}Successfully installed packages{WHITE}: {cyan_packages}{RESET}")

    if failed_packages:
        white_packages = ", ".join([f"{WHITE}{pkg}{RESET}" for pkg in failed_packages])
        print(f"{RED}Failed to install packages{WHITE}: {white_packages}{RESET}")

    # add successful user-defined packages to requirements.txt and import into src/main.py (exclude pydantic and pytest which are already added)
    with open(os.path.join(full_project_path, "requirements.txt"), "a") as f:
        for package in additional_packages:
            if package in successful_packages:
                f.write(f"{package}\n")

    with open(os.path.join(full_project_path, "src/main.py"), "r") as f:
        main_py_content = f.read()

    with open(os.path.join(full_project_path, "src/main.py"), "w") as f:
        for package in additional_packages:
            if package in successful_packages:
                f.write(f"import {package}\n")
        f.write(main_py_content)

    print(f"{PURPLE}Installing packages - Done{RESET}\n")


def main():
    while True:
        try:
            init(autoreset=True)
            print(f"{CYAN}{'='*30}\n{'Python Project Setup':^30}\n{'='*30}")

            while True:
                project_name = input(f"{YELLOW}Enter the project name: {RESET}")
                if not project_name.strip():
                    print(f"{RED}Error: Project name cannot be empty{RESET}")
                    continue
                try:
                    _ = ProjectConfig(
                        project_name=project_name,
                        project_path="/",
                        additional_packages=[],
                    )
                    break
                except ValidationError as e:
                    print(f"{RED}Error: {e.errors()[0]['msg']}{RESET}")

            while True:
                project_path = input(
                    f"\n{YELLOW}Enter the fully qualified path to create the project: {RESET}"
                )
                if not project_path:
                    print(f"{RED}Error: Fully qualified path cannot be empty{RESET}")
                    continue
                if not os.path.exists(project_path):
                    print(
                        f"{RED}Error: The path '{project_path}' does not exist{RESET}"
                    )
                    continue
                if not os.access(project_path, os.W_OK):
                    print(
                        f"{RED}Error: You do not have write permissions for the path '{project_path}'{RESET}"
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
                    print(f"{RED}Error: {e.errors()[0]['msg']}{RESET}")

            additional_packages = input(
                f"\n{YELLOW}Enter additional packages to install (comma separated): {RESET}"
            ).split(",")
            additional_packages = [
                pkg.strip() for pkg in additional_packages if pkg.strip()
            ]

            config = ProjectConfig(
                project_name=project_name,
                project_path=project_path,
                additional_packages=additional_packages,
            )

            if not project_path.endswith("/"):
                project_path += "/"

            full_project_path = os.path.join(project_path, project_name)

            print(
                f"\n{PURPLE}Setting up project '{CYAN}{project_name}{PURPLE}' at '{CYAN}{full_project_path}{PURPLE}'\n"
            )

            create_project_structure(config)

            print(
                f"\n{PURPLE}Project '{CYAN}{project_name}{PURPLE}' created successfully at '{CYAN}{full_project_path}{PURPLE}'.{RESET}"
            )
            break

        except (ValidationError, ValueError) as e:
            print(f"{RED}Error: {str(e)}{RESET}")
            input(f"{YELLOW}Press Enter to try again...{RESET}")


if __name__ == "__main__":
    main()
