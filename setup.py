from setuptools import setup, find_packages

setup(
    name="dev_template",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[],
    entry_points={
        "console_scripts": [
            "dev_template = src.main:main",
        ],
    },
)
