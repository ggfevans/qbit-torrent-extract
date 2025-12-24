"""Archive validation and security checks."""

import re
import zipfile
import rarfile
import tarfile
import py7zr
from pathlib import Path
from typing import Optional, Tuple, List
import logging
from dataclasses import dataclass

from .config import Config


@dataclass
class ValidationResult:
    """Result of archive validation."""
    is_valid: bool
    archive_type: Optional[str] = None
    error_message: Optional[str] = None


class ArchiveValidator:
    """Validates archives for security and integrity."""

    SUPPORTED_EXTENSIONS = {
        ".zip": "zip",
        ".rar": "rar",
        ".7z": "7z",
        ".tar": "tar",
        ".tar.gz": "tar.gz",
        ".tgz": "tar.gz",
    }

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = logging.getLogger(__name__)

    def validate_archive(self, archive_path: Path) -> ValidationResult:
        """Validate an archive file."""
        if not archive_path.exists():
            return ValidationResult(False, error_message=f"Archive not found: {archive_path}")

        archive_type = self.detect_archive_type(archive_path)
        if not archive_type:
            return ValidationResult(False, error_message=f"Unsupported archive type: {archive_path.suffix}")

        try:
            # Get file sizes for ratio check
            total_size, compressed_size = self._get_archive_sizes(archive_path, archive_type)

            # Check extraction ratio (zipbomb protection)
            if compressed_size > 0:
                ratio = total_size / compressed_size
                if ratio > self.config.max_extraction_ratio:
                    return ValidationResult(
                        False,
                        archive_type=archive_type,
                        error_message=f"Extraction ratio {ratio:.1f} exceeds limit {self.config.max_extraction_ratio}"
                    )

            return ValidationResult(True, archive_type=archive_type)

        except (zipfile.BadZipFile, rarfile.BadRarFile, tarfile.TarError, py7zr.Bad7zFile) as e:
            return ValidationResult(False, archive_type=archive_type, error_message=f"Invalid {archive_type} file: {e}")
        except Exception as e:
            self.logger.error(f"Validation error for {archive_path}: {e}")
            return ValidationResult(False, archive_type=archive_type, error_message=str(e))

    def _get_archive_sizes(self, archive_path: Path, archive_type: str) -> Tuple[int, int]:
        """Get total uncompressed and compressed sizes. Returns (total, compressed)."""
        total_size = 0
        compressed_size = 0

        if archive_type == "zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                # Also check integrity
                if zf.testzip():
                    raise zipfile.BadZipFile("Corrupted archive")
                for info in zf.infolist():
                    total_size += info.file_size
                    compressed_size += info.compress_size

        elif archive_type == "rar":
            with rarfile.RarFile(archive_path, "r") as rf:
                if rf.needs_password():
                    raise rarfile.BadRarFile("Password protected archive")
                for info in rf.infolist():
                    total_size += info.file_size
                    compressed_size += info.compress_size

        elif archive_type in ("tar", "tar.gz"):
            mode = "r:gz" if archive_type == "tar.gz" else "r"
            with tarfile.open(archive_path, mode) as tf:
                for member in tf.getmembers():
                    if member.isfile():
                        total_size += member.size
            compressed_size = archive_path.stat().st_size

        elif archive_type == "7z":
            with py7zr.SevenZipFile(archive_path, "r") as szf:
                if szf.needs_password():
                    raise py7zr.Bad7zFile("Password protected archive")
                for info in szf.list():
                    total_size += info.uncompressed
                    compressed_size += info.compressed
                if compressed_size == 0:
                    compressed_size = archive_path.stat().st_size

        return total_size, compressed_size

    def detect_archive_type(self, archive_path: Path) -> Optional[str]:
        """Detect archive type from extension."""
        name_lower = archive_path.name.lower()
        if name_lower.endswith(".tar.gz") or name_lower.endswith(".tgz"):
            return "tar.gz"
        suffix = archive_path.suffix.lower()
        return self.SUPPORTED_EXTENSIONS.get(suffix)

    def is_split_archive_part(self, archive_path: Path) -> Tuple[bool, bool]:
        """Check if this is part of a split archive.

        Returns (is_split_part, is_first_part):
        - (False, True) = not split, safe to extract
        - (True, True) = split, first part, extract it
        - (True, False) = split, NOT first part, skip it
        """
        name = archive_path.name.lower()
        suffix = archive_path.suffix.lower()

        # .r00, .r01, etc - never first part
        if re.match(r'^\.r\d+$', suffix):
            return (True, False)

        # .part2.rar, .part3.rar - not first part
        match = re.match(r'.*\.part(\d+)\.rar$', name)
        if match:
            return (True, int(match.group(1)) == 1)

        # .rar with .r00 sibling = first part of old-style split
        if suffix == '.rar' and archive_path.with_suffix('.r00').exists():
            return (True, True)

        return (False, True)

    def check_nested_depth(self, archive_path: Path, current_depth: int = 0) -> Tuple[bool, int]:
        """Check if archive exceeds nested depth limit."""
        if current_depth >= self.config.max_nested_depth:
            return False, current_depth

        archive_type = self.detect_archive_type(archive_path)
        if not archive_type:
            return True, current_depth

        try:
            nested_archives = self._get_nested_archive_names(archive_path, archive_type)
            if nested_archives:
                depth = current_depth + 1
                if depth >= self.config.max_nested_depth:
                    return False, depth
                return True, depth
        except Exception as e:
            self.logger.warning(f"Error checking nested depth for {archive_path}: {e}")

        return True, current_depth

    def _get_nested_archive_names(self, archive_path: Path, archive_type: str) -> List[str]:
        """Get list of archive files contained within this archive."""
        nested = []

        if archive_type == "zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                nested = [n for n in zf.namelist() if self.detect_archive_type(Path(n))]

        elif archive_type == "rar":
            with rarfile.RarFile(archive_path, "r") as rf:
                nested = [n for n in rf.namelist() if self.detect_archive_type(Path(n))]

        elif archive_type in ("tar", "tar.gz"):
            mode = "r:gz" if archive_type == "tar.gz" else "r"
            with tarfile.open(archive_path, mode) as tf:
                nested = [m.name for m in tf.getmembers()
                         if m.isfile() and self.detect_archive_type(Path(m.name))]

        elif archive_type == "7z":
            with py7zr.SevenZipFile(archive_path, "r") as szf:
                nested = [n for n in szf.getnames() if self.detect_archive_type(Path(n))]

        return nested
