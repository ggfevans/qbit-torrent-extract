# API Documentation

This document provides comprehensive API documentation for the qbit-torrent-extract library components.

## Table of Contents

- [Config Module](#config-module)
- [Extractor Module](#extractor-module)
- [Validator Module](#validator-module)
- [Logger Module](#logger-module)
- [Statistics Module](#statistics-module)
- [Main Module](#main-module)

## Config Module

### Class: `Config`

Configuration dataclass that holds all settings for the archive extraction system.

```python
@dataclass
class Config:
    max_extraction_ratio: float = 100.0
    max_nested_depth: int = 3
    supported_extensions: List[str] = field(default_factory=lambda: [".zip", ".rar", ".7z", ".tar.gz", ".tgz"])
    log_level: str = "INFO"
    log_dir: Optional[str] = None
    log_rotation_size: int = 10 * 1024 * 1024  # 10MB
    log_rotation_count: int = 5
    preserve_originals: bool = True
    skip_on_error: bool = True
    progress_indicators: bool = True
    stats_file: Optional[str] = None
```

#### Attributes

- **max_extraction_ratio** (`float`): Maximum ratio of extracted size to archive size (zipbomb protection)
- **max_nested_depth** (`int`): Maximum depth for nested archive extraction
- **supported_extensions** (`List[str]`): List of supported archive file extensions
- **log_level** (`str`): Logging level ("DEBUG", "INFO", "WARNING", "ERROR")
- **log_dir** (`Optional[str]`): Directory for log files (None for console only)
- **log_rotation_size** (`int`): Maximum size per log file in bytes
- **log_rotation_count** (`int`): Number of backup log files to keep
- **preserve_originals** (`bool`): Whether to keep original archives after extraction
- **skip_on_error** (`bool`): Whether to continue processing other files on error
- **progress_indicators** (`bool`): Whether to show progress indicators
- **stats_file** (`Optional[str]`): Path to statistics file (None to disable)

#### Methods

##### `validate() -> None`

Validates the configuration parameters and raises `ValueError` if any are invalid.

**Raises:**
- `ValueError`: If any configuration parameter is invalid

**Example:**
```python
config = Config(max_extraction_ratio=-1)
config.validate()  # Raises ValueError
```

##### `to_dict() -> Dict[str, Any]`

Converts the configuration to a dictionary.

**Returns:**
- `Dict[str, Any]`: Configuration as dictionary

**Example:**
```python
config = Config()
config_dict = config.to_dict()
```

##### `@classmethod from_dict(cls, data: Dict[str, Any]) -> 'Config'`

Creates a Config instance from a dictionary.

**Parameters:**
- `data` (`Dict[str, Any]`): Configuration dictionary

**Returns:**
- `Config`: New Config instance

**Example:**
```python
data = {"max_extraction_ratio": 50.0, "preserve_originals": False}
config = Config.from_dict(data)
```

##### `save(self, file_path: str) -> None`

Saves the configuration to a JSON file.

**Parameters:**
- `file_path` (`str`): Path to save the configuration file

**Example:**
```python
config = Config()
config.save("config.json")
```

### Function: `load_config`

Loads configuration with optional overrides.

```python
def load_config(
    config_file: Optional[str] = None,
    **overrides
) -> Config
```

**Parameters:**
- `config_file` (`Optional[str]`): Path to JSON configuration file
- `**overrides`: Configuration overrides as keyword arguments

**Returns:**
- `Config`: Loaded and validated configuration

**Example:**
```python
# Load from file with overrides
config = load_config("config.json", preserve_originals=False, log_level="DEBUG")

# Load with just overrides
config = load_config(max_nested_depth=5)
```

## Extractor Module

### Class: `ArchiveExtractor`

Main class for extracting archives with nested support.

```python
class ArchiveExtractor:
    def __init__(
        self,
        preserve_archives: bool = True,
        config: Optional[Config] = None,
        torrent_name: Optional[str] = None
    )
```

**Parameters:**
- `preserve_archives` (`bool`): Whether to keep original archives
- `config` (`Optional[Config]`): Configuration object
- `torrent_name` (`Optional[str]`): Name for torrent-specific logging

#### Methods

##### `get_archive_files(self, directory: str) -> List[str]`

Gets list of archive files in a directory.

**Parameters:**
- `directory` (`str`): Directory path to scan

**Returns:**
- `List[str]`: List of archive file paths

**Example:**
```python
extractor = ArchiveExtractor()
archives = extractor.get_archive_files("/downloads/torrent")
```

##### `extract_all(self, directory: str) -> Dict[str, Union[int, List[str]]]`

Extracts all archives in a directory with nested support.

**Parameters:**
- `directory` (`str`): Directory containing archives

**Returns:**
- `Dict[str, Union[int, List[str]]]`: Extraction statistics
  - `total_processed` (`int`): Total archives processed
  - `successful` (`int`): Successfully extracted archives
  - `failed` (`int`): Failed extractions
  - `skipped` (`int`): Skipped archives
  - `errors` (`List[str]`): List of error messages

**Example:**
```python
extractor = ArchiveExtractor(preserve_archives=False)
stats = extractor.extract_all("/downloads/torrent")
print(f"Processed: {stats['total_processed']}, Success: {stats['successful']}")
```

##### `extract_archive(self, archive_path: str, extract_to: str) -> bool`

Extracts a single archive file.

**Parameters:**
- `archive_path` (`str`): Path to archive file
- `extract_to` (`str`): Directory to extract to

**Returns:**
- `bool`: True if extraction successful, False otherwise

**Example:**
```python
extractor = ArchiveExtractor()
success = extractor.extract_archive("archive.zip", "/extract/here")
```

## Validator Module

### Class: `ArchiveValidator`

Validates archives for security and integrity.

```python
class ArchiveValidator:
    def __init__(self, config: Config)
```

#### Methods

##### `validate_archive(self, file_path: Path) -> ValidationResult`

Validates an archive file for security and integrity.

**Parameters:**
- `file_path` (`Path`): Path to archive file

**Returns:**
- `ValidationResult`: Validation result with details

**Example:**
```python
config = Config()
validator = ArchiveValidator(config)
result = validator.validate_archive(Path("archive.zip"))
if result.is_valid:
    print("Archive is safe to extract")
```

##### `detect_archive_type(self, file_path: Path) -> Optional[str]`

Detects the type of archive based on file extension and content.

**Parameters:**
- `file_path` (`Path`): Path to archive file

**Returns:**
- `Optional[str]`: Archive type ("zip", "rar", "7z", "tar.gz", "tgz") or None

##### `check_nested_depth(self, nested_paths: List[Path]) -> ValidationResult`

Checks if nested extraction depth exceeds limits.

**Parameters:**
- `nested_paths` (`List[Path]`): List of nested archive paths

**Returns:**
- `ValidationResult`: Validation result

### Class: `ValidationResult`

Result of archive validation.

```python
@dataclass
class ValidationResult:
    is_valid: bool
    archive_type: Optional[str] = None
    error_message: Optional[str] = None
    file_count: Optional[int] = None
    total_size: Optional[int] = None
    compression_ratio: Optional[float] = None
```

#### Attributes

- **is_valid** (`bool`): Whether the archive passed validation
- **archive_type** (`Optional[str]`): Detected archive type
- **error_message** (`Optional[str]`): Error message if validation failed
- **file_count** (`Optional[int]`): Number of files in archive
- **total_size** (`Optional[int]`): Total uncompressed size
- **compression_ratio** (`Optional[float]`): Compression ratio

## Logger Module

### Class: `LoggingManager`

Manages logging for the application with per-torrent support.

```python
class LoggingManager:
    def __init__(self, config: Config)
```

#### Methods

##### `get_logger(self, name: str, torrent_name: Optional[str] = None) -> logging.Logger`

Gets a logger instance with optional torrent-specific logging.

**Parameters:**
- `name` (`str`): Logger name
- `torrent_name` (`Optional[str]`): Torrent name for separate log file

**Returns:**
- `logging.Logger`: Configured logger instance

##### `log_with_context(self, level: int, message: str, **context) -> None`

Logs a message with contextual information.

**Parameters:**
- `level` (`int`): Logging level
- `message` (`str`): Log message
- `**context`: Additional context as keyword arguments

##### `get_log_stats(self) -> Dict[str, Any]`

Gets logging statistics and configuration.

**Returns:**
- `Dict[str, Any]`: Logging statistics

##### `close(self) -> None`

Closes all loggers and handlers.

### Global Functions

##### `setup_logging(config: Config) -> LoggingManager`

Sets up the global logging system.

**Parameters:**
- `config` (`Config`): Configuration object

**Returns:**
- `LoggingManager`: Logging manager instance

##### `get_logger(name: str, torrent_name: Optional[str] = None) -> logging.Logger`

Gets a logger from the global logging manager.

##### `cleanup_logging() -> None`

Cleans up the global logging system.

## Statistics Module

### Class: `StatisticsManager`

Manages extraction statistics with persistent storage.

```python
class StatisticsManager:
    def __init__(self, stats_file: Optional[str] = None)
```

#### Methods

##### `start_extraction_run(self, directory: str) -> str`

Starts a new extraction run and returns a run ID.

**Parameters:**
- `directory` (`str`): Directory being processed

**Returns:**
- `str`: Unique run ID

##### `record_archive_processed(self, archive_path: Path, archive_type: str, success: bool, size_bytes: int, **kwargs) -> None`

Records processing of an archive.

**Parameters:**
- `archive_path` (`Path`): Path to processed archive
- `archive_type` (`str`): Type of archive
- `success` (`bool`): Whether processing was successful
- `size_bytes` (`int`): Archive size in bytes
- `**kwargs`: Additional statistics (extraction_time, etc.)

##### `finish_extraction_run(self) -> None`

Finishes the current extraction run.

##### `get_aggregated_stats(self) -> AggregatedStats`

Gets aggregated statistics across all runs.

**Returns:**
- `AggregatedStats`: Aggregated statistics

##### `export_statistics(self, export_path: Path) -> Path`

Exports statistics to a file.

**Parameters:**
- `export_path` (`Path`): Path to export file

**Returns:**
- `Path`: Path to exported file

### Class: `AggregatedStats`

Aggregated statistics across multiple runs.

```python
@dataclass
class AggregatedStats:
    total_runs: int = 0
    lifetime_archives_processed: int = 0
    lifetime_successful: int = 0
    lifetime_failed: int = 0
    lifetime_skipped: int = 0
    lifetime_errors_by_type: Dict[str, int] = field(default_factory=dict)
    lifetime_archives_by_type: Dict[str, int] = field(default_factory=dict)
    lifetime_archive_size_bytes: int = 0
    average_archives_per_run: float = 0.0
    most_common_archive_type: Optional[str] = None
    most_common_error_type: Optional[str] = None
    largest_archive_processed_bytes: int = 0
```

### Global Functions

##### `get_statistics_manager(config: Optional[Config] = None) -> StatisticsManager`

Gets the global statistics manager instance.

**Parameters:**
- `config` (`Optional[Config]`): Configuration (for stats file path)

**Returns:**
- `StatisticsManager`: Statistics manager instance

## Main Module

### Function: `main`

Main CLI entry point.

```python
@click.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
@click.option('--preserve/--no-preserve', default=True, help='Preserve original archives after extraction')
@click.option('--verbose/--quiet', default=False, help='Increase output verbosity')
@click.option('--config', type=click.Path(exists=True), help='Path to configuration file')
@click.option('--max-ratio', type=float, help='Maximum extraction ratio for zipbomb protection')
@click.option('--max-depth', type=int, help='Maximum nested archive depth')
@click.option('--log-dir', type=click.Path(), help='Directory for log files')
@click.option('--torrent-name', type=str, help='Name of the torrent for per-torrent logging')
@click.option('--stats-file', type=click.Path(), help='Path to statistics file')
@click.option('--show-stats', is_flag=True, help='Show aggregated statistics after extraction')
@click.option('--export-stats', type=click.Path(), help='Export statistics to file')
@click.version_option(version='0.1.0')
def main(
    directory: Path,
    preserve: bool,
    verbose: bool,
    config: str,
    max_ratio: float,
    max_depth: int,
    log_dir: str,
    torrent_name: str,
    stats_file: str,
    show_stats: bool,
    export_stats: str
) -> None
```

CLI function that handles archive extraction with all configuration options.

## Usage Examples

### Basic Usage

```python
from qbit_torrent_extract.extractor import ArchiveExtractor
from qbit_torrent_extract.config import Config

# Basic extraction
extractor = ArchiveExtractor()
stats = extractor.extract_all("/path/to/archives")
print(f"Extracted {stats['successful']} archives")

# With custom configuration
config = Config(preserve_originals=False, max_nested_depth=5)
extractor = ArchiveExtractor(config=config)
stats = extractor.extract_all("/path/to/archives")
```

### Advanced Configuration

```python
from qbit_torrent_extract.config import load_config
from qbit_torrent_extract.extractor import ArchiveExtractor
from qbit_torrent_extract.logger import setup_logging

# Load configuration from file
config = load_config("config.json", log_level="DEBUG")

# Setup logging
logging_manager = setup_logging(config)

# Extract with full monitoring
extractor = ArchiveExtractor(
    config=config,
    torrent_name="MyTorrent"
)
stats = extractor.extract_all("/downloads/MyTorrent")
```

### Validation Only

```python
from qbit_torrent_extract.validator import ArchiveValidator
from qbit_torrent_extract.config import Config
from pathlib import Path

config = Config()
validator = ArchiveValidator(config)

archive_path = Path("suspicious.zip")
result = validator.validate_archive(archive_path)

if result.is_valid:
    print(f"Archive is safe: {result.archive_type}")
else:
    print(f"Validation failed: {result.error_message}")
```

### Statistics Tracking

```python
from qbit_torrent_extract.statistics import get_statistics_manager
from qbit_torrent_extract.config import Config

config = Config(stats_file="extraction_stats.json")
stats_manager = get_statistics_manager(config)

# Get aggregated statistics
aggregated = stats_manager.get_aggregated_stats()
print(f"Total runs: {aggregated.total_runs}")
print(f"Success rate: {aggregated.lifetime_successful / aggregated.lifetime_archives_processed * 100:.1f}%")

# Export statistics
export_path = stats_manager.export_statistics(Path("stats_export.json"))
print(f"Statistics exported to: {export_path}")
```

## Error Handling

All modules use consistent error handling patterns:

- **Configuration errors**: Raise `ValueError` with descriptive messages
- **File operation errors**: Raise `FileNotFoundError` or `PermissionError`
- **Archive errors**: Logged and tracked in statistics, don't stop processing
- **Validation errors**: Returned as `ValidationResult` objects

### Exception Types

- `ValueError`: Configuration or parameter validation errors
- `FileNotFoundError`: Missing files or directories
- `PermissionError`: Insufficient permissions for file operations
- `zipfile.BadZipFile`: Corrupted or invalid ZIP files
- `rarfile.Error`: RAR file errors
- Standard library exceptions for other file operations

## Thread Safety

- **Config**: Thread-safe (immutable after creation)
- **ArchiveExtractor**: Not thread-safe (create separate instances)
- **ArchiveValidator**: Thread-safe
- **LoggingManager**: Thread-safe
- **StatisticsManager**: Thread-safe with file locking