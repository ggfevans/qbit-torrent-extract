"""Configuration for qbit-torrent-extract."""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Configuration for qbit-torrent-extract."""

    # Archive handling
    max_extraction_ratio: float = 100.0
    max_nested_depth: int = 3

    # Logging
    log_level: str = "INFO"
    log_dir: Optional[str] = None

    # Processing
    preserve_originals: bool = True
    progress_indicators: bool = True

    def __post_init__(self):
        """Validate configuration."""
        if self.max_extraction_ratio < 1:
            raise ValueError("max_extraction_ratio must be >= 1")

        if self.max_nested_depth < 1:
            raise ValueError("max_nested_depth must be >= 1")

        if self.log_level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
            raise ValueError(f"Invalid log level: {self.log_level}")

        if self.log_dir:
            self.log_dir = str(Path(self.log_dir).expanduser().absolute())

    @classmethod
    def from_file(cls, path: str) -> "Config":
        """Load configuration from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        # Only use keys that exist in our dataclass
        valid_keys = cls.__annotations__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

def load_config(config_file: Optional[str] = None, **overrides) -> Config:
    """Load configuration with optional file and CLI overrides.

    Args:
        config_file: Optional path to JSON config file
        **overrides: CLI overrides (None values are ignored)

    Returns:
        Config object
    """
    # Start with defaults
    config = Config()

    # Load from file if provided
    if config_file and os.path.exists(config_file):
        try:
            config = Config.from_file(config_file)
            logging.info(f"Loaded config from {config_file}")
        except Exception as e:
            logging.warning(f"Failed to load config: {e}")

    # Apply CLI overrides (skip None values)
    for key, value in overrides.items():
        if value is not None and hasattr(config, key):
            setattr(config, key, value)

    return config
