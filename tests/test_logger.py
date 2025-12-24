"""Tests for the logging system."""

import logging
import tempfile
from pathlib import Path

from qbit_torrent_extract.logger import setup_logging, get_logger


class TestLogging:
    """Test logging functionality."""

    def test_setup_logging_console_only(self):
        """Test logging setup without file output."""
        logger = setup_logging(level="INFO")

        assert logger is not None
        assert logger.level == logging.INFO
        # Should have at least one handler (console)
        assert len(logger.handlers) >= 1

    def test_setup_logging_with_file(self):
        """Test logging setup with file output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logging(level="DEBUG", log_dir=tmpdir)

            assert logger.level == logging.DEBUG
            # Should have console + file handlers
            assert len(logger.handlers) == 2

            # Log a message
            logger.info("Test message")

            # Check file was created
            log_file = Path(tmpdir) / "qbit-torrent-extract.log"
            assert log_file.exists()
            assert "Test message" in log_file.read_text()

    def test_setup_logging_creates_directory(self):
        """Test that log directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "nested" / "log" / "dir"
            logger = setup_logging(log_dir=str(log_dir))

            logger.info("Test")
            assert log_dir.exists()

    def test_get_logger(self):
        """Test getting a logger instance."""
        setup_logging()
        logger = get_logger()

        assert logger is not None
        assert logger.name == "qbit_torrent_extract"

    def test_log_levels(self):
        """Test different log levels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logging(level="WARNING", log_dir=tmpdir)

            # Debug and info should not appear
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

            log_file = Path(tmpdir) / "qbit-torrent-extract.log"
            content = log_file.read_text()

            assert "Debug message" not in content
            assert "Info message" not in content
            assert "Warning message" in content
            assert "Error message" in content

    def test_log_format(self):
        """Test log message format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logging(level="INFO", log_dir=tmpdir)
            logger.info("Test message")

            log_file = Path(tmpdir) / "qbit-torrent-extract.log"
            content = log_file.read_text()

            # Should have timestamp, level, and message
            assert "INFO" in content
            assert "Test message" in content
            assert "|" in content  # Our format uses | as separator
