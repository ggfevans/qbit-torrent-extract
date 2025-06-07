# qbit-torrent-extract Improvement Specification

## Overview
This specification defines improvements to be implemented for the qbit-torrent-extract project. The project is well-architected but requires core implementation completion and several enhancements.

## 1. Complete Core Implementation

### 1.1 Priority: CRITICAL
The following modules need their core functionality implemented based on the existing test suite:

### 1.2 Implementation Requirements

#### 1.2.1 `src/qbit_torrent_extract/extractor.py`
Implement the `ArchiveExtractor` class with the following methods and behavior:

**Core Methods:**
- `__init__(preserve_archives=True, log_level=logging.INFO, config=None, torrent_name=None)`
- `extract_all(directory: str) -> Dict[str, any]`
- `get_archive_files(directory: str) -> List[Path]`
- `get_extraction_stats() -> Dict[str, any]`

**Extraction Methods (private):**
- `_extract_single_archive(archive_path: Path) -> bool`
- `_extract_zip(archive_path: Path) -> bool`
- `_extract_rar(archive_path: Path) -> bool`
- `_extract_7z(archive_path: Path) -> bool`
- `_extract_tar(archive_path: Path, archive_type: str) -> bool`

**Behavior Requirements:**
- Support nested archive extraction up to `max_nested_depth`
- Track already processed archives to avoid duplication
- Return statistics dictionary with keys: `total_processed`, `successful`, `failed`, `skipped`, `errors`
- Support progress indicators via tqdm when enabled
- Handle corrupted archives gracefully
- Delete original archives if `preserve_archives=False`

#### 1.2.2 `src/qbit_torrent_extract/validator.py`
Implement the `ArchiveValidator` class:

**Core Methods:**
- `validate_archive(archive_path: Path) -> ValidationResult`
- `detect_archive_type(archive_path: Path) -> Optional[str]`
- `check_nested_depth(archive_path: Path, current_depth: int = 0) -> Tuple[bool, int]`
- `scan_directory(directory: Path) -> Dict[Path, ValidationResult]`

**Validation Checks:**
- Zipbomb protection (compression ratio check)
- Password-protected archive detection
- Archive corruption detection
- Path traversal attack prevention
- Nested depth limit enforcement

**Supported Archive Types:**
- ZIP (.zip)
- RAR (.rar)
- 7Z (.7z)
- TAR (.tar, .tar.gz, .tgz)

#### 1.2.3 `src/qbit_torrent_extract/logger.py`
Implement the enhanced logging system:

**Classes:**
- `StructuredFormatter`: Custom formatter with context support
- `TorrentLogManager`: Per-torrent log file management
- `LoggingManager`: Central logging coordinator

**Key Features:**
- Per-torrent log files with sanitized filenames
- Log rotation support
- Structured logging with contextual information
- Thread-safe operation

#### 1.2.4 `src/qbit_torrent_extract/statistics.py`
Implement comprehensive statistics tracking:

**Classes:**
- `StatisticsManager`: Main statistics coordinator
- `ArchiveStats`: Individual archive statistics
- `ExtractionRunStats`: Per-run statistics
- `AggregatedStats`: Cross-run aggregated statistics

**Features:**
- JSON persistence
- Atomic file writes
- Performance metrics calculation
- Error categorization

#### 1.2.5 `src/qbit_torrent_extract/config.py`
Already partially implemented, ensure:
- Validation of all parameters
- Path expansion for home directories
- Override hierarchy: CLI > Environment > File > Defaults

### 1.3 Testing Requirements
All existing tests in the `tests/` directory must pass:
- 148 total tests
- No modifications to test files allowed
- Tests define the expected behavior

## 2. Fix Dependency Conflicts

### 2.1 Priority: HIGH
Clean up `pyproject.toml` to have a single, complete project definition.

### 2.2 Implementation:
Remove the duplicate `[project]` section at the bottom of the file that shows:
```toml
[project]
name = "qbit-torrent-extract"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"
dependencies = []
```

Keep only the comprehensive project definition that includes all dependencies and metadata.

## 3. RAR Support Clarity

### 3.1 Priority: MEDIUM
Add a clear Prerequisites section at the top of README.md.

### 3.2 Implementation:
Add after the project description, before "Features":

```markdown
## Prerequisites

Before installing qbit-torrent-extract, ensure you have the following system dependencies:

- **Python 3.8+**
- **unrar** - Required for RAR archive support
  - Ubuntu/Debian: `sudo apt install unrar`
  - macOS: `brew install unrar`
  - Windows: Install WinRAR or 7-Zip
- **p7zip** - Required for 7z archive support
  - Ubuntu/Debian: `sudo apt install p7zip-full`
  - macOS: `brew install p7zip`
  - Windows: Install 7-Zip

**Note:** Without these system dependencies, extraction of RAR and 7z archives will fail.
```

## 4. Standalone Script Mode

### 4.1 Priority: MEDIUM
Add support for running without virtual environment activation.

### 4.2 Implementation:

#### 4.2.1 Create `bin/qbit-extract`
```python
#!/usr/bin/env python3
"""Standalone executable for qbit-torrent-extract."""
import sys
import os

# Add src to path to allow running without installation
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(script_dir, 'src'))

from qbit_torrent_extract.main import main

if __name__ == '__main__':
    main()
```

#### 4.2.2 Update setup.py
Add to the `setup()` call:
```python
scripts=['bin/qbit-extract'],
```

#### 4.2.3 Make executable
Ensure the script has executable permissions in the repository.

## 5. System Requirements Check

### 5.1 Priority: MEDIUM
Add runtime checking for system dependencies.

### 5.2 Implementation:

#### 5.2.1 Add to `src/qbit_torrent_extract/utils.py` (new file):
```python
"""Utility functions for qbit-torrent-extract."""
import shutil
import sys
from typing import List, Tuple

def check_system_requirements() -> Tuple[bool, List[str]]:
    """Check if required system tools are available.
    
    Returns:
        Tuple of (all_present, missing_tools)
    """
    required_tools = {
        'unrar': 'RAR archive support',
        '7z': '7z archive support'
    }
    
    missing = []
    for tool, description in required_tools.items():
        if not shutil.which(tool):
            missing.append(f"{tool} ({description})")
    
    return len(missing) == 0, missing

def print_missing_requirements(missing: List[str]) -> None:
    """Print helpful message about missing requirements."""
    print("Missing system requirements:", file=sys.stderr)
    for tool in missing:
        print(f"  - {tool}", file=sys.stderr)
    print("\nPlease install missing tools. See README.md for instructions.", file=sys.stderr)
```

#### 5.2.2 Update `main.py`
Add at the start of the `main()` function:
```python
# Check system requirements
from .utils import check_system_requirements, print_missing_requirements
all_present, missing = check_system_requirements()
if not all_present and not config.skip_on_error:
    print_missing_requirements(missing)
    click.echo("Use --skip-on-error to continue anyway.", err=True)
    sys.exit(1)
elif not all_present:
    logger.warning(f"Missing system tools: {', '.join(missing)}")
```

## 6. Debian Package Support

### 6.1 Priority: LOW
Add infrastructure for building .deb packages.

### 6.2 Implementation:

#### 6.2.1 Create `debian/` directory structure:
```
debian/
├── control
├── changelog
├── compat
├── rules
├── qbit-torrent-extract.install
└── qbit-torrent-extract.postinst
```

#### 6.2.2 `debian/control`:
```
Source: qbit-torrent-extract
Section: utils
Priority: optional
Maintainer: Your Name <your.email@example.com>
Build-Depends: debhelper (>= 9), python3, python3-setuptools, dh-python
Standards-Version: 4.5.0
Homepage: https://github.com/yourusername/qbit-torrent-extract

Package: qbit-torrent-extract
Architecture: all
Depends: ${python3:Depends}, ${misc:Depends}, python3-click, python3-tqdm, unrar, p7zip-full
Description: Automated nested archive extraction for qBittorrent
 Extracts nested archives (ZIP/RAR/7z) from completed torrent downloads.
 Integrates with qBittorrent's "Run external program on torrent completion"
 feature to ensure *arr applications can find extracted files.
```

#### 6.2.3 `debian/rules`:
```makefile
#!/usr/bin/make -f

%:
	dh $@ --with python3 --buildsystem=pybuild
```

#### 6.2.4 Add to README.md:
```markdown
### Debian/Ubuntu Package Installation

For Debian/Ubuntu users, a .deb package can be built:

```bash
# Install build dependencies
sudo apt install debhelper python3-all python3-setuptools dh-python

# Build the package
cd qbit-torrent-extract
dpkg-buildpackage -us -uc

# Install the package
sudo dpkg -i ../qbit-torrent-extract_*.deb
```
```

## 7. Integration Tests

### 7.1 Priority: LOW
Add integration tests with mock qBittorrent scenarios.

### 7.2 Implementation:
Create `tests/test_qbittorrent_integration.py` with tests that simulate:
- qBittorrent calling with various parameter combinations
- Handling of qBittorrent path variables (%F, %N, etc.)
- Permission scenarios common in qBittorrent setups

## Delivery Checklist

- [ ] All core modules implemented and passing tests
- [ ] pyproject.toml cleaned up
- [ ] Prerequisites section added to README
- [ ] Standalone script created and tested
- [ ] System requirements checker implemented
- [ ] Debian package structure created
- [ ] All 148 existing tests passing
- [ ] Code follows existing style and patterns
- [ ] Documentation updated where needed

## Notes for Developer

1. **Test-Driven Development**: The test suite is comprehensive. Run tests frequently during implementation.
2. **Error Handling**: Follow the pattern of graceful degradation - log errors but continue processing when `skip_on_error=True`.
3. **Threading**: The statistics and logging systems must be thread-safe.
4. **Backwards Compatibility**: The command-line interface and configuration format must remain compatible with the documented behavior.
