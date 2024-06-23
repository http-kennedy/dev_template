import io
import unittest
from unittest.mock import patch

from main import main


class TestMain(unittest.TestCase):
    def test_main_output(self) -> None:
        expected_output = "Thank you for using dev_template!\n"
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            main()
            self.assertEqual(fake_out.getvalue(), expected_output)


if __name__ == "__main__":
    unittest.main()
