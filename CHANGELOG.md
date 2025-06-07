# Changelog

All notable changes to qbit-torrent-extract will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite with 148 tests covering security, performance, and integration
- Advanced logging system with per-torrent log files and rotation
- Statistics tracking with JSON persistence and aggregation
- Full API documentation and user guides
- Support for .7z and .tar.gz/.tgz archives
- Password-protected archive detection
- Zipbomb protection with configurable ratios
- Nested archive depth limiting
- Path traversal attack prevention
- Progress indicators with tqdm
- Configuration file support (JSON)
- Environment variable configuration
- Command-line option overrides
- Short command alias `qte`

### Changed
- Enhanced CLI with comprehensive options
- Improved error handling with skip-and-continue approach
- Better qBittorrent integration documentation
- More detailed troubleshooting guides

### Fixed
- Archive validation for edge cases
- Memory usage optimization for large archives
- Log file encoding issues on Windows

## [0.1.0] - 2024-XX-XX

### Added
- Initial release of qbit-torrent-extract
- Core extraction functionality for ZIP and RAR archives
- Basic nested archive support
- qBittorrent integration via external program execution
- Configuration system with defaults and overrides
- Validation system for archive integrity
- Basic logging to console and files
- Preserve/delete original archives option
- Cross-platform support (Windows, macOS, Linux)
- Basic documentation and examples

### Known Issues
- Password-protected archives are not supported (detected and skipped)
- Some exotic archive formats may not be recognized
- Performance with extremely large archives (>10GB) may vary

## Installation Notes

### System Requirements
- Python 3.8 or higher
- unrar command-line tool for RAR support
- p7zip for 7z file support

### Breaking Changes
None in initial release.

## Migration Guide
Not applicable for initial release.

## Contributors
- Your Name (@yourusername) - Initial implementation

## Acknowledgments
- Inspired by the universal frustration of "No files found are eligible for import"
- Thanks to the *arr app community for the motivation
- Special mention to BitBook and similar release groups for their creative archive nesting

[Unreleased]: https://github.com/yourusername/qbit-torrent-extract/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/qbit-torrent-extract/releases/tag/v0.1.0