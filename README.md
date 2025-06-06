# qbit-torrent-extract

An automated solution for extracting nested archives (zip/rar) from completed qBittorrent downloads.

## Features

- Automatically extracts ZIP files from completed torrent downloads
- Handles nested RAR archives within ZIP files
- Integrates with qBittorrent's "Run external program on torrent completion" feature
- Comprehensive logging
- Preserves original archives
- Error handling and reporting

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/qbit-torrent-extract.git
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
1. Open qBittorrent Settings
2. Go to Downloads
3. Under "Run external program on torrent completion" add:
   ```bash
   /path/to/venv/bin/python -m qbit_torrent_extract "%F"
   ```

## Configuration

TBD: Configuration options will be documented here.

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src
```

## License

MIT License - see LICENSE file for details.
