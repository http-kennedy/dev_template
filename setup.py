import pathlib

from setuptools import find_packages, setup

HERE = pathlib.Path(__file__).parent
readme_path = HERE / "README.md"
with open(readme_path, encoding="utf-8") as f:
    long_description = f.read()

HERE = pathlib.Path(__file__).parent
requirements_path = HERE / "requirements.txt"
with open(requirements_path, encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="dev_template",
    version="1.0.2",
    description="A module to generate a Python project template.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Kennedy",
    author_email="kennedy@mylaptop.dev",
    url="https://github.com/http-kennedy/dev_template",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "dev_template = module.dev_template:main",
        ],
    },
    extras_require={"test": ["pytest"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    license="CC0-1.0",
)
