# qbit-torrent-extract Project Specification

## Project Overview
A command-line tool that automatically extracts nested archives from completed qBittorrent downloads, designed to be triggered by qBittorrent's "Run external program on torrent completion" feature.

## Core Requirements

### Archive Support
- Primary formats: .zip, .rar
- Additional formats: .7z, .tar.gz, .tgz
- Extract nested archives (archives within archives)
- Preserve original archives for seeding
- Extract to original location

### Security Features
- Basic archive validation before extraction
- Zipbomb protection via size ratio checks
- Maximum nested archive depth limit
- Skip corrupted/invalid archives
- Skip password-protected archives

### Error Handling
- Skip-and-continue approach for all errors
- Comprehensive error logging
- Continue processing other files on any error
- Handle insufficient disk space gracefully
- Handle file permission issues

### Logging System
1. Log Levels:
   - Normal: Success/failure per folder path
   - Verbose: All actions taken

2. Log Organization:
   - Central log directory
   - Separate log file per processed torrent path
   - Basic log rotation to prevent excessive size

3. Log Format:
   - Timestamp
   - Action type
   - Path
   - Result
   - Error details (if any)

4. Statistics Tracking:
   - Separate statistics file
   - Track success/failure counts
   - Track processed file counts
   - Track error types

### Performance & Resource Management
- Handle large (multi-GB) archives
- Process multiple nested archives
- Handle many small archives efficiently
- Basic resource management
- Progress indicators for large extractions

## Command Line Interface
```bash
qbit-torrent-extract [OPTIONS] DIRECTORY

Options:
  --verbose              Enable verbose logging
  --max-depth INTEGER    Maximum nested archive depth
  --help                 Show help message
  --version             Show version
```

## Configuration
- Max nested depth (default: 3)
- Log directory path
- Size ratio limits for zipbomb protection
- Resource usage limits

## Integration
- Primary: qBittorrent "Run external program on torrent completion"
- Command format: `qbit-torrent-extract "%F"`
