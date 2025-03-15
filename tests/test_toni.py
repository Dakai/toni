"""Tests for the TONI package."""

import unittest
from unittest.mock import patch, MagicMock
from toni.core import get_system_info, command_exists


class TestToni(unittest.TestCase):
    """Test cases for TONI functionality."""

    def test_get_system_info(self):
        """Test that system info is returned."""
        result = get_system_info()
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    @patch("toni.core.shutil.which")
    def test_command_exists(self, mock_which):
        """Test command_exists function."""
        mock_which.return_value = "/usr/bin/ls"
        self.assertTrue(command_exists("ls"))

        mock_which.return_value = None
        self.assertFalse(command_exists("nonexistentcommand"))


if __name__ == "__main__":
    unittest.main()
