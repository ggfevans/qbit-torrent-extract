import logging
import os
import tarfile
import time
from pathlib import Path
from typing import Optional, List, Dict, Set, Tuple
import zipfile
import rarfile
import py7zr
from tqdm import tqdm
from .config import Config
from .validator import ArchiveValidator, ValidationResult
from .logger import get_logger, log_with_context
from .statistics import get_statistics_manager, categorize_error, ErrorType

class ArchiveExtractor:
    def __init__(self, preserve_archives: bool = True, log_level: int = logging.INFO, 
                 config: Optional[Config] = None, torrent_name: Optional[str] = None):
        """Initialize the archive extractor.
        
        Args:
            preserve_archives: If True, keep original archives after extraction
            log_level: Logging level to use (deprecated, use config.log_level)
            config: Configuration object
            torrent_name: Optional torrent name for per-torrent logging
        """
        self.config = config or Config()
        self.preserve_archives = preserve_archives
        self.torrent_name = torrent_name
        self.validator = ArchiveValidator(config)
        self.extracted_archives: Set[Path] = set()
        
        # Legacy stats for backward compatibility
        self.extraction_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        # Enhanced statistics tracking
        self.stats_manager = get_statistics_manager(config)
        self.current_run_id: Optional[str] = None
        
        # Use the new logging system
        self.logger = get_logger("extractor", torrent_name)


    def extract_all(self, directory: str) -> Dict[str, any]:
        """Extract all supported archives in the given directory recursively.
        
        Returns:
            Dictionary with extraction statistics
        """
        self.logger.info(f"Starting extraction in directory: {directory}")
        directory_path = Path(directory)
        
        # Start enhanced statistics tracking
        self.current_run_id = self.stats_manager.start_extraction_run(directory, self.torrent_name)
        
        # Reset legacy stats for this run
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
                
        # Finish enhanced statistics tracking
        run_stats = self.stats_manager.finish_extraction_run()
        
        self.logger.info(f"Extraction complete. Stats: {self.extraction_stats}")
        
        # Add enhanced stats to legacy stats for backward compatibility
        if run_stats:
            self.extraction_stats['run_id'] = run_stats.run_id
            self.extraction_stats['duration_seconds'] = run_stats.duration_seconds
            self.extraction_stats['archives_by_type'] = run_stats.archives_by_type
            self.extraction_stats['errors_by_type'] = run_stats.errors_by_type
        
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

    def _get_archive_size(self, archive_path: Path) -> int:
        """Get the size of an archive file in bytes."""
        try:
            return archive_path.stat().st_size
        except (OSError, AttributeError):
            return 0
    
    def _extract_single_archive(self, archive_path: Path) -> bool:
        """Extract a single archive with validation and error handling.
        
        Args:
            archive_path: Path to the archive to extract
            
        Returns:
            True if extraction was successful, False otherwise
        """
        self.extraction_stats['total_processed'] += 1
        archive_size = self._get_archive_size(archive_path)
        start_time = time.time()
        
        # Skip if already processed
        if archive_path in self.extracted_archives:
            self.logger.debug(f"Skipping already processed archive: {archive_path}")
            self.extraction_stats['skipped'] += 1
            self.stats_manager.record_archive_skipped(archive_path, "already_processed")
            return True
            
        # Validate archive before extraction
        log_with_context(logging.INFO, "Validating archive", 
                        torrent_name=self.torrent_name, archive_path=archive_path)
        validation = self.validator.validate_archive(archive_path)
        
        if not validation.is_valid:
            error_msg = f"Archive validation failed: {validation.error_message}"
            log_with_context(logging.WARNING, error_msg, 
                           torrent_name=self.torrent_name, archive_path=archive_path)
            self.extraction_stats['failed'] += 1
            self.extraction_stats['errors'].append(f"{archive_path}: {error_msg}")
            self.extracted_archives.add(archive_path)  # Mark as processed to avoid retry
            
            # Record detailed statistics
            extraction_time = time.time() - start_time
            error_type = categorize_error(validation.error_message or "validation_failed")
            self.stats_manager.record_archive_processed(
                archive_path=archive_path,
                archive_type=validation.archive_type or "unknown",
                success=False,
                size_bytes=archive_size,
                extraction_time=extraction_time,
                error_type=error_type,
                error_message=validation.error_message
            )
            return False
            
        # Check nested depth
        within_limit, depth = self.validator.check_nested_depth(archive_path)
        if not within_limit:
            error_msg = f"Archive exceeds maximum nested depth {self.config.max_nested_depth}"
            log_with_context(logging.WARNING, error_msg, 
                           torrent_name=self.torrent_name, archive_path=archive_path, depth=depth)
            self.extraction_stats['failed'] += 1
            self.extraction_stats['errors'].append(f"{archive_path}: {error_msg}")
            self.extracted_archives.add(archive_path)
            
            # Record detailed statistics
            extraction_time = time.time() - start_time
            self.stats_manager.record_archive_processed(
                archive_path=archive_path,
                archive_type=validation.archive_type,
                success=False,
                size_bytes=archive_size,
                extraction_time=extraction_time,
                error_type=ErrorType.NESTED_DEPTH_EXCEEDED,
                error_message=error_msg,
                nested_depth=depth
            )
            return False
            
        # Extract based on archive type
        try:
            log_with_context(logging.INFO, 
                           f"Extracting {validation.archive_type} archive (ratio: {validation.extraction_ratio:.1f})", 
                           torrent_name=self.torrent_name, archive_path=archive_path, 
                           archive_type=validation.archive_type, extraction_ratio=validation.extraction_ratio)
            
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
                
            # Record detailed statistics
            extraction_time = time.time() - start_time
            
            if success:
                self.extraction_stats['successful'] += 1
                self.extracted_archives.add(archive_path)
                
                # Record successful extraction
                self.stats_manager.record_archive_processed(
                    archive_path=archive_path,
                    archive_type=validation.archive_type,
                    success=True,
                    size_bytes=archive_size,
                    extracted_size_bytes=validation.total_size,
                    compression_ratio=validation.extraction_ratio,
                    extraction_time=extraction_time,
                    nested_depth=depth
                )
                
                # Remove original if requested
                if not self.preserve_archives:
                    os.remove(archive_path)
                    log_with_context(logging.INFO, "Removed original archive", 
                                   torrent_name=self.torrent_name, archive_path=archive_path)
            else:
                self.extraction_stats['failed'] += 1
                self.extracted_archives.add(archive_path)  # Mark as processed
                
                # Record failed extraction (specific error will be recorded in individual methods)
                self.stats_manager.record_archive_processed(
                    archive_path=archive_path,
                    archive_type=validation.archive_type,
                    success=False,
                    size_bytes=archive_size,
                    extraction_time=extraction_time,
                    error_type=ErrorType.EXTRACTION_ERROR,
                    error_message="Extraction method failed",
                    nested_depth=depth
                )
                
            return success
            
        except Exception as e:
            error_msg = f"Unexpected error extracting archive: {e}"
            log_with_context(logging.ERROR, error_msg, 
                           torrent_name=self.torrent_name, archive_path=archive_path, exception=str(e))
            self.extraction_stats['failed'] += 1
            self.extraction_stats['errors'].append(f"{archive_path}: {error_msg}")
            self.extracted_archives.add(archive_path)
            
            # Record detailed statistics
            extraction_time = time.time() - start_time
            error_type = categorize_error(str(e), type(e).__name__)
            self.stats_manager.record_archive_processed(
                archive_path=archive_path,
                archive_type=validation.archive_type if 'validation' in locals() else "unknown",
                success=False,
                size_bytes=archive_size,
                extraction_time=extraction_time,
                error_type=error_type,
                error_message=str(e),
                nested_depth=depth if 'depth' in locals() else 0
            )
            return False

    def _extract_zip(self, archive_path: Path) -> bool:
        """Extract a ZIP archive."""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(path=archive_path.parent)
            return True
        except zipfile.BadZipFile as e:
            log_with_context(logging.ERROR, f"Invalid ZIP file: {e}", 
                           torrent_name=self.torrent_name, archive_path=archive_path)
            return False
        except PermissionError as e:
            log_with_context(logging.ERROR, f"Permission denied extracting ZIP: {e}", 
                           torrent_name=self.torrent_name, archive_path=archive_path)
            return False
        except Exception as e:
            log_with_context(logging.ERROR, f"Error extracting ZIP: {e}", 
                           torrent_name=self.torrent_name, archive_path=archive_path)
            return False
            
    def _extract_rar(self, archive_path: Path) -> bool:
        """Extract a RAR archive."""
        try:
            with rarfile.RarFile(archive_path, 'r') as rf:
                if rf.needs_password():
                    log_with_context(logging.WARNING, "Skipping password-protected RAR", 
                                   torrent_name=self.torrent_name, archive_path=archive_path)
                    return False
                rf.extractall(path=archive_path.parent)
            return True
        except rarfile.BadRarFile as e:
            log_with_context(logging.ERROR, f"Invalid RAR file: {e}", 
                           torrent_name=self.torrent_name, archive_path=archive_path)
            return False
        except PermissionError as e:
            log_with_context(logging.ERROR, f"Permission denied extracting RAR: {e}", 
                           torrent_name=self.torrent_name, archive_path=archive_path)
            return False
        except Exception as e:
            log_with_context(logging.ERROR, f"Error extracting RAR: {e}", 
                           torrent_name=self.torrent_name, archive_path=archive_path)
            return False
            
    def _extract_7z(self, archive_path: Path) -> bool:
        """Extract a 7z archive."""
        try:
            with py7zr.SevenZipFile(archive_path, 'r') as szf:
                if szf.needs_password():
                    log_with_context(logging.WARNING, "Skipping password-protected 7z", 
                                   torrent_name=self.torrent_name, archive_path=archive_path)
                    return False
                szf.extractall(path=archive_path.parent)
            return True
        except py7zr.Bad7zFile as e:
            log_with_context(logging.ERROR, f"Invalid 7z file: {e}", 
                           torrent_name=self.torrent_name, archive_path=archive_path)
            return False
        except PermissionError as e:
            log_with_context(logging.ERROR, f"Permission denied extracting 7z: {e}", 
                           torrent_name=self.torrent_name, archive_path=archive_path)
            return False
        except Exception as e:
            log_with_context(logging.ERROR, f"Error extracting 7z: {e}", 
                           torrent_name=self.torrent_name, archive_path=archive_path)
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
            log_with_context(logging.ERROR, f"Invalid TAR file: {e}", 
                           torrent_name=self.torrent_name, archive_path=archive_path)
            return False
        except PermissionError as e:
            log_with_context(logging.ERROR, f"Permission denied extracting TAR: {e}", 
                           torrent_name=self.torrent_name, archive_path=archive_path)
            return False
        except Exception as e:
            log_with_context(logging.ERROR, f"Error extracting TAR: {e}", 
                           torrent_name=self.torrent_name, archive_path=archive_path)
            return False
            
    def get_archive_files(self, directory: str) -> List[Path]:
        """Get all archive files in the directory."""
        return self._find_all_archives(Path(directory))
        
    def get_extraction_stats(self) -> Dict[str, any]:
        """Get current extraction statistics."""
        return self.extraction_stats.copy()
    
    def get_enhanced_stats(self) -> Optional[Dict[str, any]]:
        """Get enhanced statistics from the current run.
        
        Returns:
            Enhanced statistics dictionary or None if no run is active
        """
        return self.stats_manager.get_current_run_stats()
    
    def get_aggregated_stats(self):
        """Get aggregated statistics across all runs."""
        return self.stats_manager.get_aggregated_stats()
    
    def get_recent_runs(self, limit: int = 10):
        """Get recent extraction runs."""
        return self.stats_manager.get_recent_runs(limit)

