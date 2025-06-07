# Troubleshooting Guide

This comprehensive guide helps you diagnose and resolve common issues with qbit-torrent-extract.

## Table of Contents

- [Quick Diagnostic Steps](#quick-diagnostic-steps)
- [Installation Issues](#installation-issues)
- [Configuration Problems](#configuration-problems)
- [Archive Extraction Issues](#archive-extraction-issues)
- [qBittorrent Integration Problems](#qbittorrent-integration-problems)
- [Performance Issues](#performance-issues)
- [Logging and Statistics Issues](#logging-and-statistics-issues)
- [Security and Validation Issues](#security-and-validation-issues)
- [Platform-Specific Issues](#platform-specific-issues)
- [Advanced Troubleshooting](#advanced-troubleshooting)
- [Getting Help](#getting-help)

## Quick Diagnostic Steps

When encountering issues, follow these steps first:

### 1. Check Basic Functionality

```bash
# Verify installation
qbit-torrent-extract --version

# Test with verbose output
qbit-torrent-extract /path/to/test --verbose

# Check help for available options
qbit-torrent-extract --help
```

### 2. Create Test Environment

```bash
# Create test directory
mkdir qbit-test && cd qbit-test

# Create simple test archive
echo "test content" > test.txt
zip test.zip test.txt
rm test.txt

# Test extraction
qbit-torrent-extract . --verbose
```

### 3. Check Dependencies

```bash
# Python version
python --version  # Should be 3.8+

# Required packages
python -c "import rarfile, py7zr, click, tqdm; print('All packages imported successfully')"

# System tools
unrar --version
7z --version
```

### 4. Review Logs

```bash
# Check for log files
ls ~/.qbit-torrent-extract/logs/

# View main log
cat ~/.qbit-torrent-extract/logs/qbit-torrent-extract.log

# View recent errors
grep -i error ~/.qbit-torrent-extract/logs/qbit-torrent-extract.log | tail -10
```

## Installation Issues

### Python Version Problems

#### Issue: "Python version not supported"
**Symptoms**: Installation fails with Python version error
**Solutions**:
```bash
# Check Python version
python --version
python3 --version

# Install Python 3.8+
# Ubuntu/Debian
sudo apt update && sudo apt install python3.9

# macOS with Homebrew
brew install python@3.9

# Use specific Python version
python3.9 -m pip install qbit-torrent-extract
```

#### Issue: "python: command not found"
**Symptoms**: System cannot find Python
**Solutions**:
```bash
# Try python3
python3 --version

# Add to PATH (Linux/macOS)
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Windows: Add Python to System PATH via Control Panel
```

### Package Installation Problems

#### Issue: "pip: command not found"
**Solutions**:
```bash
# Install pip
# Ubuntu/Debian
sudo apt install python3-pip

# macOS
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py

# Verify pip installation
pip --version
python3 -m pip --version
```

#### Issue: "Permission denied during installation"
**Solutions**:
```bash
# Use virtual environment (recommended)
python3 -m venv qbit-env
source qbit-env/bin/activate  # Linux/macOS
# qbit-env\Scripts\activate   # Windows
pip install qbit-torrent-extract

# Or install for user only
pip install --user qbit-torrent-extract

# Check user installation path
python -m site --user-site
```

#### Issue: "Failed building wheel" or compilation errors
**Solutions**:
```bash
# Install build dependencies
# Ubuntu/Debian
sudo apt install build-essential python3-dev

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel

# macOS
xcode-select --install

# Retry installation
pip install --upgrade pip setuptools wheel
pip install qbit-torrent-extract
```

### Dependency Installation Issues

#### Issue: "rarfile.RarCannotExec: Unrar not installed"
**Solutions**:
```bash
# Install unrar
# Ubuntu/Debian
sudo apt install unrar

# CentOS/RHEL (requires EPEL)
sudo yum install epel-release
sudo yum install unrar

# macOS
brew install unrar

# Verify installation
unrar --version

# Set UNRAR_TOOL if needed
export UNRAR_TOOL=/usr/bin/unrar
```

#### Issue: "py7zr import error"
**Solutions**:
```bash
# Reinstall py7zr
pip uninstall py7zr
pip install py7zr

# Or install system 7z
# Ubuntu/Debian
sudo apt install p7zip-full

# macOS
brew install p7zip

# Test 7z functionality
python -c "import py7zr; print('7z support OK')"
```

## Configuration Problems

### Invalid Configuration Files

#### Issue: "JSON decode error" in configuration file
**Symptoms**: Configuration file cannot be parsed
**Solutions**:
```bash
# Validate JSON syntax
python -m json.tool config.json

# Use online JSON validator
# Check for common issues:
# - Missing commas
# - Trailing commas
# - Unquoted strings
# - Invalid escape sequences

# Example valid configuration
cat > config.json << 'EOF'
{
  "max_extraction_ratio": 100.0,
  "preserve_originals": true,
  "log_level": "INFO"
}
EOF
```

#### Issue: "Configuration validation failed"
**Symptoms**: Configuration values are rejected
**Solutions**:
```bash
# Check parameter ranges
{
  "max_extraction_ratio": 50.0,     # Must be 1.0-10000.0
  "max_nested_depth": 3,            # Must be 1-10
  "log_level": "INFO",              # Must be DEBUG/INFO/WARNING/ERROR
  "log_rotation_size": 10485760,    # Must be 1024-1073741824
  "log_rotation_count": 5           # Must be 1-50
}

# Test configuration
qbit-torrent-extract --config config.json --help
```

### Path and Permission Issues

#### Issue: "Permission denied" accessing configuration/log directories
**Solutions**:
```bash
# Check directory permissions
ls -la ~/.qbit-torrent-extract/

# Create directories with correct permissions
mkdir -p ~/.qbit-torrent-extract/logs
chmod 755 ~/.qbit-torrent-extract
chmod 755 ~/.qbit-torrent-extract/logs

# Use alternative location
{
  "log_dir": "/tmp/qbit-logs",
  "stats_file": "/tmp/qbit-stats.json"
}
```

#### Issue: "Log directory not found"
**Solutions**:
```bash
# Enable auto-creation in config
{
  "log_dir": "~/qbit-logs"  # Will be created automatically
}

# Or create manually
mkdir -p ~/qbit-logs

# Check path expansion
python -c "import os; print(os.path.expanduser('~/qbit-logs'))"
```

## Archive Extraction Issues

### Archive Format Problems

#### Issue: "Unsupported archive type"
**Symptoms**: Archives are skipped or ignored
**Solutions**:
```bash
# Check supported extensions
qbit-torrent-extract --help | grep -A5 "supported"

# Add extensions to config
{
  "supported_extensions": [".zip", ".rar", ".7z", ".tar.gz", ".tgz", ".tar.bz2"]
}

# Verify archive type
file archive.zip
unzip -t archive.zip
```

#### Issue: "Corrupted archive detected"
**Symptoms**: Archives fail validation
**Solutions**:
```bash
# Test archive integrity
unzip -t archive.zip
unrar t archive.rar
7z t archive.7z

# Check file size and permissions
ls -la archive.zip

# Try manual extraction
unzip archive.zip
```

### Password-Protected Archives

#### Issue: "Password-protected archive detected"
**Symptoms**: Archives are skipped
**Current Limitation**: Password-protected archives are not supported
**Workaround**:
```bash
# Extract manually first
unrar x -pPASSWORD archive.rar

# Or extract to different location
mkdir extracted
cd extracted
unrar x -pPASSWORD ../archive.rar
```

### Zipbomb Protection

#### Issue: "Zipbomb detected" or extraction fails due to size limits
**Symptoms**: Large compressed files fail extraction
**Solutions**:
```bash
# Increase extraction ratio limit
qbit-torrent-extract /path --max-ratio 500.0

# Or in configuration
{
  "max_extraction_ratio": 500.0
}

# Check actual compression ratio
unzip -l archive.zip  # See compressed vs uncompressed sizes
```

### Nested Archive Limits

#### Issue: "Maximum nested depth reached"
**Symptoms**: Deeply nested archives stop extracting
**Solutions**:
```bash
# Increase nesting depth
qbit-torrent-extract /path --max-depth 5

# Or in configuration
{
  "max_nested_depth": 5
}

# Check nesting structure manually
unzip archive.zip
ls -la  # Look for more archives inside
```

## qBittorrent Integration Problems

### Command Configuration Issues

#### Issue: "External program failed" in qBittorrent
**Symptoms**: qBittorrent shows external program execution failed
**Solutions**:

1. **Verify Python path**:
```bash
# Find Python executable
which python3
/usr/bin/python3 --version

# Test command manually
/usr/bin/python3 -m qbit_torrent_extract --help
```

2. **Use absolute paths**:
```bash
# Instead of: python -m qbit_torrent_extract "%F"
# Use: /usr/bin/python3 -m qbit_torrent_extract "%F"
```

3. **Test with simple command first**:
```bash
# qBittorrent setting: echo "%F" > /tmp/qbit-test.txt
# Check if file is created with torrent path
```

#### Issue: "Module not found" when run from qBittorrent
**Symptoms**: Works in terminal but fails in qBittorrent
**Solutions**:
```bash
# Use virtual environment with full path
/path/to/venv/bin/python -m qbit_torrent_extract "%F"

# Or install system-wide
sudo pip3 install qbit-torrent-extract

# Check module installation
python3 -c "import qbit_torrent_extract; print('Module found')"
```

### Variable Substitution Problems

#### Issue: "No such file or directory" with qBittorrent variables
**Symptoms**: Paths with %F, %N don't work correctly
**Solutions**:

1. **Test variable expansion**:
```bash
# qBittorrent setting for testing:
echo "F=%F N=%N" > /tmp/qbit-vars.txt

# Check file contents to see if variables are expanded
```

2. **Handle spaces in paths**:
```bash
# Use quotes around %F
"/path/to/python" -m qbit_torrent_extract "%F" --torrent-name "%N"
```

3. **Escape special characters**:
```bash
# For complex paths, use shell escaping
bash -c '/path/to/python -m qbit_torrent_extract "$1" --torrent-name "$2"' -- "%F" "%N"
```

### Permission and Access Issues

#### Issue: "Permission denied" when qBittorrent runs extraction
**Symptoms**: Works manually but fails from qBittorrent
**Solutions**:
```bash
# Check qBittorrent user/permissions
ps aux | grep qbittorrent

# Ensure extraction tool has same permissions
# Run qBittorrent as user with appropriate permissions

# Or give broader permissions to extraction location
chmod 755 /downloads
chown -R qbittorrent:qbittorrent /downloads
```

## Performance Issues

### Slow Extraction

#### Issue: "Extraction takes very long time"
**Symptoms**: Large archives process slowly
**Solutions**:

1. **Check system resources**:
```bash
# Monitor during extraction
top -p $(pgrep python)
iostat 1  # Check disk I/O
df -h     # Check disk space
```

2. **Optimize configuration**:
```json
{
  "progress_indicators": false,  // Reduces overhead
  "log_level": "WARNING",       // Less logging
  "max_nested_depth": 2         // Reduce nesting
}
```

3. **System optimization**:
```bash
# Use faster storage for temporary files
export TMPDIR=/path/to/fast/storage

# Increase available memory
# Close other applications
```

### Memory Usage Issues

#### Issue: "Out of memory" or excessive RAM usage
**Symptoms**: System becomes unresponsive during extraction
**Solutions**:

1. **Monitor memory usage**:
```bash
# During extraction
watch -n 1 'ps -o pid,ppid,cmd,%mem,%cpu -p $(pgrep python)'

# System memory
free -h
```

2. **Process smaller batches**:
```bash
# Extract fewer archives at once
# Move some archives to different directory temporarily
```

3. **Increase swap space**:
```bash
# Linux - add swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Disk Space Problems

#### Issue: "No space left on device"
**Symptoms**: Extraction fails due to insufficient disk space
**Solutions**:

1. **Check available space**:
```bash
df -h /path/to/extraction/directory
du -sh /path/to/archives/*
```

2. **Clean up space**:
```bash
# Remove old logs
find ~/.qbit-torrent-extract/logs -name "*.log.*" -mtime +7 -delete

# Clean temporary files
rm -rf /tmp/qbit-*
```

3. **Use different extraction location**:
```bash
# Extract to different drive with more space
qbit-torrent-extract /archives --config config.json
# Then move files back if needed
```

## Logging and Statistics Issues

### Log File Problems

#### Issue: "Cannot create log file"
**Symptoms**: Logging fails to start
**Solutions**:
```bash
# Check log directory permissions
ls -la ~/.qbit-torrent-extract/
mkdir -p ~/.qbit-torrent-extract/logs
chmod 755 ~/.qbit-torrent-extract/logs

# Use alternative log location
{
  "log_dir": "/tmp/qbit-logs"
}

# Test log creation
touch ~/.qbit-torrent-extract/logs/test.log
```

#### Issue: "Log files grow too large"
**Symptoms**: Disk space consumed by logs
**Solutions**:
```json
{
  "log_rotation_size": 5242880,    // 5MB instead of 10MB
  "log_rotation_count": 3,         // Keep fewer backups
  "log_level": "WARNING"           // Less verbose logging
}
```

#### Issue: "Cannot read log files"
**Symptoms**: Log files exist but are empty or unreadable
**Solutions**:
```bash
# Check file permissions
ls -la ~/.qbit-torrent-extract/logs/

# Check file encoding
file ~/.qbit-torrent-extract/logs/qbit-torrent-extract.log

# View recent logs
tail -f ~/.qbit-torrent-extract/logs/qbit-torrent-extract.log
```

### Statistics Problems

#### Issue: "Statistics not being recorded"
**Symptoms**: Stats file empty or not created
**Solutions**:
```bash
# Check stats file configuration
{
  "stats_file": "~/.qbit-torrent-extract/stats.json"
}

# Test stats file creation
touch ~/.qbit-torrent-extract/stats.json
echo '{}' > ~/.qbit-torrent-extract/stats.json

# Check file permissions
ls -la ~/.qbit-torrent-extract/stats.json
```

#### Issue: "Corrupted statistics file"
**Symptoms**: JSON parse error in stats file
**Solutions**:
```bash
# Validate JSON
python -m json.tool ~/.qbit-torrent-extract/stats.json

# Backup and reset
cp ~/.qbit-torrent-extract/stats.json ~/.qbit-torrent-extract/stats.json.backup
echo '{"runs": [], "aggregated": {}}' > ~/.qbit-torrent-extract/stats.json

# Check for file locks
lsof ~/.qbit-torrent-extract/stats.json
```

## Security and Validation Issues

### Archive Validation Failures

#### Issue: "Archive validation failed" for legitimate archives
**Symptoms**: Valid archives are rejected
**Solutions**:

1. **Check validation criteria**:
```bash
# Test archive manually
unzip -t archive.zip
unrar t archive.rar

# Check compression ratio
unzip -l archive.zip  # Compare compressed vs uncompressed
```

2. **Adjust security settings**:
```json
{
  "max_extraction_ratio": 200.0,  // Allow higher compression ratios
  "max_nested_depth": 4           // Allow deeper nesting
}
```

3. **Bypass validation temporarily**:
```bash
# Test extraction without validation
unzip archive.zip
# If successful, adjust configuration
```

### False Positive Security Alerts

#### Issue: "Zipbomb detected" for normal archives
**Symptoms**: Compressed files trigger security alerts
**Solutions**:

1. **Analyze compression ratio**:
```bash
# Check actual ratio
unzip -l large.zip | tail -1
# Compare "compressed" vs "uncompressed" sizes
```

2. **Adjust threshold**:
```json
{
  "max_extraction_ratio": 500.0  // Increase for legitimate high-compression files
}
```

3. **Whitelist specific files**:
```bash
# Extract problematic files manually first
# Then process remaining archives
```

## Platform-Specific Issues

### Windows Issues

#### Issue: "Path too long" errors
**Solutions**:
```bash
# Enable long path support in Windows 10+
# Group Policy: Computer Configuration > Administrative Templates > System > Filesystem
# Enable "Enable Win32 long paths"

# Or use shorter extraction paths
# Extract to C:\temp\ instead of deep nested folders
```

#### Issue: "Access denied" on Windows
**Solutions**:
```bash
# Run as Administrator
# Right-click Command Prompt > "Run as administrator"

# Check Windows Defender exclusions
# Add extraction directory to Windows Defender exclusions

# Use Windows Subsystem for Linux (WSL)
```

### macOS Issues

#### Issue: "Operation not permitted" on macOS
**Solutions**:
```bash
# Grant Full Disk Access to Terminal
# System Preferences > Security & Privacy > Privacy > Full Disk Access

# Use sudo for system directories
sudo qbit-torrent-extract /System/Volumes/Data/downloads

# Check quarantine attributes
xattr -r -d com.apple.quarantine /path/to/archives
```

#### Issue: "Unidentified developer" warnings
**Solutions**:
```bash
# Allow in System Preferences
# System Preferences > Security & Privacy > General > Allow apps downloaded from: anywhere

# Or bypass for specific file
sudo spctl --master-disable
```

### Linux Issues

#### Issue: "SELinux preventing access"
**Solutions**:
```bash
# Check SELinux status
sestatus

# Temporarily disable
sudo setenforce 0

# Add SELinux context
sudo setsebool -P allow_execstack 1

# Check audit logs
sudo ausearch -m avc -ts recent
```

#### Issue: "AppArmor blocking execution"
**Solutions**:
```bash
# Check AppArmor status
sudo aa-status

# Disable for python
sudo aa-disable /usr/bin/python3

# Check logs
sudo journalctl -xe | grep apparmor
```

## Advanced Troubleshooting

### Debugging with Python

#### Enable Python debugging
```bash
# Run with Python debugging
python -X dev -m qbit_torrent_extract /path --verbose

# Enable all warnings
python -W all -m qbit_torrent_extract /path
```

#### Trace execution
```python
import trace
tracer = trace.Trace(count=False, trace=True)
# Run extraction with tracer
```

### Network and Firewall Issues

#### Issue: "Network timeout" or connection issues
**Solutions**:
```bash
# Check firewall rules
sudo iptables -L
sudo ufw status

# Test network connectivity
ping 8.8.8.8
curl -I http://example.com

# Bypass proxy if needed
export no_proxy="*"
```

### System Resource Monitoring

#### Monitor system during extraction
```bash
# CPU and memory
htop

# Disk I/O
iotop

# File operations
strace -e file python -m qbit_torrent_extract /path

# Open files
lsof -p $(pgrep python)
```

### Process and Thread Analysis

#### Debug hanging processes
```bash
# Check process status
ps aux | grep python

# Send SIGQUIT for stack trace
kill -QUIT $(pgrep python)

# Use gdb for debugging
gdb python
(gdb) attach PID
(gdb) thread apply all bt
```

## Getting Help

### Information to Collect

When reporting issues, include:

1. **System Information**:
```bash
# Operating system
uname -a
lsb_release -a  # Linux

# Python version
python --version

# Package versions
pip list | grep -E "(qbit|rarfile|py7zr|click|tqdm)"
```

2. **Configuration**:
```bash
# Sanitized configuration file
cat config.json

# Command line used
qbit-torrent-extract --help
```

3. **Error Information**:
```bash
# Full error output
qbit-torrent-extract /path --verbose 2>&1 | tee error.log

# Recent log entries
tail -50 ~/.qbit-torrent-extract/logs/qbit-torrent-extract.log
```

4. **Archive Information**:
```bash
# Archive details (without exposing sensitive content)
file archive.zip
unzip -l archive.zip | head -20
ls -la archive.zip
```

### Support Channels

1. **GitHub Issues**: For bugs and feature requests
2. **Documentation**: Check API documentation and configuration reference
3. **Community Forums**: For general questions and discussions
4. **Stack Overflow**: Tag questions with `qbit-torrent-extract`

### Self-Help Resources

1. **Enable verbose logging**: Always include `--verbose` output
2. **Check recent changes**: Review configuration and system changes
3. **Test with minimal setup**: Use default configuration
4. **Search existing issues**: Check GitHub issues for similar problems
5. **Test with different archives**: Isolate archive-specific vs system issues

### Creating Effective Bug Reports

Include:
- Clear description of expected vs actual behavior
- Minimal steps to reproduce the issue
- Complete error messages and stack traces
- System and version information
- Sample configuration files (sanitized)
- Sample archive files (if not sensitive)

For security-related issues, use private communication channels and avoid posting sensitive information publicly.