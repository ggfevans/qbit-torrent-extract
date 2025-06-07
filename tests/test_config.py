"""Tests for the configuration system."""

import json
import pytest
import tempfile
import os
from pathlib import Path
from qbit_torrent_extract.config import Config, load_config, get_default_config


class TestConfig:
    """Test configuration functionality."""

    def test_default_config(self):
        """Test default configuration values."""
        config = get_default_config()

        assert config.max_extraction_ratio == 100.0
        assert config.max_nested_depth == 3
        assert config.preserve_originals is True
        assert config.log_level == "INFO"
        assert ".zip" in config.supported_extensions
        assert ".rar" in config.supported_extensions

    def test_config_validation(self):
        """Test configuration validation."""
        # Invalid extraction ratio
        with pytest.raises(ValueError, match="max_extraction_ratio must be >= 1"):
            Config(max_extraction_ratio=0.5)

        # Invalid nested depth
        with pytest.raises(ValueError, match="max_nested_depth must be >= 1"):
            Config(max_nested_depth=0)

        # Invalid log level
        with pytest.raises(ValueError, match="Invalid log level"):
            Config(log_level="INVALID")

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "max_extraction_ratio": 200.0,
            "max_nested_depth": 5,
            "log_level": "DEBUG",
            "preserve_originals": False,
        }

        config = Config.from_dict(data)

        assert config.max_extraction_ratio == 200.0
        assert config.max_nested_depth == 5
        assert config.log_level == "DEBUG"
        assert config.preserve_originals is False

    def test_config_from_file(self):
        """Test loading config from JSON file."""
        config_data = {
            "max_extraction_ratio": 150.0,
            "max_nested_depth": 4,
            "log_level": "WARNING",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name

        try:
            config = Config.from_file(temp_file)

            assert config.max_extraction_ratio == 150.0
            assert config.max_nested_depth == 4
            assert config.log_level == "WARNING"
        finally:
            os.unlink(temp_file)

    def test_config_save(self):
        """Test saving config to file."""
        config = Config(
            max_extraction_ratio=75.0, max_nested_depth=2, log_level="ERROR"
        )

        with tempfile.NamedTemporaryFile(mode="r", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            config.save(temp_file)

            with open(temp_file, "r") as f:
                loaded_data = json.load(f)

            assert loaded_data["max_extraction_ratio"] == 75.0
            assert loaded_data["max_nested_depth"] == 2
            assert loaded_data["log_level"] == "ERROR"
        finally:
            os.unlink(temp_file)

    def test_apply_overrides(self):
        """Test applying command-line overrides."""
        config = get_default_config()

        config.apply_overrides(
            max_extraction_ratio=50.0,
            log_level="DEBUG",
            preserve_originals=False,
            non_existent_field="ignored",
        )

        assert config.max_extraction_ratio == 50.0
        assert config.log_level == "DEBUG"
        assert config.preserve_originals is False

    def test_load_config_with_overrides(self):
        """Test load_config with file and overrides."""
        config_data = {"max_extraction_ratio": 100.0, "log_level": "INFO"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name

        try:
            # Load with overrides
            config = load_config(
                config_file=temp_file, max_extraction_ratio=200.0, log_level="DEBUG"
            )

            # Overrides should take precedence
            assert config.max_extraction_ratio == 200.0
            assert config.log_level == "DEBUG"
        finally:
            os.unlink(temp_file)

    def test_log_dir_expansion(self):
        """Test log directory path expansion."""
        config = Config(log_dir="~/logs")

        # Should be expanded to absolute path
        assert config.log_dir == str(Path("~/logs").expanduser().absolute())
