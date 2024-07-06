# Why?

The `dev_template` tool is designed with simplicity and speed in mind, providing a streamlined approach to setting up new Python projects. Unlike other feature-rich tools, `dev_template` focuses on quick development, allowing you to get started without the need to wade through extensive documentation (_hopefully_).

This tool was created to help enforce _better_ development standards, even for quick tools and hobbyist programs. It offers essential features that facilitate a consistent project structure and dependency management, making it ideal for developers who need a reliable setup process without the overhead of complex configurations.

For those who want a bit more customization, the project's `README` provides clear instructions on how to modify templates and configuration settings. Everything you need to know is right there, making it easy to tailor the tool to fit your specific needs. (_If you still have/find issues please submit an issue_).

With `dev_template`, you can start your projects quickly, maintain _good_ development practices, and avoid the hassle of extensive setup processes and documentation crawling.

## TLDR

_this tool is for those of us that are lazy_

## Features

* **User-Friendly**

* **Interactive Prompts:**
  * Utilizes interactive prompts with directory path completion.

* **Cross-Platform Compatibility:**
  * Handles platform-specific differences for paths and commands (e.g., Windows vs. Unix-like systems).

* **Project Directory Creation:**
  * Creates a new project directory structure, including subdirectories (`src`, `tests`) and basic files (`README.md`, `.gitignore`, `requirements.txt`, etc.).
  * Optionally creates `setup.py` and `pyproject.toml` based on configuration settings.

* **Configuration Management:**
  * Uses a configuration file to manage default settings like packages to install, project path, and templates.
  * Provides an interactive setup configuration option to modify default settings.

* **Template Copying:**
  * Copies predefined templates for project files from a configured templates directory.
  * Ability to replace template files in the config directory with their own personalized versions.

* **Virtual Environment Management:**
  * Automatically creates a virtual environment for the new project.
  * Installs specified packages into the virtual environment.

* **Package Management:**
  * Installs packages specified by the user or from the default configuration.
  * Allows specifying exact package versions during creation.
  * Updates `requirements.txt` and `pyproject.toml` with successfully installed packages and their versions.

* **Error Handling:**
  * Provides comprehensive error handling and logging for various operations, including directory creation, package installation, and user input validation.

* **Logging:**
  * Supports debug logging for detailed execution trace.

## Example Demo

![Demo GIF](https://raw.githubusercontent.com/http-kennedy/dev_template/main/images/1.1.3.gif)

## Example Project Structure

```shell
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
├── setup.py (creation disabled by default)
└── pyproject.toml (creation enabled by default)

```

### Pip Installation & Usage

To install the package using pip, run the following command:

```shell
pip install dev-template
```

Once installed, you can start the tool by typing the following command in your terminal:

```shell
dev_template
```

Alternatively, you can run it as a Python module:

```shell
python -m dev_template.dev_template
```

After setting up your project, navigate into the project directory and activate the virtual environment.

* **The virtual environment folder is named after your project (e.g., project_venv).**

For Linux/macOS:

```shell
source project_venv/bin/activate
```

For Windows (Powershell):

```shell
.\project_venv\Scripts\Activate.ps1
```

To deactivate the virtual environment, simply type:

```shell
deactivate
```

## Source Installation & Usage

1. Clone the repository, navigate to the project directory, create and activate a virtual environment:

* On MacOS/Linux:

```batch
git clone https://github.com/http-kennedy/dev_template.git
cd dev_template
python -m venv venv
source venv/bin/activate
```

* On Windows (Powershell):

```batch
git clone https://github.com/http-kennedy/dev_template.git
cd dev_template
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install the requirements:

```bash
pip install -r requirements.txt
```

3. Install the package:

* For interactive development (editable mode):

```shell
pip install -e .
```

* To install directly:

```shell
pip install .
```

Once installed, you can start the tool by typing the following command in your terminal:

```shell
dev_template
```

Alternatively, you can run the script directly:

```shell
python src/dev_template/dev_template.py
```

After setting up your project, navigate into the project directory and activate the virtual environment.

* **The virtual environment folder is named after your project (e.g., project_venv).**

For Linux/macOS:

```batch
source project_venv/bin/activate
```

For Windows (Powershell):

```powershell
.\project_venv\Scripts\Activate.ps1
```

To deactivate the virtual environment, simply type:

```shell
deactivate
```

## Command-Line Options

The `dev_template` tool can be ran with various flags to perform different actions. Here are the available options:

* `-h`, `--help`:
  * Displays the help message with information about all available options.

* `-c`, `--config`:
  * Enters configuration mode, allowing you to customize default settings such as default packages to install, default directory for projects, and whether to create `setup.py` and `pyproject.toml` files.

* `-d`, `--debug`:
  * Enables debug logging for more detailed output during execution.
  * **Log File Locations**
    * Linux/macOS:
      * Log files: ~/.config/dev_template/logs
    * Windows:
      * Log files: %LOCALAPPDATA%\dev_template\logs

## Configuration Mode

The `dev_template` tool offers a configuration mode to customize default settings. You can enter configuration mode by running:

```shell
dev_template -c
```

or

```shell
dev_template --config
```

When in configuration mode you can set the following values:

* Default packages to install:
  * Packages must be `commma delimited`.
  * Can be modified during normal execution of `dev_template`
  * If defining a specific version use pip's version specifier syntax.
    * `'package_name'=='version'`
    * For example: ```pandas==2.1.4```

* Absolute path for default project directory creation:
  * Sets default input for where to create the project.
  * Can be modified during normal execution of `dev_template`

* Create `setup.py` for new project directories:
  * Choose whether to create a `setup.py` file in new project directories.
  * Default is set to `No`

* Create `pyproject.toml` for new project directories:
  * Choose whether to create a `pyproject.toml` file in new project directories.
  * Default is set to `Yes`

**Configuration File Locations**

* Linux/macOS:
  * Configuration file: ~/.config/dev_template/config.ini
  * Templates directory: ~/.config/dev_template/templates/

* Windows:
  * Configuration file: %LOCALAPPDATA%\dev_template\config.ini
  * Templates directory: %LOCALAPPDATA%\dev_template\templates\

### Customizing Templates

* If you replace or modify any of the template files in the templates directory using the **same filename/s**, the customized files will be used during project setup.

## Roadmap

### Improvements

* **Logging Wrapper**: Implement a standardized logging wrapper.
* **Typer Package**: Enhance the command-line interface using the `typer` package.

### Features to Add

* Store virtual environments in the project directory or a user-specified location.
* Add version management and update notifications.
* Add an argument to remake the configuration directory.
* Allow custom project structures via the templates directory.

### NOTES TO REMEBER

----------------------
* If you need to install a specific package verison, use pip's version specifier syntax.
  * `'package_name'=='version'`
  * For example: ```pandas==2.1.4```

### KNOWN ISSUES

----------------------

* pyproject.toml: The `dependencies` section must be present in the `pyproject.toml` file. The absence of this section can cause installation issues.

* Config Template Directory: Problems may arise if not all expected files are present in the templates directory. Ensure that all necessary template files are included to avoid errors.
  * Workaround: Delete`config directory` and re-run `dev_template`.
    * For Linux/macOS:
      * `~/.config/dev_template`
    * For Windows:
      * `%LOCALAPPDATA%\dev_template`
