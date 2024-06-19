import os
import shutil
import subprocess
import sys
from unittest.mock import call, patch

import pytest
from src.module.dev_template import (
    create_basic_files,
    create_project_directory,
    create_subdirectories,
    create_virtualenv,
    install_packages,
)


@pytest.fixture
def setup_project_path():
    project_name = "testproject"
    project_path = "/tmp/testprojects/"
    full_project_path = os.path.join(project_path, project_name)
    additional_packages = ["colorama"]
    yield project_name, project_path, full_project_path, additional_packages
    if os.path.exists(full_project_path):
        shutil.rmtree(full_project_path)
    if os.path.exists(project_path) and not os.listdir(project_path):
        os.rmdir(project_path)


def test_create_project_directory(setup_project_path):
    project_name, project_path, full_project_path, additional_packages = (
        setup_project_path
    )
    create_project_directory(full_project_path)
    assert os.path.exists(full_project_path)


def test_create_subdirectories(setup_project_path):
    project_name, project_path, full_project_path, additional_packages = (
        setup_project_path
    )
    create_project_directory(full_project_path)
    create_subdirectories(full_project_path, project_name)
    assert os.path.exists(os.path.join(full_project_path, "src", project_name))
    assert os.path.exists(os.path.join(full_project_path, "tests"))


def test_create_basic_files(setup_project_path):
    project_name, project_path, full_project_path, additional_packages = (
        setup_project_path
    )
    create_project_directory(full_project_path)
    create_subdirectories(full_project_path, project_name)
    create_basic_files(full_project_path, project_name)
    assert os.path.isfile(os.path.join(full_project_path, "README.md"))
    assert os.path.isfile(os.path.join(full_project_path, ".gitignore"))
    assert os.path.isfile(os.path.join(full_project_path, "requirements.txt"))
    assert os.path.isfile(os.path.join(full_project_path, "setup.py"))
    assert os.path.isfile(os.path.join(full_project_path, "pyproject.toml"))
    assert os.path.isfile(
        os.path.join(full_project_path, "src", project_name, "__init__.py")
    )
    assert os.path.isfile(
        os.path.join(full_project_path, "src", project_name, "main.py")
    )
    assert os.path.isfile(os.path.join(full_project_path, "tests", "__init__.py"))
    assert os.path.isfile(os.path.join(full_project_path, "tests", "test_main.py"))


@patch("subprocess.check_call")
def test_create_virtualenv(mock_subprocess, setup_project_path):
    project_name, project_path, full_project_path, additional_packages = (
        setup_project_path
    )
    create_virtualenv(full_project_path, project_name)
    venv_path = os.path.join(full_project_path, f"{project_name}_venv")
    mock_subprocess.assert_called_once_with([sys.executable, "-m", "venv", venv_path])


@patch("subprocess.check_call")
def test_install_packages_and_verify_imports(mock_subprocess, setup_project_path):
    project_name, project_path, full_project_path, additional_packages = (
        setup_project_path
    )
    create_project_directory(full_project_path)
    create_subdirectories(full_project_path, project_name)
    create_virtualenv(full_project_path, project_name)
    create_basic_files(full_project_path, project_name)

    install_packages(full_project_path, project_name, additional_packages)
    venv_path = os.path.join(full_project_path, f"{project_name}_venv", "bin", "pip")
    expected_calls = [
        call(
            [venv_path, "install", "pydantic"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
        call(
            [venv_path, "install", "pytest"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
        call(
            [venv_path, "install", "setuptools"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
        call(
            [venv_path, "install", "wheel"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
    ]
    expected_calls += [
        call(
            [venv_path, "install", package],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for package in additional_packages
    ]
    mock_subprocess.assert_has_calls(expected_calls, any_order=True)

    main_py_path = os.path.join(full_project_path, "src", project_name, "main.py")
    with open(main_py_path, "r") as f:
        content = f.read()
        lines = content.split("\n")
        assert "import pydantic" in lines
        for package in additional_packages:
            assert f"import {package}" in lines

    test_main_py_path = os.path.join(full_project_path, "tests", "test_main.py")
    with open(test_main_py_path, "r") as f:
        content = f.read()
        lines = content.split("\n")
        assert "import pytest" in lines
