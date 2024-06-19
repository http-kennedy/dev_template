# dev_template

A module to quickly generate a basic Python project template without the fluff.

## Features

* Creates a basic python project template
* Initalizes a virtual environment for the project
* Ability to add user-defined packages during setup
* Installs required (pydantic, pytest) and user defined packages into venv
* Standard Python .gitignore (also ignores _venv directory)
* Adds required (pydantic, pytest) and user defined packages to requirements.txt
* Imports user defined packages during setup to main.py
* Prebuilds setup.py
* Prebuilds pyproject.toml

## Example Demo
![Demo GIF](https://raw.githubusercontent.com/http-kennedy/dev_template/main/images/dev_template.gif)

## Example Project Structure

```
project
├── project_venv
├── src
│   └── project
│       ├── __init__.py
│       └── main.py
├── tests
│   ├── __init__.py
│   └── test_main.py
├── .gitignore
├── README.md
├── requirements.txt
├── setup.py
└── pyproject.toml

```

## Installation

To install the package, use pip:

```bash
pip install dev-template
```

## Usage

Once installed type the following command into your terminal:

```bash
dev_template
```

or

```bash
python -m module.dev_template
```

Once project setup is done navigate into the project directory and type the following command to activate the venv:
* the folder that has the venv is named after your project. In this example we are using `project`

Linux
```bash
source project_venv/bin/activate
```

Powershell
```bash
.\project_venv\Scripts\Activate.ps1
```

To deactivate the venv type the following command into your terminal:

```bash
deactivate
```