import pathlib

from setuptools import find_packages, setup

HERE = pathlib.Path(__file__).parent
requirements_path = HERE / "requirements.txt"
with open(requirements_path, encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="dev_template",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "dev_template = module.dev_template:main",
        ],
    },
    extras_require={"test": ["pytest"]},
)
