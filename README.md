# qbit-torrent-extract

An automated solution for extracting nested archives (zip/rar) from completed qBittorrent downloads.

> *"No files found are eligible for import"* - Every Readarr user, probably

Finally, a tool that ensures your \*arr apps actually find the files hidden inside those pesky nested archives!

## Features

- Automatically extracts ZIP files from completed torrent downloads
- Handles nested RAR archives within ZIP files (because BitBook loves their archive-ception)
- Integrates with qBittorrent's "Run external program on torrent completion" feature
- Comprehensive logging (so you know exactly why Readarr is happy now)
- Preserves original archives (keep seeding, friends!)
- Error handling and reporting (no more silent failures)
- Makes your \*arr apps actually see those EPUB files buried in `Chuck.Palahniuk.-.Fight.Club.2011.Retail.EPUB.eBook-BitBook.zip`

## Installation

```bash
# Clone the repository
git clone https://github.com/ggfevans/qbit-torrent-extract.git
cd qbit-torrent-extract

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

## Usage

### Command Line
```bash
qbit-torrent-extract /path/to/torrent/folder
```

### qBittorrent Integration

#### Basic Setup
1. **Open qBittorrent Settings** (Tools → Options)
2. **Navigate to Downloads tab**
3. **Enable "Run external program on torrent completion"**
4. **Add the extraction command:**
   ```bash
   /path/to/venv/bin/python -m qbit_torrent_extract "%F"
   ```

#### Advanced Configuration Examples

**With Verbose Logging:**
```bash
/path/to/venv/bin/python -m qbit_torrent_extract "%F" --verbose --torrent-name "%N"
```

**With Custom Configuration:**
```bash
/path/to/venv/bin/python -m qbit_torrent_extract "%F" --config /path/to/config.json --torrent-name "%N"
```

**With Statistics Tracking:**
```bash
/path/to/venv/bin/python -m qbit_torrent_extract "%F" --stats-file /path/to/stats.json --show-stats
```

#### qBittorrent Variable Reference
- `%F` - Torrent content path (file or root directory)
- `%N` - Torrent name
- `%R` - Root directory of the torrent
- `%D` - Save directory
- `%C` - Number of files in the torrent
- `%Z` - Torrent size (bytes)
- `%T` - Torrent category
- `%I` - Torrent hash

#### Recommended Setup
For best results, use this command which includes torrent name for logging:
```bash
/path/to/venv/bin/python -m qbit_torrent_extract "%F" --torrent-name "%N" --preserve
```

## Configuration

The tool supports both command-line options and JSON configuration files.

### Command Line Options
```bash
qbit-torrent-extract [OPTIONS] DIRECTORY

Options:
  --preserve / --no-preserve    Preserve original archives after extraction [default: preserve]
  --verbose / --quiet          Increase output verbosity [default: quiet]
  --config PATH                Path to configuration file
  --max-ratio FLOAT           Maximum extraction ratio for zipbomb protection [default: 100.0]
  --max-depth INTEGER         Maximum nested archive depth [default: 3]
  --log-dir PATH              Directory for log files [default: ~/.qbit-torrent-extract/logs]
  --torrent-name TEXT         Name of the torrent for per-torrent logging
  --stats-file PATH           Path to statistics file [default: ~/.qbit-torrent-extract/stats.json]
  --show-stats                Show aggregated statistics after extraction
  --export-stats PATH         Export statistics to file
  --version                   Show the version and exit
  --help                      Show this message and exit
```

### Configuration File Format
Create a JSON configuration file for consistent settings:

```json
{
  "max_extraction_ratio": 100.0,
  "max_nested_depth": 3,
  "supported_extensions": [".zip", ".rar", ".7z", ".tar.gz", ".tgz"],
  "log_level": "INFO",
  "log_dir": "~/.qbit-torrent-extract/logs",
  "log_rotation_size": 10485760,
  "log_rotation_count": 5,
  "preserve_originals": true,
  "skip_on_error": true,
  "progress_indicators": true,
  "stats_file": "~/.qbit-torrent-extract/stats.json"
}
```

### Security Settings
- `max_extraction_ratio`: Prevents zipbomb attacks by limiting extraction size vs archive size
- `max_nested_depth`: Limits recursive extraction depth to prevent infinite loops
- `skip_on_error`: Continues processing other files when one archive fails

## Troubleshooting

### Common Issues

#### 1. Permission Errors
**Problem:** `PermissionError: [Errno 13] Permission denied`
**Solution:** 
- Ensure qBittorrent runs with appropriate permissions
- Check that the download directory is writable
- On Linux/macOS, verify file ownership: `chown -R user:group /download/path`

#### 2. Path Not Found
**Problem:** `FileNotFoundError: [Errno 2] No such file or directory`
**Solution:**
- Verify the Python path in qBittorrent settings is correct
- Use absolute paths for the script location
- Test the command manually: `python -m qbit_torrent_extract /test/path`

#### 3. Missing Dependencies
**Problem:** `ModuleNotFoundError: No module named 'rarfile'`
**Solution:**
```bash
# Reinstall with all dependencies
pip install -e .

# Or install missing dependencies manually
pip install rarfile py7zr tqdm click
```

#### 4. Archives Not Extracting
**Problem:** Archives are found but not extracted
**Solutions:**
- Check if archives are password-protected (not supported)
- Verify archive integrity: `unrar t archive.rar` or `unzip -t archive.zip`
- Increase verbosity to see detailed logs: `--verbose`
- Check zipbomb protection limits: `--max-ratio 200`

#### 5. Large Archive Timeouts
**Problem:** Extraction stops or times out on large archives
**Solutions:**
- Increase system resources (RAM, disk space)
- Check available disk space before extraction
- Use `--verbose` to monitor progress
- Consider splitting large archives

### Debugging Steps

1. **Test manually first:**
   ```bash
   python -m qbit_torrent_extract /path/to/torrent --verbose
   ```

2. **Check logs:**
   ```bash
   # View main log
   cat ~/.qbit-torrent-extract/logs/qbit-torrent-extract.log
   
   # View torrent-specific log
   cat ~/.qbit-torrent-extract/logs/TorrentName.log
   ```

3. **Verify qBittorrent setup:**
   - Test with a simple command first: `echo "%F" > /tmp/qbit-test.txt`
   - Check if qBittorrent variables are being passed correctly

4. **Check statistics:**
   ```bash
   python -m qbit_torrent_extract /any/path --show-stats
   ```

### Log Analysis

#### Normal Operation:
```
2023-XX-XX 12:00:00 | INFO | Starting qbit-torrent-extract v0.1.0
2023-XX-XX 12:00:00 | INFO | Processing directory: /downloads/TorrentName
2023-XX-XX 12:00:00 | INFO | Found 3 archives to process
2023-XX-XX 12:00:01 | INFO | Successfully extracted: archive1.zip
2023-XX-XX 12:00:02 | INFO | Extraction completed - Processed: 3, Successful: 3, Failed: 0
```

#### Error Indicators:
```
ERROR | Zipbomb detected in archive.zip (ratio: 1500.0 > 100.0)
ERROR | Password-protected archive detected: secret.rar
ERROR | Corrupted archive detected: broken.zip
WARNING | Maximum nested depth reached (3) for nested.zip
```

## Best Practices

### 1. Security Considerations
- **Always use zipbomb protection** (default: enabled)
- **Set reasonable depth limits** (default: 3 levels)
- **Monitor disk space** before processing large torrents
- **Use dedicated user account** for qBittorrent with limited permissions

### 2. Performance Optimization
- **Allocate sufficient RAM** for large archive extraction
- **Use SSD storage** for extraction operations when possible
- **Monitor system resources** during heavy extraction periods
- **Enable log rotation** to prevent log files from growing too large

### 3. Organization and Maintenance
- **Use per-torrent logging** with `--torrent-name "%N"`
- **Enable statistics tracking** to monitor success rates
- **Regular log cleanup** using built-in rotation features
- **Backup important configuration** files

### 4. Integration Tips
- **Test extraction manually** before setting up automation
- **Start with conservative settings** (low max-ratio, shallow depth)
- **Use absolute paths** in qBittorrent configuration
- **Monitor logs regularly** for issues or patterns
- **Keep extraction and seed directories separate** when possible

### 5. Advanced Configuration
```bash
# Production setup with comprehensive logging and stats
/path/to/venv/bin/python -m qbit_torrent_extract "%F" \
  --torrent-name "%N" \
  --config /etc/qbit-extract/config.json \
  --log-dir /var/log/qbit-extract \
  --stats-file /var/lib/qbit-extract/stats.json \
  --preserve
```

### 6. Monitoring and Alerts
Consider setting up monitoring for:
- Extraction failure rates (via statistics export)
- Disk space usage in download directories
- Log file sizes and rotation
- Unusual extraction patterns or errors

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Installation Guide](docs/installation.md)** - Detailed installation instructions for all platforms
- **[Configuration Reference](docs/configuration.md)** - Complete configuration options and examples  
- **[API Documentation](docs/api.md)** - Full API reference for developers
- **[Troubleshooting Guide](docs/troubleshooting.md)** - Common issues and solutions

### Quick Links

- [Platform-specific installation](docs/installation.md#platform-specific-instructions)
- [qBittorrent integration setup](docs/installation.md#qbittorrent-integration)
- [Configuration file format](docs/configuration.md#configuration-file-format)
- [Security settings](docs/configuration.md#security-settings)
- [Performance optimization](docs/troubleshooting.md#performance-issues)
- [Common errors and solutions](docs/troubleshooting.md#quick-diagnostic-steps)

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/qbit-torrent-extract.git
cd qbit-torrent-extract

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/test_security.py  # Security tests
pytest tests/test_performance.py -m performance  # Performance tests
pytest tests/test_integration.py  # Integration tests

# Run tests with verbose output
pytest -v --tb=short
```

### Code Quality Tools

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Run all quality checks
black --check src/ tests/ && flake8 src/ tests/ && mypy src/
```

### Project Structure

```
qbit-torrent-extract/
├── src/qbit_torrent_extract/     # Main package
│   ├── __init__.py
│   ├── main.py                   # CLI entry point
│   ├── config.py                 # Configuration management
│   ├── extractor.py              # Archive extraction logic
│   ├── validator.py              # Archive validation
│   ├── logger.py                 # Logging system
│   └── statistics.py             # Statistics tracking
├── tests/                        # Test suite (148 tests)
│   ├── test_main.py             # CLI tests
│   ├── test_config.py           # Configuration tests
│   ├── test_extractor.py        # Extraction tests
│   ├── test_validator.py        # Validation tests
│   ├── test_logger.py           # Logging tests
│   ├── test_statistics.py       # Statistics tests
│   ├── test_security.py         # Security tests
│   ├── test_performance.py      # Performance tests
│   └── test_integration.py      # Integration tests
├── docs/                        # Documentation
│   ├── installation.md         # Installation guide
│   ├── configuration.md        # Configuration reference
│   ├── api.md                  # API documentation
│   └── troubleshooting.md      # Troubleshooting guide
├── setup.py                    # Package configuration
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

### Contributing

1. **Fork the repository** and create a feature branch
2. **Install development dependencies**: `pip install -e ".[dev]"`
3. **Write tests** for new functionality
4. **Run the test suite**: `pytest`
5. **Check code quality**: `black --check . && flake8 . && mypy src/`
6. **Update documentation** if needed
7. **Submit a pull request** with a clear description

### Testing Guidelines

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test component interactions and workflows
- **Security tests**: Test security features and edge cases
- **Performance tests**: Benchmark and regression testing
- **All tests should pass**: Never commit failing tests
- **Aim for high coverage**: Target >90% code coverage

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: See [docs/](docs/) directory
- **Issues**: Report bugs on [GitHub Issues](https://github.com/ggfevans/qbit-torrent-extract/issues)
- **Discussions**: Join discussions on [GitHub Discussions](https://github.com/ggfevans/qbit-torrent-extract/discussions)
- **Security**: Report security issues privately via email

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.
