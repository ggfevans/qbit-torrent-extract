# Prompt Plan for qbit-torrent-extract Development

## Progress Summary
**Overall Completion**: 3/11 prompts complete (27%)
- ✅ Complete: 3
- 🚧 In Progress: 0
- ⚠️ Partial: 5
- ❌ Not Started: 3

## Completion Checklist

### Stage 1: Project Setup and Basic Structure
- [x] Prompt 1: Initial Setup
- [x] Prompt 2: Configuration System

### Stage 2: Core Functionality  
- [x] Prompt 3: Archive Detection and Validation
- [ ] Prompt 4: Extraction System ⚠️

### Stage 3: Logging and Monitoring
- [ ] Prompt 5: Logging System ⚠️
- [ ] Prompt 6: Statistics Tracking

### Stage 4: Integration and Testing
- [ ] Prompt 7: CLI Implementation ⚠️
- [ ] Prompt 8: qBittorrent Integration ⚠️
- [ ] Prompt 9: Testing Suite ⚠️

### Stage 5: Documentation and Deployment
- [ ] Prompt 10: Documentation
- [ ] Prompt 11: Packaging

## Git Workflow Guidelines

### Branch Strategy
- Use feature branches for each prompt/feature: `feature/prompt-N-description`
- Example: `feature/prompt-2-config-system`
- Keep main branch stable and working
- Create pull requests for review before merging

### Commit Message Format
```
<type>: <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or modifications
- `refactor`: Code refactoring
- `chore`: Build process or auxiliary tool changes

Example:
```
feat: add configuration system with JSON support

- Implement Config dataclass with validation
- Add support for JSON config files
- Enable command-line overrides
- Include zipbomb protection settings
```

### Development Process per Prompt
1. Create feature branch: `git checkout -b feature/prompt-N-description`
2. Implement the feature with regular commits
3. Run tests: `pytest tests/`
4. Run linting/type checking if available
5. Create PR or merge to main when complete
6. Tag completion: `git tag prompt-N-complete`

## Stage 1: Project Setup and Basic Structure

### Prompt 1: Initial Setup ✅ COMPLETED
```
Create the basic project structure for qbit-torrent-extract. Include:
1. Directory structure
2. Empty __init__.py files
3. Basic setup.py
4. requirements.txt with core dependencies
5. README.md template
```
**Status**: Complete in initial commit

### Prompt 2: Configuration System ✅ COMPLETED
```
Implement a configuration system that handles:
1. Default settings
2. Command line overrides
3. Size ratio limits for zipbomb protection
4. Logging paths and levels
Show the implementation and explain the design choices.
```
**Branch**: `feature/prompt-2-config-system`

**Subtasks:**
- [x] Create Config dataclass with defaults
- [x] Implement JSON config file support
- [x] Add command-line override mechanism
- [x] Add validation for config values
- [x] Write comprehensive tests
- [x] Integrate with CLI and extractor module
- [ ] Document configuration options (deferred to Prompt 10)

## Stage 2: Core Functionality

### Prompt 3: Archive Detection and Validation ✅ COMPLETED
```
Implement the archive detection and validation system that:
1. Identifies supported archive types (.zip, .rar, .7z, .tar.gz, .tgz)
2. Performs basic validation
3. Implements zipbomb protection
4. Handles nested archive depth checking
Include unit tests for this functionality.
```

**Subtasks:**
- [x] Create archive validator module
- [x] Implement file type detection
- [x] Add zipbomb protection (size ratio check)
- [x] Implement nested depth tracking
- [x] Add corruption detection
- [x] Write unit tests (14 tests)
- [ ] Document security features (deferred to Prompt 10)

### Prompt 4: Extraction System ⚠️ PARTIAL
```
Create the core extraction system that:
1. Handles all supported archive types
2. Manages nested archives
3. Preserves original files
4. Implements skip-and-continue error handling
Include error handling and progress indicators.
```
**Status**: Basic .zip and .rar extraction exists, missing .7z, .tar.gz support and nested handling

**Subtasks:**
- [x] Basic .zip extraction
- [x] Basic .rar extraction
- [ ] Add .7z support (py7zr library)
- [ ] Add .tar.gz/.tgz support
- [ ] Implement nested archive extraction
- [ ] Add comprehensive error handling
- [ ] Improve progress indicators
- [ ] Add extraction validation

## Stage 3: Logging and Monitoring

### Prompt 5: Logging System ⚠️ PARTIAL
```
Implement the logging system with:
1. Multiple log levels (normal/verbose)
2. Per-torrent log files
3. Log rotation
4. Structured log format
Show the implementation and example outputs.
```
**Status**: Basic logging exists, missing per-torrent files and rotation

### Prompt 6: Statistics Tracking ❌ NOT STARTED
```
Create the statistics tracking system that:
1. Records success/failure counts
2. Tracks processed files
3. Maintains error type statistics
4. Implements atomic writes for stats updates
```

## Stage 4: Integration and Testing

### Prompt 7: CLI Implementation ⚠️ PARTIAL
```
Implement the command-line interface with:
1. All specified options
2. Help documentation
3. Version information
4. Input validation
```
**Status**: Basic CLI exists with some options, needs full feature set

### Prompt 8: qBittorrent Integration ⚠️ PARTIAL
```
Create documentation and examples for:
1. qBittorrent configuration
2. Command line usage
3. Common troubleshooting
4. Best practices
```
**Status**: Basic documentation in README, needs expansion

### Prompt 9: Testing Suite ⚠️ PARTIAL
```
Implement comprehensive tests:
1. Unit tests for each component
2. Integration tests
3. Security tests (zipbomb, corruption)
4. Performance tests
```
**Status**: Basic unit tests exist, needs comprehensive coverage

## Stage 5: Documentation and Deployment

### Prompt 10: Documentation ❌ NOT STARTED
```
Create comprehensive documentation:
1. Installation guide
2. Configuration reference
3. Troubleshooting guide
4. API documentation
```

### Prompt 11: Packaging ❌ NOT STARTED
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
- Follow git workflow for each prompt

## Expected Deliverables for Each Stage
1. Working code with tests
2. Documentation updates
3. Test coverage reports
4. Example outputs where applicable
5. Clean git history with meaningful commits

## Review Points
After each stage, verify:
1. Code quality and style
2. Test coverage
3. Documentation completeness
4. Error handling
5. Performance considerations
6. Git branch is clean and ready to merge

## Completion Tracking
- ✅ COMPLETED - Feature is fully implemented and tested
- 🚧 IN PROGRESS - Currently being worked on
- ⚠️ PARTIAL - Basic functionality exists but needs enhancement
- ❌ NOT STARTED - No implementation yet
