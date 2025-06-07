# Configuration Reference

This document provides comprehensive reference for all configuration options in qbit-torrent-extract.

## Table of Contents

- [Configuration Overview](#configuration-overview)
- [Configuration Methods](#configuration-methods)
- [Configuration Parameters](#configuration-parameters)
- [Configuration File Format](#configuration-file-format)
- [Command Line Options](#command-line-options)
- [Environment Variables](#environment-variables)
- [Configuration Examples](#configuration-examples)
- [Validation and Defaults](#validation-and-defaults)
- [Best Practices](#best-practices)

## Configuration Overview

qbit-torrent-extract uses a hierarchical configuration system with the following precedence (highest to lowest):

1. **Command-line arguments** (highest priority)
2. **Environment variables**
3. **Configuration file**
4. **Default values** (lowest priority)

## Configuration Methods

### 1. Command Line Arguments

Override any configuration option directly via command line:

```bash
qbit-torrent-extract /path/to/archives \
  --max-ratio 50.0 \
  --max-depth 5 \
  --preserve \
  --verbose \
  --config /path/to/config.json
```

### 2. Configuration File

Create a JSON configuration file for consistent settings:

```bash
# Use default location
qbit-torrent-extract /path/to/archives --config config.json

# Or specify full path
qbit-torrent-extract /path/to/archives --config /etc/qbit-extract/config.json
```

### 3. Environment Variables

Set configuration via environment variables (prefix with `QBIT_EXTRACT_`):

```bash
export QBIT_EXTRACT_MAX_RATIO=50.0
export QBIT_EXTRACT_LOG_LEVEL=DEBUG
qbit-torrent-extract /path/to/archives
```

### 4. Programmatic Configuration

When using as a library:

```python
from qbit_torrent_extract.config import Config, load_config

# Direct instantiation
config = Config(max_extraction_ratio=50.0, preserve_originals=False)

# Load with overrides
config = load_config("config.json", max_nested_depth=5)
```

## Configuration Parameters

### Security Settings

#### `max_extraction_ratio`
- **Type**: `float`
- **Default**: `100.0`
- **Range**: `1.0` to `10000.0`
- **Description**: Maximum ratio of extracted size to archive size (zipbomb protection)
- **Example**: `50.0` means extracted content can be at most 50x the archive size

```json
{
  "max_extraction_ratio": 100.0
}
```

**Command line**: `--max-ratio 100.0`
**Environment**: `QBIT_EXTRACT_MAX_RATIO=100.0`

#### `max_nested_depth`
- **Type**: `int`
- **Default**: `3`
- **Range**: `1` to `10`
- **Description**: Maximum depth for nested archive extraction
- **Example**: `3` allows archive → archive → archive → files

```json
{
  "max_nested_depth": 3
}
```

**Command line**: `--max-depth 3`
**Environment**: `QBIT_EXTRACT_MAX_NESTED_DEPTH=3`

#### `supported_extensions`
- **Type**: `List[str]`
- **Default**: `[".zip", ".rar", ".7z", ".tar.gz", ".tgz"]`
- **Description**: List of supported archive file extensions
- **Note**: Extensions are case-insensitive

```json
{
  "supported_extensions": [".zip", ".rar", ".7z", ".tar.gz", ".tgz"]
}
```

**Environment**: `QBIT_EXTRACT_SUPPORTED_EXTENSIONS=.zip,.rar,.7z`

### File Handling Settings

#### `preserve_originals`
- **Type**: `bool`
- **Default**: `true`
- **Description**: Whether to keep original archives after successful extraction
- **Recommendation**: Keep `true` for seeding torrents

```json
{
  "preserve_originals": true
}
```

**Command line**: `--preserve` or `--no-preserve`
**Environment**: `QBIT_EXTRACT_PRESERVE_ORIGINALS=true`

#### `skip_on_error`
- **Type**: `bool`
- **Default**: `true`
- **Description**: Continue processing other files when one archive fails
- **Recommendation**: Keep `true` for batch processing

```json
{
  "skip_on_error": true
}
```

**Environment**: `QBIT_EXTRACT_SKIP_ON_ERROR=true`

#### `progress_indicators`
- **Type**: `bool`
- **Default**: `true`
- **Description**: Show progress bars and indicators during extraction
- **Note**: Automatically disabled in non-interactive environments

```json
{
  "progress_indicators": true
}
```

**Environment**: `QBIT_EXTRACT_PROGRESS_INDICATORS=true`

### Logging Settings

#### `log_level`
- **Type**: `str`
- **Default**: `"INFO"`
- **Valid values**: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`
- **Description**: Minimum logging level
- **Debug**: Detailed operation logs
- **Info**: Normal operation logs
- **Warning**: Important warnings only
- **Error**: Errors only

```json
{
  "log_level": "INFO"
}
```

**Command line**: `--verbose` (sets to DEBUG) or `--quiet` (sets to WARNING)
**Environment**: `QBIT_EXTRACT_LOG_LEVEL=INFO`

#### `log_dir`
- **Type**: `str` or `null`
- **Default**: `null` (console logging only)
- **Description**: Directory for log files
- **Path expansion**: Supports `~` for home directory
- **Auto-creation**: Directory created if it doesn't exist

```json
{
  "log_dir": "~/.qbit-torrent-extract/logs"
}
```

**Command line**: `--log-dir /path/to/logs`
**Environment**: `QBIT_EXTRACT_LOG_DIR=/path/to/logs`

#### `log_rotation_size`
- **Type**: `int`
- **Default**: `10485760` (10MB)
- **Range**: `1024` (1KB) to `1073741824` (1GB)
- **Description**: Maximum size per log file in bytes
- **Behavior**: New log file created when size exceeded

```json
{
  "log_rotation_size": 10485760
}
```

**Environment**: `QBIT_EXTRACT_LOG_ROTATION_SIZE=10485760`

#### `log_rotation_count`
- **Type**: `int`
- **Default**: `5`
- **Range**: `1` to `50`
- **Description**: Number of backup log files to keep
- **Behavior**: Oldest files deleted when limit exceeded

```json
{
  "log_rotation_count": 5
}
```

**Environment**: `QBIT_EXTRACT_LOG_ROTATION_COUNT=5`

### Statistics Settings

#### `stats_file`
- **Type**: `str` or `null`
- **Default**: `null` (statistics disabled)
- **Description**: Path to statistics file
- **Format**: JSON file with extraction statistics
- **Auto-creation**: File created if it doesn't exist

```json
{
  "stats_file": "~/.qbit-torrent-extract/stats.json"
}
```

**Command line**: `--stats-file /path/to/stats.json`
**Environment**: `QBIT_EXTRACT_STATS_FILE=/path/to/stats.json`

## Configuration File Format

### JSON Schema

The configuration file must be valid JSON with the following structure:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "max_extraction_ratio": {
      "type": "number",
      "minimum": 1.0,
      "maximum": 10000.0
    },
    "max_nested_depth": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10
    },
    "supported_extensions": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": "^\\."
      }
    },
    "log_level": {
      "type": "string",
      "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]
    },
    "log_dir": {
      "type": ["string", "null"]
    },
    "log_rotation_size": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 1073741824
    },
    "log_rotation_count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50
    },
    "preserve_originals": {
      "type": "boolean"
    },
    "skip_on_error": {
      "type": "boolean"
    },
    "progress_indicators": {
      "type": "boolean"
    },
    "stats_file": {
      "type": ["string", "null"]
    }
  },
  "additionalProperties": false
}
```

### Sample Configuration Files

#### Minimal Configuration

```json
{
  "preserve_originals": false,
  "max_extraction_ratio": 50.0
}
```

#### Development Configuration

```json
{
  "log_level": "DEBUG",
  "log_dir": "./logs",
  "stats_file": "./stats.json",
  "preserve_originals": true,
  "max_extraction_ratio": 200.0,
  "max_nested_depth": 5,
  "progress_indicators": true
}
```

#### Production Configuration

```json
{
  "log_level": "INFO",
  "log_dir": "/var/log/qbit-extract",
  "log_rotation_size": 52428800,
  "log_rotation_count": 10,
  "stats_file": "/var/lib/qbit-extract/stats.json",
  "preserve_originals": true,
  "max_extraction_ratio": 100.0,
  "max_nested_depth": 3,
  "skip_on_error": true,
  "progress_indicators": false
}
```

#### Security-Focused Configuration

```json
{
  "max_extraction_ratio": 10.0,
  "max_nested_depth": 2,
  "supported_extensions": [".zip", ".7z"],
  "preserve_originals": true,
  "skip_on_error": true,
  "log_level": "WARNING",
  "log_dir": "/secure/logs"
}
```

## Command Line Options

### Complete Options Reference

```bash
qbit-torrent-extract [OPTIONS] DIRECTORY

Arguments:
  DIRECTORY  Path to directory containing archives [required]

Options:
  --preserve / --no-preserve     Preserve original archives [default: preserve]
  --verbose / --quiet           Increase/decrease output verbosity [default: quiet]
  --config PATH                 Path to configuration file
  --max-ratio FLOAT            Maximum extraction ratio [default: 100.0]
  --max-depth INTEGER          Maximum nested depth [default: 3]
  --log-dir PATH               Directory for log files
  --torrent-name TEXT          Torrent name for per-torrent logging
  --stats-file PATH            Path to statistics file
  --show-stats                 Show aggregated statistics after extraction
  --export-stats PATH          Export statistics to file
  --version                    Show version and exit
  --help                       Show help message and exit
```

### Option Combinations

#### Verbose Processing with Statistics
```bash
qbit-torrent-extract /downloads \
  --verbose \
  --stats-file stats.json \
  --show-stats \
  --torrent-name "MyTorrent"
```

#### Security-Focused Processing
```bash
qbit-torrent-extract /downloads \
  --max-ratio 10.0 \
  --max-depth 2 \
  --no-preserve \
  --config security-config.json
```

#### Production Batch Processing
```bash
qbit-torrent-extract /downloads \
  --config /etc/qbit-extract/prod.json \
  --log-dir /var/log/qbit-extract \
  --stats-file /var/lib/qbit-extract/stats.json \
  --quiet
```

## Environment Variables

### Supported Variables

All configuration parameters can be set via environment variables with the `QBIT_EXTRACT_` prefix:

| Parameter | Environment Variable | Example |
|-----------|---------------------|---------|
| `max_extraction_ratio` | `QBIT_EXTRACT_MAX_RATIO` | `QBIT_EXTRACT_MAX_RATIO=50.0` |
| `max_nested_depth` | `QBIT_EXTRACT_MAX_NESTED_DEPTH` | `QBIT_EXTRACT_MAX_NESTED_DEPTH=5` |
| `log_level` | `QBIT_EXTRACT_LOG_LEVEL` | `QBIT_EXTRACT_LOG_LEVEL=DEBUG` |
| `log_dir` | `QBIT_EXTRACT_LOG_DIR` | `QBIT_EXTRACT_LOG_DIR=/tmp/logs` |
| `preserve_originals` | `QBIT_EXTRACT_PRESERVE_ORIGINALS` | `QBIT_EXTRACT_PRESERVE_ORIGINALS=false` |
| `stats_file` | `QBIT_EXTRACT_STATS_FILE` | `QBIT_EXTRACT_STATS_FILE=/tmp/stats.json` |

### Environment Configuration Examples

#### Docker Environment
```bash
docker run -e QBIT_EXTRACT_LOG_LEVEL=DEBUG \
           -e QBIT_EXTRACT_MAX_RATIO=50.0 \
           -e QBIT_EXTRACT_PRESERVE_ORIGINALS=false \
           qbit-torrent-extract /data
```

#### Systemd Service
```ini
[Service]
Environment=QBIT_EXTRACT_LOG_DIR=/var/log/qbit-extract
Environment=QBIT_EXTRACT_STATS_FILE=/var/lib/qbit-extract/stats.json
Environment=QBIT_EXTRACT_LOG_LEVEL=INFO
ExecStart=/usr/local/bin/qbit-torrent-extract
```

#### Shell Configuration
```bash
# Add to ~/.bashrc or ~/.zshrc
export QBIT_EXTRACT_LOG_LEVEL=INFO
export QBIT_EXTRACT_PRESERVE_ORIGINALS=true
export QBIT_EXTRACT_MAX_RATIO=100.0
```

## Configuration Examples

### qBittorrent Integration Configurations

#### Basic qBittorrent Setup
```json
{
  "preserve_originals": true,
  "log_level": "INFO",
  "log_dir": "~/.qbit-torrent-extract/logs",
  "max_extraction_ratio": 100.0,
  "max_nested_depth": 3
}
```

qBittorrent command:
```
/path/to/python -m qbit_torrent_extract "%F" --config ~/.qbit-torrent-extract/config.json --torrent-name "%N"
```

#### Advanced qBittorrent Setup
```json
{
  "log_level": "DEBUG",
  "log_dir": "/var/log/qbit-extract",
  "log_rotation_size": 20971520,
  "log_rotation_count": 10,
  "stats_file": "/var/lib/qbit-extract/stats.json",
  "preserve_originals": true,
  "max_extraction_ratio": 200.0,
  "max_nested_depth": 4,
  "progress_indicators": false,
  "skip_on_error": true
}
```

### Use Case Specific Configurations

#### The "Make Readarr Happy" Configuration
```json
{
  "preserve_originals": true,
  "max_extraction_ratio": 100.0,
  "max_nested_depth": 3,
  "skip_on_error": true,
  "log_level": "INFO",
  "log_dir": "~/qbit-logs",
  "stats_file": "~/readarr-extraction-wins.json",
  "progress_indicators": false,
  "supported_extensions": [".zip", ".rar", ".7z"]
}
```

Perfect for those BitBook releases that hide EPUBs inside ZIPs inside folders with names longer than a Tolstoy novel.

#### High Security Environment
```json
{
  "max_extraction_ratio": 5.0,
  "max_nested_depth": 1,
  "supported_extensions": [".zip"],
  "preserve_originals": true,
  "skip_on_error": false,
  "log_level": "DEBUG",
  "log_dir": "/secure/audit/logs"
}
```

#### High Performance Environment
```json
{
  "max_extraction_ratio": 500.0,
  "max_nested_depth": 5,
  "preserve_originals": false,
  "skip_on_error": true,
  "progress_indicators": false,
  "log_level": "WARNING"
}
```

#### Development/Testing Environment
```json
{
  "log_level": "DEBUG",
  "log_dir": "./dev-logs",
  "stats_file": "./dev-stats.json",
  "preserve_originals": true,
  "max_extraction_ratio": 1000.0,
  "max_nested_depth": 10,
  "progress_indicators": true
}
```

## Validation and Defaults

### Automatic Validation

Configuration values are automatically validated:

- **Type checking**: Ensures correct data types
- **Range validation**: Checks numeric ranges
- **File path validation**: Verifies path accessibility
- **Extension validation**: Ensures extensions start with '.'

### Validation Errors

Common validation errors and solutions:

```python
# Invalid ratio
ValueError: max_extraction_ratio must be between 1.0 and 10000.0

# Invalid depth
ValueError: max_nested_depth must be between 1 and 10

# Invalid log level
ValueError: log_level must be one of: DEBUG, INFO, WARNING, ERROR

# Invalid extension
ValueError: Extensions must start with '.'
```

### Default Value Reference

| Parameter | Default Value | Notes |
|-----------|---------------|-------|
| `max_extraction_ratio` | `100.0` | Conservative for security |
| `max_nested_depth` | `3` | Sufficient for most use cases |
| `supported_extensions` | `[".zip", ".rar", ".7z", ".tar.gz", ".tgz"]` | Common archive types |
| `log_level` | `"INFO"` | Balanced verbosity |
| `log_dir` | `null` | Console logging only |
| `log_rotation_size` | `10485760` (10MB) | Reasonable file size |
| `log_rotation_count` | `5` | Keep recent history |
| `preserve_originals` | `true` | Safe for torrenting |
| `skip_on_error` | `true` | Resilient processing |
| `progress_indicators` | `true` | User-friendly |
| `stats_file` | `null` | Statistics disabled |

## Best Practices

### Configuration Management

1. **Use configuration files** for consistent settings across runs
2. **Version control** your configuration files
3. **Separate environments** (dev, staging, prod) with different configs
4. **Document changes** to configuration parameters
5. **Test configurations** before production deployment

### Security Considerations

1. **Conservative ratios**: Start with low `max_extraction_ratio`
2. **Limit nesting**: Keep `max_nested_depth` reasonable
3. **Enable logging**: Use `log_level: "INFO"` or higher
4. **Monitor statistics**: Track extraction patterns
5. **Review logs**: Regularly check for security issues

### Performance Optimization

1. **Disable progress indicators** in automated environments
2. **Adjust log levels** based on monitoring needs
3. **Use appropriate ratios** for your content types
4. **Monitor resource usage** with statistics
5. **Tune rotation settings** for your disk space

### Maintenance

1. **Regular log rotation** to prevent disk space issues
2. **Statistics monitoring** to identify trends
3. **Configuration updates** for changing requirements
4. **Backup configurations** before major changes
5. **Document custom settings** for team knowledge

### Troubleshooting Configuration

1. **Validate syntax** with JSON validator
2. **Check file permissions** for config and log directories
3. **Test with verbose logging** to debug issues
4. **Use minimal config** to isolate problems
5. **Check environment variables** for conflicts

For more configuration examples and troubleshooting, see the [Installation Guide](installation.md) and [Troubleshooting Guide](troubleshooting.md).