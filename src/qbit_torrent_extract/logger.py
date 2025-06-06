"""Enhanced logging system with file support, rotation, and per-torrent logging."""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler
from datetime import datetime
import threading
from .config import Config


class StructuredFormatter(logging.Formatter):
    """Custom formatter that provides structured logging with contextual information."""
    
    def __init__(self, include_context: bool = True):
        """Initialize the structured formatter.
        
        Args:
            include_context: Whether to include contextual information in logs
        """
        self.include_context = include_context
        # Base format with timestamp, level, module, and message
        base_format = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
        super().__init__(base_format, datefmt="%Y-%m-%d %H:%M:%S")
    
    def format(self, record):
        """Format the log record with additional context if available."""
        # Create a copy to avoid modifying the original record
        import copy
        record_copy = copy.copy(record)
        
        # Add contextual information if available
        if self.include_context and hasattr(record_copy, 'torrent_name'):
            record_copy.name = f"{record_copy.name}[{record_copy.torrent_name}]"
        
        if hasattr(record_copy, 'archive_path'):
            # Truncate long paths for readability
            archive_path = str(record_copy.archive_path)
            if len(archive_path) > 50:
                archive_path = "..." + archive_path[-47:]
            record_copy.msg = f"[{archive_path}] {record_copy.msg}"
        
        return super().format(record_copy)


class TorrentLogManager:
    """Manages per-torrent log files with rotation."""
    
    def __init__(self, config: Config):
        """Initialize the torrent log manager.
        
        Args:
            config: Configuration object with logging settings
        """
        self.config = config
        self.torrent_loggers: Dict[str, logging.Logger] = {}
        self.lock = threading.Lock()
    
    def get_torrent_logger(self, torrent_name: str) -> logging.Logger:
        """Get or create a logger for a specific torrent.
        
        Args:
            torrent_name: Name of the torrent for logging
            
        Returns:
            Logger instance for the torrent
        """
        with self.lock:
            if torrent_name not in self.torrent_loggers:
                self.torrent_loggers[torrent_name] = self._create_torrent_logger(torrent_name)
            return self.torrent_loggers[torrent_name]
    
    def _create_torrent_logger(self, torrent_name: str) -> logging.Logger:
        """Create a new logger for a torrent.
        
        Args:
            torrent_name: Name of the torrent
            
        Returns:
            Configured logger instance
        """
        # Sanitize torrent name for filename
        safe_name = self._sanitize_filename(torrent_name)
        logger_name = f"qbit_torrent_extract.torrent.{safe_name}"
        
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
        
        if self.config.log_dir:
            # Create log directory if it doesn't exist
            log_dir = Path(self.config.log_dir).expanduser()
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Create rotating file handler for this torrent
            log_file = log_dir / f"{safe_name}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=self.config.log_rotation_size,
                backupCount=self.config.log_rotation_count
            )
            file_handler.setFormatter(StructuredFormatter())
            logger.addHandler(file_handler)
        
        return logger
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize a string to be safe for use as a filename.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem use
        """
        # Replace invalid characters with underscores
        invalid_chars = '<>:"/\\|?* '  # Added space
        sanitized = filename
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Limit length and strip whitespace/underscores
        sanitized = sanitized.strip('_')[:100]
        
        # Ensure it's not empty or just underscores
        if not sanitized or sanitized.replace('_', '') == '':
            sanitized = "unknown_torrent"
            
        return sanitized
    
    def close_all_loggers(self):
        """Close all torrent loggers and their handlers."""
        with self.lock:
            for logger in self.torrent_loggers.values():
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)
            self.torrent_loggers.clear()


class LoggingManager:
    """Central logging manager for the application."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the logging manager.
        
        Args:
            config: Configuration object with logging settings
        """
        self.config = config or Config()
        self.torrent_manager = TorrentLogManager(self.config) if self.config.per_torrent_logs else None
        self.main_logger: Optional[logging.Logger] = None
        self._setup_main_logger()
    
    def _setup_main_logger(self):
        """Set up the main application logger."""
        self.main_logger = logging.getLogger("qbit_torrent_extract")
        self.main_logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # Remove existing handlers to avoid duplicates
        for handler in self.main_logger.handlers[:]:
            self.main_logger.removeHandler(handler)
        
        # Console handler (always present)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter())
        self.main_logger.addHandler(console_handler)
        
        # File handler (if log directory is configured)
        if self.config.log_dir:
            self._setup_file_logging()
    
    def _setup_file_logging(self):
        """Set up file logging with rotation."""
        log_dir = Path(self.config.log_dir).expanduser()
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Main application log file
        main_log_file = log_dir / "qbit-torrent-extract.log"
        file_handler = RotatingFileHandler(
            main_log_file,
            maxBytes=self.config.log_rotation_size,
            backupCount=self.config.log_rotation_count
        )
        file_handler.setFormatter(StructuredFormatter())
        self.main_logger.addHandler(file_handler)
        
        self.main_logger.info(f"File logging enabled: {main_log_file}")
        self.main_logger.info(f"Log rotation: {self.config.log_rotation_size} bytes, {self.config.log_rotation_count} backups")
    
    def get_logger(self, name: str, torrent_name: Optional[str] = None) -> logging.Logger:
        """Get a logger instance with optional torrent context.
        
        Args:
            name: Logger name (typically module name)
            torrent_name: Optional torrent name for per-torrent logging
            
        Returns:
            Configured logger instance
        """
        if torrent_name and self.torrent_manager:
            # Return torrent-specific logger
            torrent_logger = self.torrent_manager.get_torrent_logger(torrent_name)
            return torrent_logger
        else:
            # Return main logger or module-specific logger
            if name.startswith("qbit_torrent_extract"):
                return logging.getLogger(name)
            else:
                return logging.getLogger(f"qbit_torrent_extract.{name}")
    
    def log_with_context(self, level: int, message: str, logger_name: str = "main", 
                        torrent_name: Optional[str] = None, 
                        archive_path: Optional[Path] = None, **kwargs):
        """Log a message with contextual information.
        
        Args:
            level: Logging level (e.g., logging.INFO)
            message: Log message
            logger_name: Name of the logger to use
            torrent_name: Optional torrent name for context
            archive_path: Optional archive path for context
            **kwargs: Additional context to include
        """
        logger = self.get_logger(logger_name, torrent_name)
        
        # Create log record with context
        extra = {}
        if torrent_name:
            extra['torrent_name'] = torrent_name
        if archive_path:
            extra['archive_path'] = archive_path
        extra.update(kwargs)
        
        logger.log(level, message, extra=extra)
    
    def set_level(self, level: str):
        """Set the logging level for all loggers.
        
        Args:
            level: Logging level as string ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        """
        numeric_level = getattr(logging, level.upper())
        self.config.log_level = level.upper()
        
        # Update main logger
        self.main_logger.setLevel(numeric_level)
        
        # Update all torrent loggers
        if self.torrent_manager:
            for logger in self.torrent_manager.torrent_loggers.values():
                logger.setLevel(numeric_level)
    
    def close(self):
        """Close all loggers and their handlers."""
        if self.torrent_manager:
            self.torrent_manager.close_all_loggers()
        
        # Close main logger handlers
        if self.main_logger:
            for handler in self.main_logger.handlers[:]:
                handler.close()
                self.main_logger.removeHandler(handler)
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get statistics about the logging system.
        
        Returns:
            Dictionary with logging statistics
        """
        stats = {
            'main_logger_level': self.main_logger.level if self.main_logger else None,
            'log_dir': str(self.config.log_dir) if self.config.log_dir else None,
            'per_torrent_logs': self.config.per_torrent_logs,
            'log_rotation_size': self.config.log_rotation_size,
            'log_rotation_count': self.config.log_rotation_count,
            'active_torrent_loggers': len(self.torrent_manager.torrent_loggers) if self.torrent_manager else 0
        }
        
        if self.torrent_manager:
            stats['torrent_loggers'] = list(self.torrent_manager.torrent_loggers.keys())
        
        return stats


# Global logging manager instance
_logging_manager: Optional[LoggingManager] = None


def setup_logging(config: Optional[Config] = None) -> LoggingManager:
    """Set up the global logging system.
    
    Args:
        config: Configuration object with logging settings
        
    Returns:
        Configured logging manager instance
    """
    global _logging_manager
    
    if _logging_manager:
        _logging_manager.close()
    
    _logging_manager = LoggingManager(config)
    return _logging_manager


def get_logger(name: str, torrent_name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance from the global logging manager.
    
    Args:
        name: Logger name
        torrent_name: Optional torrent name for per-torrent logging
        
    Returns:
        Logger instance
    """
    global _logging_manager
    
    if not _logging_manager:
        _logging_manager = LoggingManager()
    
    return _logging_manager.get_logger(name, torrent_name)


def log_with_context(level: int, message: str, **kwargs):
    """Log a message with context using the global logging manager.
    
    Args:
        level: Logging level
        message: Log message
        **kwargs: Context arguments
    """
    global _logging_manager
    
    if not _logging_manager:
        _logging_manager = LoggingManager()
    
    _logging_manager.log_with_context(level, message, **kwargs)


def cleanup_logging():
    """Clean up the global logging system."""
    global _logging_manager
    
    if _logging_manager:
        _logging_manager.close()
        _logging_manager = None