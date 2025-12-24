# Changelog

## [0.2.0] - 2024-12-24

### Changed
- Simplified codebase from ~2,200 LOC to ~700 LOC
- Removed over-engineered statistics tracking system
- Removed per-torrent logging (nobody reads those)
- Simplified configuration options
- Updated minimum Python version to 3.9

### Added
- Split RAR archive detection (`.r00`, `.part1.rar`)
- Incomplete download detection (`.!qb`, `.part`, `.crdownload`)
- Tarfile path traversal protection (CVE-2007-4559)

### Removed
- `--torrent-name` CLI option
- `--stats-file`, `--show-stats`, `--export-stats` CLI options
- `statistics.py` module
- Per-torrent log files
- 3,000+ lines of documentation nobody reads

## [0.1.0] - 2024-XX-XX

### Added
- Initial release
- ZIP, RAR, 7z, TAR extraction
- Nested archive support
- qBittorrent integration
- Zipbomb protection
- Basic logging
