"""Tests for the main CLI module."""

import json
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from qbit_torrent_extract.main import main


class TestCLI:
    """Test the command-line interface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_zip(self, filename: str, content: str = "test content") -> Path:
        """Create a test ZIP file."""
        zip_path = self.temp_path / filename
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test.txt", content)
        return zip_path

    def test_help_option(self):
        """Test the --help option."""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Extract nested archives" in result.output
        assert "DIRECTORY" in result.output
        assert "--verbose" in result.output
        assert "--preserve" in result.output

    def test_version_option(self):
        """Test the --version option."""
        result = self.runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.2.0" in result.output

    def test_basic_extraction(self):
        """Test basic archive extraction."""
        # Create test archive
        self.create_test_zip("test.zip")

        # Run extraction
        result = self.runner.invoke(main, [str(self.temp_path)])
        assert result.exit_code == 0
        assert "Extraction completed successfully!" in result.output

        # Verify extracted file exists
        extracted_file = self.temp_path / "test.txt"
        assert extracted_file.exists()
        assert extracted_file.read_text() == "test content"

    def test_verbose_output(self):
        """Test verbose output option."""
        self.create_test_zip("test.zip")

        result = self.runner.invoke(main, [str(self.temp_path), "--verbose"])
        assert result.exit_code == 0
        assert "Found" in result.output
        assert "test.zip" in result.output

    def test_preserve_option(self):
        """Test archive preservation options."""
        zip_path = self.create_test_zip("test.zip")

        # Test with --preserve (default)
        result = self.runner.invoke(main, [str(self.temp_path), "--preserve"])
        assert result.exit_code == 0
        assert zip_path.exists()  # Archive should still exist

        # Clean up extracted file for next test
        (self.temp_path / "test.txt").unlink()

        # Test with --no-preserve
        result = self.runner.invoke(main, [str(self.temp_path), "--no-preserve"])
        assert result.exit_code == 0
        assert not zip_path.exists()  # Archive should be deleted

    def test_config_file_option(self):
        """Test configuration file option."""
        # Create config file
        config_path = self.temp_path / "config.json"
        config_data = {
            "max_extraction_ratio": 50.0,
            "max_nested_depth": 2,
            "preserve_originals": True,
        }
        config_path.write_text(json.dumps(config_data))

        self.create_test_zip("test.zip")

        result = self.runner.invoke(
            main, [str(self.temp_path), "--config", str(config_path)]
        )
        assert result.exit_code == 0

    def test_max_ratio_option(self):
        """Test maximum extraction ratio option."""
        self.create_test_zip("test.zip")

        result = self.runner.invoke(
            main, [str(self.temp_path), "--max-ratio", "200.0"]
        )
        assert result.exit_code == 0

    def test_max_depth_option(self):
        """Test maximum depth option."""
        self.create_test_zip("test.zip")

        result = self.runner.invoke(main, [str(self.temp_path), "--max-depth", "5"])
        assert result.exit_code == 0

    def test_log_dir_option(self):
        """Test log directory option."""
        log_dir = self.temp_path / "logs"
        log_dir.mkdir()

        self.create_test_zip("test.zip")

        result = self.runner.invoke(
            main, [str(self.temp_path), "--log-dir", str(log_dir)]
        )
        assert result.exit_code == 0

    def test_nonexistent_directory(self):
        """Test handling of nonexistent directory."""
        result = self.runner.invoke(main, ["/nonexistent/path"])
        assert result.exit_code != 0

    def test_empty_directory(self):
        """Test handling of empty directory."""
        result = self.runner.invoke(main, [str(self.temp_path)])
        assert result.exit_code == 0
        assert "Extraction completed successfully!" in result.output

    @patch("qbit_torrent_extract.main.ArchiveExtractor")
    def test_extraction_error_handling(self, mock_extractor):
        """Test handling of extraction errors."""
        # Mock extractor to raise an exception
        mock_extractor.return_value.extract_all.side_effect = Exception("Test error")

        result = self.runner.invoke(main, [str(self.temp_path)])
        assert result.exit_code == 1
        assert "Error: Test error" in result.output


class TestCLIIntegration:
    """Integration tests for the CLI with various scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_nested_archives(self):
        """Create nested archive structure for testing."""
        # Create inner ZIP
        inner_zip = self.temp_path / "inner.zip"
        with zipfile.ZipFile(inner_zip, "w") as zf:
            zf.writestr("inner_file.txt", "inner content")

        # Create outer ZIP containing inner ZIP
        outer_zip = self.temp_path / "outer.zip"
        with zipfile.ZipFile(outer_zip, "w") as zf:
            zf.write(inner_zip, "inner.zip")

        # Clean up the standalone inner ZIP
        inner_zip.unlink()

        return outer_zip

    def test_nested_extraction_integration(self):
        """Test end-to-end nested archive extraction."""
        self.create_nested_archives()

        result = self.runner.invoke(main, [str(self.temp_path), "--verbose"])
        assert result.exit_code == 0

        # Verify both files were extracted
        assert (self.temp_path / "inner_file.txt").exists()
        assert (self.temp_path / "inner_file.txt").read_text() == "inner content"

    def test_multiple_archives_integration(self):
        """Test processing multiple archives in one run."""
        # Create multiple test archives
        with zipfile.ZipFile(self.temp_path / "archive1.zip", "w") as zf:
            zf.writestr("file1.txt", "content1")

        with zipfile.ZipFile(self.temp_path / "archive2.zip", "w") as zf:
            zf.writestr("file2.txt", "content2")

        result = self.runner.invoke(main, [str(self.temp_path), "--verbose"])
        assert result.exit_code == 0

        # Verify all files were extracted
        assert (self.temp_path / "file1.txt").exists()
        assert (self.temp_path / "file2.txt").exists()
        assert "Found 2 archives" in result.output

    def test_configuration_override_integration(self):
        """Test that CLI options properly override configuration."""
        # Create config with preserve=False
        config_path = self.temp_path / "config.json"
        config_data = {"preserve_originals": False, "max_extraction_ratio": 50.0}
        config_path.write_text(json.dumps(config_data))

        zip_path = self.temp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test.txt", "content")

        # Override with --preserve on command line
        result = self.runner.invoke(
            main, [str(self.temp_path), "--config", str(config_path), "--preserve"]
        )

        assert result.exit_code == 0
        assert zip_path.exists()  # Should be preserved due to CLI override
