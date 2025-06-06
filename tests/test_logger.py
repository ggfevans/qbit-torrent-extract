"""Tests for the enhanced logging system."""

import pytest
import tempfile
import logging
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from qbit_torrent_extract.logger import (
    LoggingManager, TorrentLogManager, StructuredFormatter,
    setup_logging, get_logger, log_with_context, cleanup_logging
)
from qbit_torrent_extract.config import Config


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def config_with_logging(temp_log_dir):
    """Create a config with logging enabled."""
    return Config(
        log_dir=str(temp_log_dir),
        per_torrent_logs=True,
        log_level='DEBUG',
        log_rotation_size=1024,  # Small size for testing
        log_rotation_count=3
    )


@pytest.fixture
def config_console_only():
    """Create a config with console-only logging."""
    return Config(
        log_dir=None,
        per_torrent_logs=False,
        log_level='INFO'
    )


class TestStructuredFormatter:
    """Test the structured log formatter."""
    
    def test_basic_formatting(self):
        """Test basic log formatting without context."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert "INFO" in formatted
        assert "test.module" in formatted
        assert "Test message" in formatted
    
    def test_torrent_context_formatting(self):
        """Test log formatting with torrent context."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.torrent_name = "My Torrent"
        
        formatted = formatter.format(record)
        assert "[My Torrent]" in formatted
    
    def test_archive_path_formatting(self):
        """Test log formatting with archive path context."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.archive_path = Path("/path/to/archive.zip")
        
        formatted = formatter.format(record)
        assert "[/path/to/archive.zip]" in formatted
    
    def test_long_path_truncation(self):
        """Test that long paths are truncated for readability."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        long_path = "/very/long/path/that/should/be/truncated/because/it/is/too/long/for/display/archive.zip"
        record.archive_path = Path(long_path)
        
        formatted = formatter.format(record)
        assert "..." in formatted
        # The formatted message should be shorter than if we included the full path
        # Plus the path should be truncated to 50 chars max


class TestTorrentLogManager:
    """Test the per-torrent log manager."""
    
    def test_sanitize_filename(self, config_with_logging):
        """Test filename sanitization."""
        manager = TorrentLogManager(config_with_logging)
        
        # Test invalid characters
        assert manager._sanitize_filename("torrent<>name") == "torrent__name"
        assert manager._sanitize_filename("torrent/with\\slashes") == "torrent_with_slashes"
        assert manager._sanitize_filename("torrent:with|special?chars*") == "torrent_with_special_chars"
        
        # Test length limiting
        long_name = "a" * 150
        sanitized = manager._sanitize_filename(long_name)
        assert len(sanitized) <= 100
        
        # Test empty name
        assert manager._sanitize_filename("") == "unknown_torrent"
        assert manager._sanitize_filename("   ") == "unknown_torrent"
    
    def test_get_torrent_logger(self, config_with_logging):
        """Test getting torrent-specific loggers."""
        manager = TorrentLogManager(config_with_logging)
        
        # Get logger for first torrent
        logger1 = manager.get_torrent_logger("Torrent 1")
        assert logger1 is not None
        assert "Torrent_1" in logger1.name
        
        # Get same logger again (should be cached)
        logger1_again = manager.get_torrent_logger("Torrent 1")
        assert logger1 is logger1_again
        
        # Get different logger
        logger2 = manager.get_torrent_logger("Torrent 2")
        assert logger2 is not logger1
        assert "Torrent_2" in logger2.name
    
    def test_logger_file_creation(self, config_with_logging):
        """Test that log files are created for torrents."""
        manager = TorrentLogManager(config_with_logging)
        
        # Get logger for a torrent
        logger = manager.get_torrent_logger("Test Torrent")
        
        # Log a message
        logger.info("Test message")
        
        # Check that log file was created
        expected_file = Path(config_with_logging.log_dir) / "Test_Torrent.log"
        assert expected_file.exists()
        
        # Check log content
        content = expected_file.read_text()
        assert "Test message" in content
    
    def test_close_all_loggers(self, config_with_logging):
        """Test closing all torrent loggers."""
        manager = TorrentLogManager(config_with_logging)
        
        # Create multiple loggers
        logger1 = manager.get_torrent_logger("Torrent 1")
        logger2 = manager.get_torrent_logger("Torrent 2")
        
        assert len(manager.torrent_loggers) == 2
        
        # Close all loggers
        manager.close_all_loggers()
        
        assert len(manager.torrent_loggers) == 0


class TestLoggingManager:
    """Test the main logging manager."""
    
    def test_console_only_logging(self, config_console_only):
        """Test logging manager with console-only configuration."""
        manager = LoggingManager(config_console_only)
        
        assert manager.main_logger is not None
        assert len(manager.main_logger.handlers) == 1  # Console handler only
        assert manager.torrent_manager is None
    
    def test_file_logging(self, config_with_logging):
        """Test logging manager with file logging enabled."""
        manager = LoggingManager(config_with_logging)
        
        assert manager.main_logger is not None
        assert len(manager.main_logger.handlers) == 2  # Console + file handlers
        assert manager.torrent_manager is not None
        
        # Check that main log file is created
        main_log_file = Path(config_with_logging.log_dir) / "qbit-torrent-extract.log"
        
        # Log a message to trigger file creation
        manager.main_logger.info("Test message")
        
        assert main_log_file.exists()
        content = main_log_file.read_text()
        assert "Test message" in content
    
    def test_get_logger_without_torrent(self, config_console_only):
        """Test getting a regular logger without torrent context."""
        manager = LoggingManager(config_console_only)
        
        logger = manager.get_logger("test.module")
        assert logger.name == "qbit_torrent_extract.test.module"
    
    def test_get_logger_with_torrent(self, config_with_logging):
        """Test getting a torrent-specific logger."""
        manager = LoggingManager(config_with_logging)
        
        logger = manager.get_logger("test.module", "My Torrent")
        assert logger.name.endswith("My_Torrent")
    
    def test_log_with_context(self, config_with_logging):
        """Test logging with contextual information."""
        manager = LoggingManager(config_with_logging)
        
        # Log with various context - this should create a torrent-specific log
        manager.log_with_context(
            logging.INFO,
            "Test message",
            logger_name="test",  # Specify a logger name
            torrent_name="Test Torrent",
            archive_path=Path("/test/archive.zip"),
            custom_field="custom_value"
        )
        
        # Check that torrent log file was created
        import time
        time.sleep(0.1)  # Small delay to ensure file is flushed
        torrent_log = Path(config_with_logging.log_dir) / "Test_Torrent.log"
        assert torrent_log.exists()
        
        content = torrent_log.read_text()
        assert "Test message" in content
        assert "/test/archive.zip" in content
    
    def test_set_level(self, config_with_logging):
        """Test setting log levels."""
        manager = LoggingManager(config_with_logging)
        
        # Create a torrent logger
        torrent_logger = manager.get_logger("test", "Test Torrent")
        
        # Set level to WARNING
        manager.set_level("WARNING")
        
        assert manager.main_logger.level == logging.WARNING
        assert torrent_logger.level == logging.WARNING
    
    def test_get_log_stats(self, config_with_logging):
        """Test getting logging statistics."""
        manager = LoggingManager(config_with_logging)
        
        # Create some torrent loggers
        manager.get_logger("test", "Torrent 1")
        manager.get_logger("test", "Torrent 2")
        
        stats = manager.get_log_stats()
        
        assert stats['log_dir'] == str(config_with_logging.log_dir)
        assert stats['per_torrent_logs'] is True
        assert stats['active_torrent_loggers'] == 2
        assert "Torrent 1" in stats['torrent_loggers']
        assert "Torrent 2" in stats['torrent_loggers']
    
    def test_close(self, config_with_logging):
        """Test closing the logging manager."""
        manager = LoggingManager(config_with_logging)
        
        # Create some loggers
        manager.get_logger("test", "Test Torrent")
        
        # Close the manager
        manager.close()
        
        # Torrent manager should be cleaned up
        assert len(manager.torrent_manager.torrent_loggers) == 0


class TestGlobalFunctions:
    """Test the global logging functions."""
    
    def test_setup_logging(self, config_with_logging):
        """Test the global setup_logging function."""
        manager = setup_logging(config_with_logging)
        
        assert manager is not None
        assert isinstance(manager, LoggingManager)
        
        # Test that we can get loggers
        logger = get_logger("test")
        assert logger is not None
    
    def test_get_logger_global(self, config_console_only):
        """Test the global get_logger function."""
        setup_logging(config_console_only)
        
        logger = get_logger("test.module")
        assert logger.name == "qbit_torrent_extract.test.module"
        
        torrent_logger = get_logger("test.module", "Test Torrent")
        # Should return regular logger since per_torrent_logs is False
        assert torrent_logger.name == "qbit_torrent_extract.test.module"
    
    def test_log_with_context_global(self, config_with_logging):
        """Test the global log_with_context function."""
        setup_logging(config_with_logging)
        
        log_with_context(
            logging.INFO,
            "Global context test",
            torrent_name="Global Torrent",
            archive_path=Path("/global/test.zip")
        )
        
        # Check that log was written
        torrent_log = Path(config_with_logging.log_dir) / "Global_Torrent.log"
        assert torrent_log.exists()
        
        content = torrent_log.read_text()
        assert "Global context test" in content
    
    def test_cleanup_logging(self, config_with_logging):
        """Test the global cleanup_logging function."""
        setup_logging(config_with_logging)
        get_logger("test", "Test Torrent")  # Create a torrent logger
        
        cleanup_logging()
        
        # After cleanup, should create new manager if needed
        logger = get_logger("test")
        assert logger is not None
    
    def test_automatic_manager_creation(self):
        """Test that logging manager is created automatically if needed."""
        cleanup_logging()  # Ensure clean state
        
        # Getting a logger should create manager automatically
        logger = get_logger("auto.test")
        assert logger is not None
        assert logger.name == "qbit_torrent_extract.auto.test"


class TestLogRotation:
    """Test log rotation functionality."""
    
    def test_log_rotation_config(self, temp_log_dir):
        """Test that log rotation is configured correctly."""
        config = Config(
            log_dir=str(temp_log_dir),
            log_rotation_size=100,  # Very small for testing
            log_rotation_count=2
        )
        
        manager = LoggingManager(config)
        
        # Check that file handler has rotation configured
        file_handler = None
        for handler in manager.main_logger.handlers:
            if hasattr(handler, 'maxBytes'):
                file_handler = handler
                break
        
        assert file_handler is not None
        assert file_handler.maxBytes == 100
        assert file_handler.backupCount == 2
    
    @patch('qbit_torrent_extract.logger.RotatingFileHandler')
    def test_torrent_log_rotation(self, mock_handler, config_with_logging):
        """Test that torrent loggers use rotation."""
        manager = TorrentLogManager(config_with_logging)
        
        manager.get_torrent_logger("Test Torrent")
        
        # Verify that RotatingFileHandler was called with correct parameters
        mock_handler.assert_called()
        call_args = mock_handler.call_args
        assert call_args[1]['maxBytes'] == config_with_logging.log_rotation_size
        assert call_args[1]['backupCount'] == config_with_logging.log_rotation_count


class TestIntegrationWithExtractor:
    """Test logging integration with the extractor."""
    
    def test_extractor_with_torrent_logging(self, config_with_logging):
        """Test that extractor uses torrent-specific logging."""
        from qbit_torrent_extract.extractor import ArchiveExtractor
        
        setup_logging(config_with_logging)
        
        extractor = ArchiveExtractor(
            config=config_with_logging,
            torrent_name="Integration Test"
        )
        
        # The extractor should have a logger
        assert extractor.logger is not None
        
        # Test that the logger works
        extractor.logger.info("Integration test message")
        
        # Check that torrent log file was created
        torrent_log = Path(config_with_logging.log_dir) / "Integration_Test.log"
        assert torrent_log.exists()
        
        content = torrent_log.read_text()
        assert "Integration test message" in content