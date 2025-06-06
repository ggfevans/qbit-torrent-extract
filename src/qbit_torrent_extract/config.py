"""Configuration system for qbit-torrent-extract."""

import os
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class Config:
    """Configuration for qbit-torrent-extract."""
    
    # Archive handling
    max_extraction_ratio: float = 100.0
    max_nested_depth: int = 3
    supported_extensions: list = field(default_factory=lambda: [
        '.zip', '.rar', '.7z', '.tar.gz', '.tgz', '.tar', '.gz'
    ])
    
    # Logging
    log_level: str = 'INFO'
    log_dir: Optional[str] = None
    per_torrent_logs: bool = True
    log_rotation_size: int = 10 * 1024 * 1024  # 10MB
    log_rotation_count: int = 5
    
    # Processing
    preserve_originals: bool = True
    skip_on_error: bool = True
    progress_indicators: bool = True
    
    # Paths
    stats_file: Optional[str] = None
    
    def __post_init__(self):
        """Validate and normalize configuration."""
        if self.max_extraction_ratio < 1:
            raise ValueError("max_extraction_ratio must be >= 1")
        
        if self.max_nested_depth < 1:
            raise ValueError("max_nested_depth must be >= 1")
        
        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            raise ValueError(f"Invalid log level: {self.log_level}")
        
        if self.log_dir:
            self.log_dir = str(Path(self.log_dir).expanduser().absolute())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create Config from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
    
    @classmethod
    def from_file(cls, path: str) -> 'Config':
        """Load configuration from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def save(self, path: str):
        """Save configuration to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def apply_overrides(self, **kwargs):
        """Apply command-line overrides to configuration."""
        for key, value in kwargs.items():
            if value is not None and hasattr(self, key):
                setattr(self, key, value)


def get_default_config() -> Config:
    """Get default configuration."""
    return Config()


def load_config(config_file: Optional[str] = None, **overrides) -> Config:
    """Load configuration with optional file and command-line overrides.
    
    Args:
        config_file: Optional path to configuration file
        **overrides: Command-line overrides
    
    Returns:
        Config object with all settings applied
    """
    # Start with defaults
    config = get_default_config()
    
    # Load from file if provided
    if config_file and os.path.exists(config_file):
        try:
            config = Config.from_file(config_file)
            logging.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logging.warning(f"Failed to load config from {config_file}: {e}")
    
    # Apply command-line overrides
    config.apply_overrides(**overrides)
    
    return config