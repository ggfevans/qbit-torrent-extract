# Installation Guide

This guide provides comprehensive installation instructions for qbit-torrent-extract across different platforms and environments.

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Installation](#quick-installation)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [Development Installation](#development-installation)
- [Docker Installation](#docker-installation)
- [Virtual Environment Setup](#virtual-environment-setup)
- [Dependency Installation](#dependency-installation)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+, CentOS 7+)
- **RAM**: 512MB available memory
- **Disk Space**: 100MB for installation + space for archive extraction
- **Network**: Internet connection for initial package downloads

### Recommended Requirements

- **Python**: 3.10 or higher
- **RAM**: 2GB+ for large archive processing
- **Disk Space**: 1GB+ free space for extraction operations
- **CPU**: Multi-core processor for better performance

### Required System Tools

#### Windows
- **unrar**: Install WinRAR or 7-Zip for RAR support
- **7z**: 7-Zip for .7z file support

#### macOS
```bash
# Install via Homebrew
brew install unrar p7zip
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install unrar p7zip-full python3-dev python3-pip
```

#### Linux (CentOS/RHEL/Fedora)
```bash
# Enable EPEL repository first (CentOS/RHEL)
sudo yum install epel-release  # or sudo dnf install epel-release

# Install packages
sudo yum install unrar p7zip python3-devel python3-pip
# or for newer versions: sudo dnf install unrar p7zip python3-devel python3-pip
```

## Quick Installation

### For End Users

```bash
# Install from source (recommended)
git clone https://github.com/yourusername/qbit-torrent-extract.git
cd qbit-torrent-extract
pip install .
```

### For qBittorrent Integration

```bash
# Install in a dedicated virtual environment
python -m venv qbit-extract-env
source qbit-extract-env/bin/activate  # Windows: qbit-extract-env\Scripts\activate
pip install git+https://github.com/yourusername/qbit-torrent-extract.git

# Note the installation path for qBittorrent configuration
which qbit-torrent-extract
```

## Platform-Specific Instructions

### Windows Installation

#### Method 1: Using Windows Subsystem for Linux (WSL) - Recommended

1. **Install WSL2**:
   ```powershell
   # Run as Administrator
   wsl --install
   # Restart computer if prompted
   ```

2. **Install Ubuntu in WSL**:
   ```bash
   # In WSL Ubuntu terminal
   sudo apt update
   sudo apt install python3 python3-pip python3-venv unrar p7zip-full git
   ```

3. **Install qbit-torrent-extract**:
   ```bash
   git clone https://github.com/yourusername/qbit-torrent-extract.git
   cd qbit-torrent-extract
   python3 -m venv venv
   source venv/bin/activate
   pip install .
   ```

4. **Configure qBittorrent**:
   - Use WSL path: `wsl /home/username/qbit-torrent-extract/venv/bin/python -m qbit_torrent_extract "%F"`

#### Method 2: Native Windows Installation

1. **Install Python**:
   - Download from [python.org](https://python.org)
   - Ensure "Add Python to PATH" is checked

2. **Install Required Tools**:
   - Install [7-Zip](https://7-zip.org)
   - Install [WinRAR](https://winrar.com) (for RAR support)

3. **Install qbit-torrent-extract**:
   ```cmd
   # In Command Prompt or PowerShell
   python -m venv qbit-extract-env
   qbit-extract-env\Scripts\activate
   pip install git+https://github.com/yourusername/qbit-torrent-extract.git
   ```

4. **Configure qBittorrent**:
   ```
   C:\path\to\qbit-extract-env\Scripts\python.exe -m qbit_torrent_extract "%F"
   ```

### macOS Installation

#### Using Homebrew (Recommended)

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Dependencies**:
   ```bash
   brew install python unrar p7zip git
   ```

3. **Install qbit-torrent-extract**:
   ```bash
   git clone https://github.com/yourusername/qbit-torrent-extract.git
   cd qbit-torrent-extract
   python3 -m venv venv
   source venv/bin/activate
   pip install .
   ```

4. **Configure qBittorrent**:
   ```bash
   # Find the Python path
   which python
   # Use in qBittorrent: /path/to/venv/bin/python -m qbit_torrent_extract "%F"
   ```

#### Using MacPorts

1. **Install MacPorts Dependencies**:
   ```bash
   sudo port install python310 py310-pip unrar p7zip
   ```

2. **Install qbit-torrent-extract**:
   ```bash
   python3.10 -m venv qbit-extract-env
   source qbit-extract-env/bin/activate
   pip install git+https://github.com/yourusername/qbit-torrent-extract.git
   ```

### Linux Installation

#### Ubuntu/Debian

1. **Install System Dependencies**:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv unrar p7zip-full git build-essential
   ```

2. **Install qbit-torrent-extract**:
   ```bash
   git clone https://github.com/yourusername/qbit-torrent-extract.git
   cd qbit-torrent-extract
   python3 -m venv venv
   source venv/bin/activate
   pip install .
   ```

3. **System-wide Installation** (optional):
   ```bash
   sudo pip3 install .
   # Configure qBittorrent with: python3 -m qbit_torrent_extract "%F"
   ```

#### CentOS/RHEL/Fedora

1. **Install System Dependencies**:
   ```bash
   # CentOS 7/8
   sudo yum install epel-release
   sudo yum install python3 python3-pip python3-devel unrar p7zip git gcc

   # CentOS Stream/RHEL 9/Fedora
   sudo dnf install python3 python3-pip python3-devel unrar p7zip git gcc
   ```

2. **Install qbit-torrent-extract**:
   ```bash
   git clone https://github.com/yourusername/qbit-torrent-extract.git
   cd qbit-torrent-extract
   python3 -m venv venv
   source venv/bin/activate
   pip install .
   ```

#### Arch Linux

1. **Install Dependencies**:
   ```bash
   sudo pacman -S python python-pip unrar p7zip git base-devel
   ```

2. **Install qbit-torrent-extract**:
   ```bash
   git clone https://github.com/yourusername/qbit-torrent-extract.git
   cd qbit-torrent-extract
   python -m venv venv
   source venv/bin/activate
   pip install .
   ```

## Development Installation

For contributors and developers:

### Setting Up Development Environment

1. **Clone Repository**:
   ```bash
   git clone https://github.com/yourusername/qbit-torrent-extract.git
   cd qbit-torrent-extract
   ```

2. **Create Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install in Development Mode**:
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install Pre-commit Hooks** (optional):
   ```bash
   pre-commit install
   ```

5. **Verify Development Setup**:
   ```bash
   # Run tests
   pytest tests/

   # Run linting
   black --check src/ tests/
   flake8 src/ tests/
   mypy src/

   # Run in development mode
   python -m qbit_torrent_extract --help
   ```

### Development Dependencies

The development installation includes:
- **pytest**: Testing framework
- **black**: Code formatter
- **flake8**: Linting
- **mypy**: Type checking
- **coverage**: Test coverage
- **pre-commit**: Git hooks

## Docker Installation

### Using Pre-built Image

```bash
# Pull the image
docker pull yourusername/qbit-torrent-extract:latest

# Run extraction
docker run --rm -v /path/to/downloads:/data yourusername/qbit-torrent-extract:latest /data
```

### Building from Source

1. **Clone Repository**:
   ```bash
   git clone https://github.com/yourusername/qbit-torrent-extract.git
   cd qbit-torrent-extract
   ```

2. **Build Docker Image**:
   ```bash
   docker build -t qbit-torrent-extract .
   ```

3. **Run Container**:
   ```bash
   docker run --rm -v /downloads:/data qbit-torrent-extract /data
   ```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  qbit-extract:
    build: .
    volumes:
      - /path/to/downloads:/data
    environment:
      - LOG_LEVEL=INFO
    command: /data
```

Run with:
```bash
docker-compose up
```

## Virtual Environment Setup

### Creating Isolated Environment

```bash
# Create virtual environment
python3 -m venv qbit-extract-env

# Activate environment
source qbit-extract-env/bin/activate  # Linux/macOS
# or
qbit-extract-env\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip

# Install package
pip install git+https://github.com/yourusername/qbit-torrent-extract.git
```

### Managing Multiple Environments

Using `virtualenvwrapper` (Linux/macOS):

```bash
# Install virtualenvwrapper
pip install virtualenvwrapper

# Add to ~/.bashrc or ~/.zshrc
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh

# Create environment
mkvirtualenv qbit-extract

# Work on environment
workon qbit-extract

# Deactivate
deactivate
```

## Dependency Installation

### Core Dependencies

The package automatically installs these dependencies:

- **click**: Command-line interface
- **tqdm**: Progress bars
- **rarfile**: RAR archive support
- **py7zr**: 7z archive support

### Optional Dependencies

Install based on your needs:

```bash
# For development
pip install ".[dev]"

# For specific archive types (if not working)
pip install rarfile py7zr

# For performance monitoring
pip install psutil
```

### System-Level Dependencies

Ensure these are installed on your system:

- **unrar**: For RAR file extraction
- **7z/p7zip**: For 7z file extraction
- **tar/gzip**: Usually pre-installed on Unix systems

## Verification

### Test Installation

1. **Check Version**:
   ```bash
   qbit-torrent-extract --version
   # or
   python -m qbit_torrent_extract --version
   ```

2. **Test with Sample Archive**:
   ```bash
   # Create test directory
   mkdir test-extraction
   cd test-extraction

   # Create test ZIP file
   echo "test content" > test.txt
   zip test.zip test.txt
   rm test.txt

   # Test extraction
   qbit-torrent-extract . --verbose
   ```

3. **Verify Dependencies**:
   ```bash
   # Test RAR support
   python -c "import rarfile; print('RAR support: OK')"

   # Test 7z support  
   python -c "import py7zr; print('7z support: OK')"

   # Test system tools
   unrar --version
   7z --version  # or 7za --version
   ```

### Integration Test

Test integration with qBittorrent:

1. **Create Test Configuration**:
   ```bash
   echo '{"preserve_originals": true, "log_level": "DEBUG"}' > test-config.json
   ```

2. **Test Command**:
   ```bash
   qbit-torrent-extract /test/directory --config test-config.json --verbose --torrent-name "TestTorrent"
   ```

3. **Check Logs**:
   ```bash
   ls ~/.qbit-torrent-extract/logs/
   cat ~/.qbit-torrent-extract/logs/qbit-torrent-extract.log
   ```

## Troubleshooting

### Common Installation Issues

#### Python Version Issues

**Problem**: `python: command not found`
**Solution**:
```bash
# Try python3 instead
python3 --version

# Or install Python
# Ubuntu/Debian: sudo apt install python3
# CentOS/RHEL: sudo yum install python3
# macOS: brew install python3
```

#### Permission Errors

**Problem**: `Permission denied` during installation
**Solutions**:
```bash
# Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install .

# Or install for current user only
pip install --user .

# As last resort (not recommended)
sudo pip install .
```

#### Missing System Dependencies

**Problem**: `unrar: command not found` or similar
**Solutions**:
```bash
# Ubuntu/Debian
sudo apt install unrar p7zip-full

# CentOS/RHEL
sudo yum install epel-release
sudo yum install unrar p7zip

# macOS
brew install unrar p7zip

# Arch Linux
sudo pacman -S unrar p7zip
```

#### RAR Support Issues

**Problem**: `rarfile.RarCannotExec` error
**Solutions**:
1. Install unrar system package
2. Set UNRAR_TOOL environment variable:
   ```bash
   export UNRAR_TOOL=/usr/bin/unrar
   ```
3. Test RAR support:
   ```bash
   python -c "import rarfile; rarfile.UNRAR_TOOL"
   ```

#### 7z Support Issues

**Problem**: `py7zr` import errors
**Solutions**:
```bash
# Reinstall py7zr
pip uninstall py7zr
pip install py7zr

# Or use system 7z
sudo apt install p7zip-full  # Ubuntu/Debian
brew install p7zip          # macOS
```

### Performance Issues

#### Slow Extraction

**Solutions**:
- Increase available RAM
- Use SSD storage for extraction
- Adjust `max_nested_depth` setting
- Enable `progress_indicators` for monitoring

#### Memory Usage

**Solutions**:
- Process smaller batches
- Increase system swap
- Monitor with `--verbose` flag
- Use system monitoring tools

### Platform-Specific Issues

#### Windows PATH Issues

**Problem**: Command not found after installation
**Solutions**:
1. Add Python Scripts directory to PATH
2. Use full path to python executable
3. Use `python -m qbit_torrent_extract` instead

#### macOS Security Issues

**Problem**: "Cannot verify developer" warnings
**Solutions**:
1. Allow in System Preferences → Security
2. Use `--trusted-host` for pip installs
3. Install from source instead of binary

#### Linux Permission Issues

**Problem**: Cannot access archive files
**Solutions**:
1. Check file permissions: `ls -la`
2. Ensure user ownership: `chown user:group files`
3. Run qBittorrent with appropriate user permissions

### Getting Help

If you encounter issues not covered here:

1. **Check the logs**: Look in `~/.qbit-torrent-extract/logs/`
2. **Run with verbose**: Use `--verbose` flag for detailed output
3. **Check system requirements**: Verify all dependencies are installed
4. **Search issues**: Check GitHub issues for similar problems
5. **Create bug report**: Include logs, system info, and steps to reproduce

For more help, see the [Troubleshooting Guide](troubleshooting.md) or [Configuration Reference](configuration.md).