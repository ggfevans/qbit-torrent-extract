"""Archive validation and security checks."""

import os
import zipfile
import rarfile
import tarfile
import gzip
import py7zr
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import logging
from dataclasses import dataclass

from .config import Config


@dataclass
class ValidationResult:
    """Result of archive validation."""
    is_valid: bool
    archive_type: Optional[str] = None
    error_message: Optional[str] = None
    total_size: int = 0
    compressed_size: int = 0
    extraction_ratio: float = 0.0
    nested_depth: int = 0
    file_count: int = 0


class ArchiveValidator:
    """Validates archives for security and integrity."""
    
    SUPPORTED_EXTENSIONS = {
        '.zip': 'zip',
        '.rar': 'rar',
        '.7z': '7z',
        '.tar': 'tar',
        '.tar.gz': 'tar.gz',
        '.tgz': 'tar.gz',
        '.gz': 'gz'
    }
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize validator with configuration.
        
        Args:
            config: Configuration object with validation settings
        """
        self.config = config or Config()
        self.logger = logging.getLogger(__name__)
    
    def validate_archive(self, archive_path: Path) -> ValidationResult:
        """Validate an archive file.
        
        Args:
            archive_path: Path to the archive file
            
        Returns:
            ValidationResult with validation details
        """
        if not archive_path.exists():
            return ValidationResult(
                is_valid=False,
                error_message=f"Archive not found: {archive_path}"
            )
        
        # Detect archive type
        archive_type = self.detect_archive_type(archive_path)
        if not archive_type:
            return ValidationResult(
                is_valid=False,
                error_message=f"Unsupported archive type: {archive_path.suffix}"
            )
        
        # Validate based on type
        try:
            if archive_type == 'zip':
                return self._validate_zip(archive_path)
            elif archive_type == 'rar':
                return self._validate_rar(archive_path)
            elif archive_type in ('tar', 'tar.gz'):
                return self._validate_tar(archive_path)
            elif archive_type == '7z':
                return self._validate_7z(archive_path)
            else:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Validation not implemented for {archive_type}"
                )
        except Exception as e:
            self.logger.error(f"Validation error for {archive_path}: {e}")
            return ValidationResult(
                is_valid=False,
                archive_type=archive_type,
                error_message=str(e)
            )
    
    def detect_archive_type(self, archive_path: Path) -> Optional[str]:
        """Detect the type of archive from file extension.
        
        Args:
            archive_path: Path to the archive file
            
        Returns:
            Archive type string or None if unsupported
        """
        # Get the full file name in lowercase
        name_lower = archive_path.name.lower()
        
        # Check for compound extensions first
        if name_lower.endswith('.tar.gz') or name_lower.endswith('.tgz'):
            return 'tar.gz'
        
        # Check single extensions
        suffix = archive_path.suffix.lower()
        return self.SUPPORTED_EXTENSIONS.get(suffix)
    
    def _validate_zip(self, archive_path: Path) -> ValidationResult:
        """Validate a ZIP archive."""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                # Test archive integrity
                bad_file = zf.testzip()
                if bad_file:
                    return ValidationResult(
                        is_valid=False,
                        archive_type='zip',
                        error_message=f"Corrupted file in archive: {bad_file}"
                    )
                
                # Calculate sizes and check for zipbomb
                total_size = 0
                compressed_size = 0
                file_count = 0
                
                for info in zf.infolist():
                    total_size += info.file_size
                    compressed_size += info.compress_size
                    file_count += 1
                
                # Calculate extraction ratio
                extraction_ratio = total_size / compressed_size if compressed_size > 0 else 1.0
                
                # Check against limits
                if extraction_ratio > self.config.max_extraction_ratio:
                    return ValidationResult(
                        is_valid=False,
                        archive_type='zip',
                        error_message=f"Extraction ratio {extraction_ratio:.1f} exceeds limit {self.config.max_extraction_ratio}",
                        total_size=total_size,
                        compressed_size=compressed_size,
                        extraction_ratio=extraction_ratio,
                        file_count=file_count
                    )
                
                return ValidationResult(
                    is_valid=True,
                    archive_type='zip',
                    total_size=total_size,
                    compressed_size=compressed_size,
                    extraction_ratio=extraction_ratio,
                    file_count=file_count
                )
                
        except zipfile.BadZipFile as e:
            return ValidationResult(
                is_valid=False,
                archive_type='zip',
                error_message=f"Invalid ZIP file: {e}"
            )
    
    def _validate_rar(self, archive_path: Path) -> ValidationResult:
        """Validate a RAR archive."""
        try:
            with rarfile.RarFile(archive_path, 'r') as rf:
                # Test archive integrity
                if rf.needs_password():
                    return ValidationResult(
                        is_valid=False,
                        archive_type='rar',
                        error_message="Password protected archive"
                    )
                
                # Calculate sizes
                total_size = 0
                compressed_size = 0
                file_count = 0
                
                for info in rf.infolist():
                    total_size += info.file_size
                    compressed_size += info.compress_size
                    file_count += 1
                
                # Calculate extraction ratio
                extraction_ratio = total_size / compressed_size if compressed_size > 0 else 1.0
                
                # Check against limits
                if extraction_ratio > self.config.max_extraction_ratio:
                    return ValidationResult(
                        is_valid=False,
                        archive_type='rar',
                        error_message=f"Extraction ratio {extraction_ratio:.1f} exceeds limit {self.config.max_extraction_ratio}",
                        total_size=total_size,
                        compressed_size=compressed_size,
                        extraction_ratio=extraction_ratio,
                        file_count=file_count
                    )
                
                return ValidationResult(
                    is_valid=True,
                    archive_type='rar',
                    total_size=total_size,
                    compressed_size=compressed_size,
                    extraction_ratio=extraction_ratio,
                    file_count=file_count
                )
                
        except rarfile.BadRarFile as e:
            return ValidationResult(
                is_valid=False,
                archive_type='rar',
                error_message=f"Invalid RAR file: {e}"
            )
    
    def _validate_tar(self, archive_path: Path) -> ValidationResult:
        """Validate a TAR archive (including .tar.gz)."""
        try:
            # Determine mode based on extension
            mode = 'r:gz' if archive_path.suffix in ('.gz', '.tgz') else 'r'
            
            with tarfile.open(archive_path, mode) as tf:
                # Calculate sizes
                total_size = 0
                file_count = 0
                
                for member in tf.getmembers():
                    if member.isfile():
                        total_size += member.size
                        file_count += 1
                
                # For tar files, we can't easily get compressed size
                compressed_size = archive_path.stat().st_size
                extraction_ratio = total_size / compressed_size if compressed_size > 0 else 1.0
                
                # Check against limits
                if extraction_ratio > self.config.max_extraction_ratio:
                    return ValidationResult(
                        is_valid=False,
                        archive_type='tar.gz' if mode == 'r:gz' else 'tar',
                        error_message=f"Extraction ratio {extraction_ratio:.1f} exceeds limit {self.config.max_extraction_ratio}",
                        total_size=total_size,
                        compressed_size=compressed_size,
                        extraction_ratio=extraction_ratio,
                        file_count=file_count
                    )
                
                return ValidationResult(
                    is_valid=True,
                    archive_type='tar.gz' if mode == 'r:gz' else 'tar',
                    total_size=total_size,
                    compressed_size=compressed_size,
                    extraction_ratio=extraction_ratio,
                    file_count=file_count
                )
                
        except tarfile.TarError as e:
            return ValidationResult(
                is_valid=False,
                archive_type='tar',
                error_message=f"Invalid TAR file: {e}"
            )
    
    def _validate_7z(self, archive_path: Path) -> ValidationResult:
        """Validate a 7z archive."""
        try:
            with py7zr.SevenZipFile(archive_path, 'r') as szf:
                # Test archive integrity
                if szf.needs_password():
                    return ValidationResult(
                        is_valid=False,
                        archive_type='7z',
                        error_message="Password protected archive"
                    )
                
                # Get archive info
                total_size = 0
                compressed_size = 0
                file_count = 0
                
                # Get list of files and their info
                names = szf.getnames()
                file_count = len(names)
                
                # For 7z, we need to check the archive info differently
                for name, info in szf.list():
                    total_size += info.uncompressed
                    compressed_size += info.compressed
                
                # If we couldn't get sizes from list, estimate from file size
                if compressed_size == 0:
                    compressed_size = archive_path.stat().st_size
                
                # Calculate extraction ratio
                extraction_ratio = total_size / compressed_size if compressed_size > 0 else 1.0
                
                # Check against limits
                if extraction_ratio > self.config.max_extraction_ratio:
                    return ValidationResult(
                        is_valid=False,
                        archive_type='7z',
                        error_message=f"Extraction ratio {extraction_ratio:.1f} exceeds limit {self.config.max_extraction_ratio}",
                        total_size=total_size,
                        compressed_size=compressed_size,
                        extraction_ratio=extraction_ratio,
                        file_count=file_count
                    )
                
                return ValidationResult(
                    is_valid=True,
                    archive_type='7z',
                    total_size=total_size,
                    compressed_size=compressed_size,
                    extraction_ratio=extraction_ratio,
                    file_count=file_count
                )
                
        except py7zr.Bad7zFile as e:
            return ValidationResult(
                is_valid=False,
                archive_type='7z',
                error_message=f"Invalid 7z file: {e}"
            )
    
    def check_nested_depth(self, archive_path: Path, current_depth: int = 0) -> Tuple[bool, int]:
        """Check if archive contains nested archives within depth limit.
        
        Args:
            archive_path: Path to the archive
            current_depth: Current nesting depth
            
        Returns:
            Tuple of (within_limit, max_depth_found)
        """
        if current_depth >= self.config.max_nested_depth:
            return False, current_depth
        
        archive_type = self.detect_archive_type(archive_path)
        if not archive_type:
            return True, current_depth
        
        max_depth = current_depth
        
        try:
            # Check for nested archives based on type
            if archive_type == 'zip':
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    for name in zf.namelist():
                        if self.detect_archive_type(Path(name)):
                            # Found nested archive
                            max_depth = max(max_depth, current_depth + 1)
                            if max_depth >= self.config.max_nested_depth:
                                return False, max_depth
            
            elif archive_type == 'rar':
                with rarfile.RarFile(archive_path, 'r') as rf:
                    for name in rf.namelist():
                        if self.detect_archive_type(Path(name)):
                            max_depth = max(max_depth, current_depth + 1)
                            if max_depth >= self.config.max_nested_depth:
                                return False, max_depth
            
            elif archive_type in ('tar', 'tar.gz'):
                mode = 'r:gz' if archive_type == 'tar.gz' else 'r'
                with tarfile.open(archive_path, mode) as tf:
                    for member in tf.getmembers():
                        if member.isfile() and self.detect_archive_type(Path(member.name)):
                            max_depth = max(max_depth, current_depth + 1)
                            if max_depth >= self.config.max_nested_depth:
                                return False, max_depth
            
            elif archive_type == '7z':
                with py7zr.SevenZipFile(archive_path, 'r') as szf:
                    for name in szf.getnames():
                        if self.detect_archive_type(Path(name)):
                            max_depth = max(max_depth, current_depth + 1)
                            if max_depth >= self.config.max_nested_depth:
                                return False, max_depth
            
        except Exception as e:
            self.logger.warning(f"Error checking nested depth for {archive_path}: {e}")
        
        return True, max_depth
    
    def scan_directory(self, directory: Path) -> Dict[Path, ValidationResult]:
        """Scan directory for archives and validate them.
        
        Args:
            directory: Directory to scan
            
        Returns:
            Dictionary mapping archive paths to validation results
        """
        results = {}
        
        for ext, archive_type in self.SUPPORTED_EXTENSIONS.items():
            pattern = f"**/*{ext}"
            for archive_path in directory.glob(pattern):
                if archive_path not in results:  # Avoid duplicate checks
                    self.logger.info(f"Validating {archive_path}")
                    results[archive_path] = self.validate_archive(archive_path)
        
        return results