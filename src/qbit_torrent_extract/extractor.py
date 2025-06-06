import logging
import os
import tarfile
from pathlib import Path
from typing import Optional, List, Dict, Set, Tuple
import zipfile
import rarfile
import py7zr
from tqdm import tqdm
from .config import Config
from .validator import ArchiveValidator, ValidationResult

class ArchiveExtractor:
    def __init__(self, preserve_archives: bool = True, log_level: int = logging.INFO, config: Optional[Config] = None):
        """Initialize the archive extractor.
        
        Args:
            preserve_archives: If True, keep original archives after extraction
            log_level: Logging level to use
            config: Configuration object
        """
        self.config = config or Config()
        self.preserve_archives = preserve_archives
        self.validator = ArchiveValidator(config)
        self.extracted_archives: Set[Path] = set()
        self.extraction_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        self._setup_logging(log_level)

    def _setup_logging(self, log_level: int) -> None:
        """Setup logging configuration."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def extract_all(self, directory: str) -> Dict[str, any]:
        """Extract all supported archives in the given directory recursively.
        
        Returns:
            Dictionary with extraction statistics
        """
        self.logger.info(f"Starting extraction in directory: {directory}")
        directory_path = Path(directory)
        
        # Reset stats for this run
        self.extraction_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        self.extracted_archives.clear()
        
        # Process archives with nested extraction support
        max_iterations = self.config.max_nested_depth + 1
        for iteration in range(max_iterations):
            self.logger.info(f"Extraction iteration {iteration + 1}/{max_iterations}")
            
            # Find all archives in current state
            archives = self._find_all_archives(directory_path)
            new_archives = [arch for arch in archives if arch not in self.extracted_archives]
            
            if not new_archives:
                self.logger.info("No new archives found, extraction complete")
                break
                
            self.logger.info(f"Found {len(new_archives)} new archives to process")
            
            # Process each archive
            for archive_path in tqdm(new_archives, desc=f"Iteration {iteration + 1}"):
                self._extract_single_archive(archive_path)
                
        self.logger.info(f"Extraction complete. Stats: {self.extraction_stats}")
        return self.extraction_stats

    def _find_all_archives(self, directory: Path) -> List[Path]:
        """Find all supported archive files in the directory."""
        archives = []
        for ext in self.validator.SUPPORTED_EXTENSIONS.keys():
            if ext in ['.tar.gz', '.tgz']:  # Handle compound extensions
                if ext == '.tar.gz':
                    archives.extend(directory.rglob("*.tar.gz"))
                else:  # .tgz
                    archives.extend(directory.rglob("*.tgz"))
            else:
                archives.extend(directory.rglob(f"*{ext}"))
        return sorted(set(archives))

    def _extract_single_archive(self, archive_path: Path) -> bool:
        """Extract a single archive with validation and error handling.
        
        Args:
            archive_path: Path to the archive to extract
            
        Returns:
            True if extraction was successful, False otherwise
        """
        self.extraction_stats['total_processed'] += 1
        
        # Skip if already processed
        if archive_path in self.extracted_archives:
            self.logger.debug(f"Skipping already processed archive: {archive_path}")
            self.extraction_stats['skipped'] += 1
            return True
            
        # Validate archive before extraction
        self.logger.info(f"Validating archive: {archive_path}")
        validation = self.validator.validate_archive(archive_path)
        
        if not validation.is_valid:
            error_msg = f"Archive validation failed for {archive_path}: {validation.error_message}"
            self.logger.warning(error_msg)
            self.extraction_stats['failed'] += 1
            self.extraction_stats['errors'].append(error_msg)
            self.extracted_archives.add(archive_path)  # Mark as processed to avoid retry
            return False
            
        # Check nested depth
        within_limit, depth = self.validator.check_nested_depth(archive_path)
        if not within_limit:
            error_msg = f"Archive {archive_path} exceeds maximum nested depth {self.config.max_nested_depth}"
            self.logger.warning(error_msg)
            self.extraction_stats['failed'] += 1
            self.extraction_stats['errors'].append(error_msg)
            self.extracted_archives.add(archive_path)
            return False
            
        # Extract based on archive type
        try:
            self.logger.info(f"Extracting {validation.archive_type} archive: {archive_path} (ratio: {validation.extraction_ratio:.1f})")
            
            success = False
            if validation.archive_type == 'zip':
                success = self._extract_zip(archive_path)
            elif validation.archive_type == 'rar':
                success = self._extract_rar(archive_path)
            elif validation.archive_type == '7z':
                success = self._extract_7z(archive_path)
            elif validation.archive_type in ('tar', 'tar.gz'):
                success = self._extract_tar(archive_path, validation.archive_type)
            else:
                error_msg = f"Extraction not implemented for {validation.archive_type}: {archive_path}"
                self.logger.error(error_msg)
                self.extraction_stats['errors'].append(error_msg)
                
            if success:
                self.extraction_stats['successful'] += 1
                self.extracted_archives.add(archive_path)
                
                # Remove original if requested
                if not self.preserve_archives:
                    os.remove(archive_path)
                    self.logger.info(f"Removed original archive: {archive_path}")
            else:
                self.extraction_stats['failed'] += 1
                self.extracted_archives.add(archive_path)  # Mark as processed
                
            return success
            
        except Exception as e:
            error_msg = f"Unexpected error extracting {archive_path}: {e}"
            self.logger.error(error_msg)
            self.extraction_stats['failed'] += 1
            self.extraction_stats['errors'].append(error_msg)
            self.extracted_archives.add(archive_path)
            return False

    def _extract_zip(self, archive_path: Path) -> bool:
        """Extract a ZIP archive."""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(path=archive_path.parent)
            return True
        except zipfile.BadZipFile as e:
            self.logger.error(f"Invalid ZIP file {archive_path}: {e}")
            return False
        except PermissionError as e:
            self.logger.error(f"Permission denied extracting {archive_path}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error extracting ZIP {archive_path}: {e}")
            return False
            
    def _extract_rar(self, archive_path: Path) -> bool:
        """Extract a RAR archive."""
        try:
            with rarfile.RarFile(archive_path, 'r') as rf:
                if rf.needs_password():
                    self.logger.warning(f"Skipping password-protected RAR: {archive_path}")
                    return False
                rf.extractall(path=archive_path.parent)
            return True
        except rarfile.BadRarFile as e:
            self.logger.error(f"Invalid RAR file {archive_path}: {e}")
            return False
        except PermissionError as e:
            self.logger.error(f"Permission denied extracting {archive_path}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error extracting RAR {archive_path}: {e}")
            return False
            
    def _extract_7z(self, archive_path: Path) -> bool:
        """Extract a 7z archive."""
        try:
            with py7zr.SevenZipFile(archive_path, 'r') as szf:
                if szf.needs_password():
                    self.logger.warning(f"Skipping password-protected 7z: {archive_path}")
                    return False
                szf.extractall(path=archive_path.parent)
            return True
        except py7zr.Bad7zFile as e:
            self.logger.error(f"Invalid 7z file {archive_path}: {e}")
            return False
        except PermissionError as e:
            self.logger.error(f"Permission denied extracting {archive_path}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error extracting 7z {archive_path}: {e}")
            return False
            
    def _extract_tar(self, archive_path: Path, archive_type: str) -> bool:
        """Extract a TAR archive (including .tar.gz)."""
        try:
            # Determine mode based on archive type
            mode = 'r:gz' if archive_type == 'tar.gz' else 'r'
            
            with tarfile.open(archive_path, mode) as tf:
                tf.extractall(path=archive_path.parent)
            return True
        except tarfile.TarError as e:
            self.logger.error(f"Invalid TAR file {archive_path}: {e}")
            return False
        except PermissionError as e:
            self.logger.error(f"Permission denied extracting {archive_path}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error extracting TAR {archive_path}: {e}")
            return False
            
    def get_archive_files(self, directory: str) -> List[Path]:
        """Get all archive files in the directory."""
        return self._find_all_archives(Path(directory))
        
    def get_extraction_stats(self) -> Dict[str, any]:
        """Get current extraction statistics."""
        return self.extraction_stats.copy()

