import logging
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, mock_open, patch

from dev_template.dev_template import (
    CONFIG,
    copy_templates,
    create_basic_files,
    create_project_directory,
    create_subdirectories,
    create_virtualenv,
    install_packages,
    setup_logging,
    update_pyproject_toml,
    update_requirements_txt,
    write_successful_packages_to_files,
)


class TestDevTemplate(unittest.TestCase):
    def setUp(self):
        self.config_dir = "/mock/config/dir"
        self.config_path = os.path.join(self.config_dir, "config.ini")
        CONFIG["config_dir"] = self.config_dir
        CONFIG["config_path"] = self.config_path

    @patch("dev_template.dev_template.package_resources.path")
    @patch("dev_template.dev_template.shutil.copy2")
    @patch("dev_template.dev_template.Path.mkdir")
    @patch("dev_template.dev_template.os.path.exists")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="[DEFAULT]\ntemplates_copied=0\n",
    )
    def test_copy_templates(
        self,
        mock_open,
        mock_path_exists,
        mock_mkdir,
        mock_copy2,
        mock_package_resources_path,
    ):
        mock_template_src_path = MagicMock(spec=Path)
        mock_package_resources_path.return_value.__enter__.return_value = (
            mock_template_src_path
        )

        mock_template_src_path.rglob.return_value = [
            Path("/mock/src/dir/file1"),
            Path("/mock/src/dir/dir1"),
            Path("/mock/src/dir/dir1/file2"),
        ]

        def mock_relative_to(self, other):
            return Path(self.parts[-1])

        with patch.object(Path, "relative_to", new=mock_relative_to):
            mock_path_exists.return_value = True

            def copy2_side_effect(src, dst):
                print(f"shutil.copy2 called with src={src}, dst={dst}")

            def mkdir_side_effect(parents=True, exist_ok=False):
                print(f"Path.mkdir called with parents={parents}, exist_ok={exist_ok}")

            mock_copy2.side_effect = copy2_side_effect
            mock_mkdir.side_effect = mkdir_side_effect

            print(
                f"Expected config source path: {os.path.join(os.path.dirname(__file__), 'config', 'config.ini')}"
            )
            print(f"Expected config destination path: {CONFIG['config_path']}")

            copy_templates()

            mock_mkdir.assert_any_call(parents=True)
            mock_copy2.assert_any_call(
                Path("/mock/src/dir/file1"), Path("/mock/config/dir/templates/file1")
            )
            mock_copy2.assert_any_call(
                Path("/mock/src/dir/dir1/file2"),
                Path("/mock/config/dir/templates/file2"),
            )

            print("Actual shutil.copy2 calls:", mock_copy2.call_args_list)

            mock_open().write.assert_any_call("templates_copied = 1\n")

    @patch("os.makedirs")
    @patch("logging.basicConfig")
    @patch("logging.info")
    @patch("os.listdir")
    @patch("os.remove")
    @patch("os.path.getmtime")
    def test_setup_logging(
        self,
        mock_getmtime,
        mock_remove,
        mock_listdir,
        mock_logging_info,
        mock_basicConfig,
        mock_makedirs,
    ):
        log_id = "test_log_id"
        max_log_files = 5
        debug = True

        mock_listdir.return_value = [
            "log1.log",
            "log2.log",
            "log3.log",
            "log4.log",
            "log5.log",
            "log6.log",
        ]

        mock_getmtime.side_effect = lambda x: {
            "log1.log": 1,
            "log2.log": 2,
            "log3.log": 3,
            "log4.log": 4,
            "log5.log": 5,
            "log6.log": 6,
        }[os.path.basename(x)]

        setup_logging(log_id, max_log_files, debug)
        mock_makedirs.assert_called_once_with(
            os.path.join(self.config_dir, "logs"), exist_ok=True
        )

        mock_basicConfig.assert_called_once_with(
            filename=os.path.join(self.config_dir, "logs", f"{log_id}.log"),
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        mock_remove.assert_any_call(os.path.join(self.config_dir, "logs", "log1.log"))

    @patch("os.makedirs")
    def test_create_project_directory(self, mock_makedirs):
        full_project_path = "/mock/project/path"

        create_project_directory(full_project_path)
        mock_makedirs.assert_called_once_with(full_project_path, exist_ok=True)

    @patch("os.makedirs")
    def test_create_subdirectories(self, mock_makedirs):
        full_project_path = "/mock/project/path"
        project_name = "mock_project"

        create_subdirectories(full_project_path, project_name)
        mock_makedirs.assert_any_call(
            os.path.join(full_project_path, "src", project_name), exist_ok=True
        )
        mock_makedirs.assert_any_call(
            os.path.join(full_project_path, "tests"), exist_ok=True
        )

    @patch("shutil.copyfile")
    @patch("os.makedirs")
    @patch("dev_template.dev_template.CONFIG", {"config_dir": "/mock/config/dir"})
    @patch("tqdm.tqdm")
    def test_create_basic_files(self, mock_tqdm, mock_makedirs, mock_copyfile):
        full_project_path = "/mock/project/path"
        project_name = "mock_project"

        create_basic_files(full_project_path, project_name)

        expected_files = {
            "README.md": "README.md",
            ".gitignore": ".gitignore",
            "requirements.txt": "requirements.txt",
            "src/{project_name}/__init__.py": os.path.join("src", "__init__.py"),
            "src/{project_name}/main.py": os.path.join("src", "main.py"),
            "tests/__init__.py": os.path.join("tests", "__init__.py"),
            "tests/test_main.py": os.path.join("tests", "test_main.py"),
        }

        for dest_template, src_template in expected_files.items():
            dest_file = os.path.join(
                full_project_path, dest_template.format(project_name=project_name)
            )
            src_file = os.path.join("/mock/config/dir", "templates", src_template)

            mock_makedirs.assert_any_call(os.path.dirname(dest_file), exist_ok=True)
            mock_copyfile.assert_any_call(src_file, dest_file)

        self.assertEqual(mock_copyfile.call_count, len(expected_files))

    @patch("subprocess.check_call")
    @patch("tqdm.tqdm")
    def test_create_virtualenv(self, mock_tqdm, mock_check_call):
        full_project_path = "/mock/project/path"
        project_name = "mock_project"

        create_virtualenv(full_project_path, project_name)

        venv_path = os.path.join(full_project_path, f"{project_name}_venv")

        mock_check_call.assert_called_once_with(
            [sys.executable, "-m", "venv", venv_path]
        )

    @patch("subprocess.check_call")
    @patch("tqdm.tqdm")
    def test_install_packages(self, mock_tqdm, mock_check_call):
        full_project_path = "/mock/project/path"
        project_name = "mock_project"
        packages = ["pkg1", "pkg2"]

        successful_packages = install_packages(
            full_project_path, project_name, packages
        )

        venv_path = os.path.join(full_project_path, f"{project_name}_venv")
        bin_dir = "Scripts" if os.name == "nt" else "bin"

        expected_calls = [
            call(
                [os.path.join(venv_path, bin_dir, "pip"), "install", "pkg1"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ),
            call(
                [os.path.join(venv_path, bin_dir, "pip"), "install", "pkg2"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ),
        ]

        mock_check_call.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(sorted(successful_packages), sorted(packages))

    @patch("builtins.open", new_callable=mock_open)
    @patch("logging.info")
    def test_update_requirements_txt(self, mock_logging_info, mock_open):
        file_path = "/mock/requirements.txt"
        package_versions = {"pkg1": "1.0.0", "pkg2": "2.0.0"}

        update_requirements_txt(file_path, package_versions)

        handle = mock_open()
        handle.write.assert_any_call("pkg1==1.0.0\n")
        handle.write.assert_any_call("pkg2==2.0.0\n")

    @patch("builtins.open", new_callable=mock_open, read_data="dependencies = [\n]\n")
    @patch("logging.info")
    def test_update_pyproject_toml(self, mock_logging_info, mock_open):
        file_path = "/mock/pyproject.toml"
        package_versions = {"pkg1": "1.0.0", "pkg2": "2.0.0"}

        update_pyproject_toml(file_path, package_versions)

        handle = mock_open()
        handle.write.assert_any_call('    "pkg1==1.0.0",\n')
        handle.write.assert_any_call('    "pkg2==2.0.0",\n')

    @patch("dev_template.dev_template.update_requirements_txt")
    @patch("dev_template.dev_template.update_pyproject_toml")
    @patch("dev_template.dev_template.get_installed_packages")
    @patch("tqdm.tqdm")
    def test_write_successful_packages_to_files(
        self,
        mock_tqdm,
        mock_get_installed_packages,
        mock_update_pyproject_toml,
        mock_update_requirements_txt,
    ):
        full_project_path = "/mock/project/path"

        mock_get_installed_packages.return_value = {"pkg1": "1.0.0", "pkg2": "2.0.0"}

        write_successful_packages_to_files(full_project_path)

        mock_update_requirements_txt.assert_called_once_with(
            os.path.join(full_project_path, "requirements.txt"),
            {"pkg1": "1.0.0", "pkg2": "2.0.0"},
        )
        mock_update_pyproject_toml.assert_called_once_with(
            os.path.join(full_project_path, "pyproject.toml"),
            {"pkg1": "1.0.0", "pkg2": "2.0.0"},
        )


if __name__ == "__main__":
    unittest.main()
