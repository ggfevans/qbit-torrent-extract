"""Archive extraction logic for qbit-torrent-extract."""

import logging
import os
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

import py7zr
import rarfile
from tqdm import tqdm

from .config import Config
from .validator import ArchiveValidator

logger = logging.getLogger("qbit_torrent_extract")

# Extensions for incomplete downloads - skip these
INCOMPLETE_EXTENSIONS = {'.!qb', '.part', '.crdownload', '.tmp'}


class ArchiveExtractor:
    """Extracts archives with nested archive support."""

    def __init__(
        self,
        preserve_archives: bool = True,
        config: Optional[Config] = None,
    ):
        """Initialize the archive extractor.

        Args:
            preserve_archives: If True, keep original archives after extraction
            config: Configuration object
        """
        self.config = config or Config()
        self.preserve_archives = preserve_archives
        self.validator = ArchiveValidator(config)
        self.extracted_archives: Set[Path] = set()

    def extract_all(self, directory: str) -> Dict[str, Any]:
        """Extract all supported archives in the given directory recursively.

        Args:
            directory: Path to directory containing archives

        Returns:
            Dictionary with extraction statistics
        """
        logger.info(f"Starting extraction in: {directory}")
        directory_path = Path(directory)

        stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
        }
        self.extracted_archives.clear()

        # Process archives with nested extraction support
        max_iterations = self.config.max_nested_depth + 1
        for iteration in range(max_iterations):
            archives = self._find_all_archives(directory_path)
            new_archives = [a for a in archives if a not in self.extracted_archives]

            if not new_archives:
                logger.info("No new archives found, extraction complete")
                break

            logger.info(f"Iteration {iteration + 1}: Found {len(new_archives)} archives")

            for archive_path in tqdm(new_archives, desc=f"Extracting", disable=not self.config.progress_indicators):
                result = self._extract_single_archive(archive_path)
                stats["total_processed"] += 1

                if result["success"]:
                    stats["successful"] += 1
                elif result["skipped"]:
                    stats["skipped"] += 1
                else:
                    stats["failed"] += 1
                    if result["error"]:
                        stats["errors"].append(f"{archive_path.name}: {result['error']}")

        logger.info(
            f"Extraction complete - Processed: {stats['total_processed']}, "
            f"Successful: {stats['successful']}, Failed: {stats['failed']}, "
            f"Skipped: {stats['skipped']}"
        )

        return stats

    def _find_all_archives(self, directory: Path) -> List[Path]:
        """Find all supported archive files in the directory."""
        archives = []
        for ext in self.validator.SUPPORTED_EXTENSIONS:
            # Handle compound extensions
            if ext == ".tar.gz":
                archives.extend(directory.rglob("*.tar.gz"))
            elif ext == ".tgz":
                archives.extend(directory.rglob("*.tgz"))
            else:
                archives.extend(directory.rglob(f"*{ext}"))

        # Filter out incomplete downloads
        filtered = []
        for archive in archives:
            if any(archive.name.endswith(inc) for inc in INCOMPLETE_EXTENSIONS):
                logger.debug(f"Skipping incomplete download: {archive}")
                continue
            filtered.append(archive)

        return sorted(set(filtered))

    def _extract_single_archive(self, archive_path: Path) -> Dict[str, Any]:
        """Extract a single archive with validation.

        Returns:
            Dict with keys: success, skipped, error
        """
        result = {"success": False, "skipped": False, "error": None}

        # Skip if already processed
        if archive_path in self.extracted_archives:
            result["skipped"] = True
            return result

        # Check if this is a non-first split archive part
        is_split, is_first = self.validator.is_split_archive_part(archive_path)
        if is_split and not is_first:
            logger.debug(f"Skipping split archive part: {archive_path.name}")
            self.extracted_archives.add(archive_path)
            result["skipped"] = True
            return result

        # Validate archive
        validation = self.validator.validate_archive(archive_path)
        if not validation.is_valid:
            logger.warning(f"Validation failed for {archive_path.name}: {validation.error_message}")
            self.extracted_archives.add(archive_path)
            result["error"] = validation.error_message
            return result

        # Check nested depth
        within_limit, depth = self.validator.check_nested_depth(archive_path)
        if not within_limit:
            msg = f"Exceeds max nested depth ({self.config.max_nested_depth})"
            logger.warning(f"{archive_path.name}: {msg}")
            self.extracted_archives.add(archive_path)
            result["error"] = msg
            return result

        # Extract based on type
        try:
            logger.info(f"Extracting {validation.archive_type}: {archive_path.name}")

            success = False
            if validation.archive_type == "zip":
                success = self._extract_zip(archive_path)
            elif validation.archive_type == "rar":
                success = self._extract_rar(archive_path)
            elif validation.archive_type == "7z":
                success = self._extract_7z(archive_path)
            elif validation.archive_type in ("tar", "tar.gz"):
                success = self._extract_tar(archive_path, validation.archive_type)

            self.extracted_archives.add(archive_path)

            if success:
                result["success"] = True
                if not self.preserve_archives:
                    os.remove(archive_path)
                    logger.info(f"Removed: {archive_path.name}")
            else:
                result["error"] = "Extraction failed"

        except Exception as e:
            logger.error(f"Error extracting {archive_path.name}: {e}")
            self.extracted_archives.add(archive_path)
            result["error"] = str(e)

        return result

    def _extract_zip(self, archive_path: Path) -> bool:
        """Extract a ZIP archive."""
        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(path=archive_path.parent)
            return True
        except zipfile.BadZipFile as e:
            logger.error(f"Invalid ZIP: {e}")
            return False
        except PermissionError as e:
            logger.error(f"Permission denied: {e}")
            return False

    def _extract_rar(self, archive_path: Path) -> bool:
        """Extract a RAR archive."""
        try:
            with rarfile.RarFile(archive_path, "r") as rf:
                if rf.needs_password():
                    logger.warning(f"Password-protected RAR: {archive_path.name}")
                    return False
                rf.extractall(path=archive_path.parent)
            return True
        except rarfile.BadRarFile as e:
            logger.error(f"Invalid RAR: {e}")
            return False
        except PermissionError as e:
            logger.error(f"Permission denied: {e}")
            return False

    def _extract_7z(self, archive_path: Path) -> bool:
        """Extract a 7z archive."""
        try:
            with py7zr.SevenZipFile(archive_path, "r") as szf:
                if szf.needs_password():
                    logger.warning(f"Password-protected 7z: {archive_path.name}")
                    return False
                szf.extractall(path=archive_path.parent)
            return True
        except py7zr.Bad7zFile as e:
            logger.error(f"Invalid 7z: {e}")
            return False
        except PermissionError as e:
            logger.error(f"Permission denied: {e}")
            return False

    def _extract_tar(self, archive_path: Path, archive_type: str) -> bool:
        """Extract a TAR archive with path traversal protection."""
        try:
            mode = "r:gz" if archive_type == "tar.gz" else "r"
            extract_path = archive_path.parent

            with tarfile.open(archive_path, mode) as tf:
                # Python 3.12+ has built-in protection
                if sys.version_info >= (3, 12):
                    tf.extractall(path=extract_path, filter='data')
                else:
                    # Manual path traversal check for older Python
                    for member in tf.getmembers():
                        member_path = extract_path / member.name
                        try:
                            member_path.resolve().relative_to(extract_path.resolve())
                        except ValueError:
                            logger.warning(f"Skipping suspicious path: {member.name}")
                            continue
                        tf.extract(member, path=extract_path)
            return True
        except tarfile.TarError as e:
            logger.error(f"Invalid TAR: {e}")
            return False
        except PermissionError as e:
            logger.error(f"Permission denied: {e}")
            return False

    def get_archive_files(self, directory: str) -> List[Path]:
        """Get all archive files in the directory."""
        return self._find_all_archives(Path(directory))
