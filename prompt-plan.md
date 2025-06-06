# Prompt Plan for qbit-torrent-extract Development

## Stage 1: Project Setup and Basic Structure

### Prompt 1: Initial Setup
```
Create the basic project structure for qbit-torrent-extract. Include:
1. Directory structure
2. Empty __init__.py files
3. Basic setup.py
4. requirements.txt with core dependencies
5. README.md template
```

### Prompt 2: Configuration System
```
Implement a configuration system that handles:
1. Default settings
2. Command line overrides
3. Size ratio limits for zipbomb protection
4. Logging paths and levels
Show the implementation and explain the design choices.
```

## Stage 2: Core Functionality

### Prompt 3: Archive Detection and Validation
```
Implement the archive detection and validation system that:
1. Identifies supported archive types (.zip, .rar, .7z, .tar.gz, .tgz)
2. Performs basic validation
3. Implements zipbomb protection
4. Handles nested archive depth checking
Include unit tests for this functionality.
```

### Prompt 4: Extraction System
```
Create the core extraction system that:
1. Handles all supported archive types
2. Manages nested archives
3. Preserves original files
4. Implements skip-and-continue error handling
Include error handling and progress indicators.
```

## Stage 3: Logging and Monitoring

### Prompt 5: Logging System
```
Implement the logging system with:
1. Multiple log levels (normal/verbose)
2. Per-torrent log files
3. Log rotation
4. Structured log format
Show the implementation and example outputs.
```

### Prompt 6: Statistics Tracking
```
Create the statistics tracking system that:
1. Records success/failure counts
2. Tracks processed files
3. Maintains error type statistics
4. Implements atomic writes for stats updates
```

## Stage 4: Integration and Testing

### Prompt 7: CLI Implementation
```
Implement the command-line interface with:
1. All specified options
2. Help documentation
3. Version information
4. Input validation
```

### Prompt 8: qBittorrent Integration
```
Create documentation and examples for:
1. qBittorrent configuration
2. Command line usage
3. Common troubleshooting
4. Best practices
```

### Prompt 9: Testing Suite
```
Implement comprehensive tests:
1. Unit tests for each component
2. Integration tests
3. Security tests (zipbomb, corruption)
4. Performance tests
```

## Stage 5: Documentation and Deployment

### Prompt 10: Documentation
```
Create comprehensive documentation:
1. Installation guide
2. Configuration reference
3. Troubleshooting guide
4. API documentation
```

### Prompt 11: Packaging
```
Prepare for distribution:
1. Package configuration
2. Dependencies
3. Installation scripts
4. Release documentation
```

## Development Notes
- Each prompt should be run sequentially
- Review and test output of each stage before proceeding
- Keep code modular and testable
- Maintain consistent error handling throughout
- Document all major decisions and assumptions
- Use type hints and docstrings consistently

## Expected Deliverables for Each Stage
1. Working code with tests
2. Documentation updates
3. Test coverage reports
4. Example outputs where applicable

## Review Points
After each stage, verify:
1. Code quality and style
2. Test coverage
3. Documentation completeness
4. Error handling
5. Performance considerations
