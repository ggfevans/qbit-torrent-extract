"""Comprehensive statistics tracking system for archive extraction operations."""

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import tempfile
import shutil

from .config import Config
from .logger import get_logger


class ErrorType(Enum):
    """Categories of extraction errors."""

    VALIDATION_ERROR = "validation_error"
    EXTRACTION_ERROR = "extraction_error"
    PERMISSION_ERROR = "permission_error"
    CORRUPTION_ERROR = "corruption_error"
    PASSWORD_PROTECTED = "password_protected"
    ZIPBOMB_PROTECTION = "zipbomb_protection"
    NESTED_DEPTH_EXCEEDED = "nested_depth_exceeded"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ArchiveStats:
    """Statistics for a single archive."""

    path: str
    type: str
    size_bytes: int = 0
    extracted_size_bytes: int = 0
    compression_ratio: float = 0.0
    extraction_time_seconds: float = 0.0
    success: bool = False
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    nested_depth: int = 0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class ExtractionRunStats:
    """Statistics for a complete extraction run."""

    run_id: str
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: float = 0.0
    directory: str = ""
    torrent_name: Optional[str] = None

    # Aggregate counts
    total_processed: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0

    # Detailed breakdowns
    archives_by_type: Dict[str, int] = field(default_factory=dict)
    errors_by_type: Dict[str, int] = field(default_factory=dict)

    # Size statistics
    total_archive_size_bytes: int = 0
    total_extracted_size_bytes: int = 0
    average_compression_ratio: float = 0.0

    # Performance metrics
    archives_per_second: float = 0.0
    bytes_per_second: float = 0.0

    # Individual archive details
    archives: List[ArchiveStats] = field(default_factory=list)

    # Additional context
    config_snapshot: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedStats:
    """Aggregated statistics across multiple runs."""

    total_runs: int = 0
    first_run_time: Optional[str] = None
    last_run_time: Optional[str] = None

    # Lifetime totals
    lifetime_archives_processed: int = 0
    lifetime_successful: int = 0
    lifetime_failed: int = 0
    lifetime_skipped: int = 0

    # Lifetime size statistics
    lifetime_archive_size_bytes: int = 0
    lifetime_extracted_size_bytes: int = 0

    # Archive type breakdown
    lifetime_archives_by_type: Dict[str, int] = field(default_factory=dict)
    lifetime_errors_by_type: Dict[str, int] = field(default_factory=dict)

    # Performance averages
    average_archives_per_run: float = 0.0
    average_run_duration_seconds: float = 0.0
    average_archives_per_second: float = 0.0

    # Top statistics
    most_common_archive_type: Optional[str] = None
    most_common_error_type: Optional[str] = None
    largest_archive_processed_bytes: int = 0
    fastest_extraction_seconds: float = float("inf")

    # Recent statistics (last 30 days)
    recent_runs: int = 0
    recent_archives_processed: int = 0
    recent_success_rate: float = 0.0


class StatisticsManager:
    """Manages comprehensive statistics tracking for archive extraction."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the statistics manager.

        Args:
            config: Configuration object with statistics settings
        """
        self.config = config or Config()
        self.logger = get_logger("statistics")
        self.lock = threading.Lock()

        # Current run statistics
        self.current_run: Optional[ExtractionRunStats] = None

        # Initialize statistics file path
        self.stats_file = self._get_stats_file_path()
        self._ensure_stats_file_exists()

    def _get_stats_file_path(self) -> Path:
        """Get the path to the statistics file."""
        if self.config.stats_file:
            return Path(self.config.stats_file).expanduser()

        # Default to log directory if available, otherwise user's home
        if self.config.log_dir:
            stats_dir = Path(self.config.log_dir).expanduser()
        else:
            stats_dir = Path.home() / ".qbit-torrent-extract"

        stats_dir.mkdir(parents=True, exist_ok=True)
        return stats_dir / "extraction_statistics.json"

    def _ensure_stats_file_exists(self):
        """Ensure the statistics file exists with proper structure."""
        if not self.stats_file.exists():
            initial_data = {
                "version": "1.0",
                "created": datetime.now(timezone.utc).isoformat(),
                "aggregated_stats": asdict(AggregatedStats()),
                "recent_runs": [],
            }
            self._write_stats_file(initial_data)
            self.logger.info(f"Created statistics file: {self.stats_file}")

    def _read_stats_file(self) -> Dict[str, Any]:
        """Read statistics from file with error handling."""
        try:
            with open(self.stats_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
            self.logger.warning(f"Error reading statistics file: {e}")
            # Return default structure
            return {
                "version": "1.0",
                "created": datetime.now(timezone.utc).isoformat(),
                "aggregated_stats": asdict(AggregatedStats()),
                "recent_runs": [],
            }

    def _write_stats_file(self, data: Dict[str, Any]):
        """Write statistics to file atomically."""
        try:
            # Use atomic write to prevent corruption
            temp_file = self.stats_file.with_suffix(".tmp")

            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            shutil.move(str(temp_file), str(self.stats_file))

        except Exception as e:
            self.logger.error(f"Error writing statistics file: {e}")
            # Clean up temp file if it exists
            if temp_file.exists():
                temp_file.unlink()
            raise

    def start_extraction_run(
        self, directory: str, torrent_name: Optional[str] = None
    ) -> str:
        """Start tracking a new extraction run.

        Args:
            directory: Directory being processed
            torrent_name: Optional torrent name

        Returns:
            Unique run ID for this extraction
        """
        with self.lock:
            run_id = f"run_{int(time.time() * 1000)}"
            start_time = datetime.now(timezone.utc).isoformat()

            self.current_run = ExtractionRunStats(
                run_id=run_id,
                start_time=start_time,
                directory=directory,
                torrent_name=torrent_name,
                config_snapshot=self._create_config_snapshot(),
            )

            self.logger.info(
                f"Started extraction run {run_id} for directory: {directory}"
            )
            if torrent_name:
                self.logger.info(f"Run {run_id} torrent: {torrent_name}")

            return run_id

    def _create_config_snapshot(self) -> Dict[str, Any]:
        """Create a snapshot of relevant configuration for this run."""
        return {
            "max_extraction_ratio": self.config.max_extraction_ratio,
            "max_nested_depth": self.config.max_nested_depth,
            "preserve_originals": self.config.preserve_originals,
            "log_level": self.config.log_level,
        }

    def record_archive_processed(
        self,
        archive_path: Path,
        archive_type: str,
        success: bool,
        size_bytes: int = 0,
        extracted_size_bytes: int = 0,
        compression_ratio: float = 0.0,
        extraction_time: float = 0.0,
        error_type: Optional[ErrorType] = None,
        error_message: Optional[str] = None,
        nested_depth: int = 0,
    ):
        """Record statistics for a processed archive.

        Args:
            archive_path: Path to the archive
            archive_type: Type of archive (zip, rar, 7z, etc.)
            success: Whether extraction was successful
            size_bytes: Original archive size in bytes
            extracted_size_bytes: Size of extracted content in bytes
            compression_ratio: Compression ratio
            extraction_time: Time taken for extraction in seconds
            error_type: Type of error if extraction failed
            error_message: Detailed error message
            nested_depth: Nesting depth of the archive
        """
        if not self.current_run:
            self.logger.warning("No active extraction run to record archive statistics")
            return

        with self.lock:
            archive_stats = ArchiveStats(
                path=str(archive_path),
                type=archive_type,
                size_bytes=size_bytes,
                extracted_size_bytes=extracted_size_bytes,
                compression_ratio=compression_ratio,
                extraction_time_seconds=extraction_time,
                success=success,
                error_type=error_type.value if error_type else None,
                error_message=error_message,
                nested_depth=nested_depth,
            )

            self.current_run.archives.append(archive_stats)
            self.current_run.total_processed += 1

            if success:
                self.current_run.successful += 1
            else:
                self.current_run.failed += 1

            # Update type breakdown
            if archive_type in self.current_run.archives_by_type:
                self.current_run.archives_by_type[archive_type] += 1
            else:
                self.current_run.archives_by_type[archive_type] = 1

            # Update error breakdown
            if error_type:
                error_key = error_type.value
                if error_key in self.current_run.errors_by_type:
                    self.current_run.errors_by_type[error_key] += 1
                else:
                    self.current_run.errors_by_type[error_key] = 1

            # Update size statistics
            self.current_run.total_archive_size_bytes += size_bytes
            self.current_run.total_extracted_size_bytes += extracted_size_bytes

    def record_archive_skipped(
        self, archive_path: Path, reason: str = "already_processed"
    ):
        """Record a skipped archive.

        Args:
            archive_path: Path to the skipped archive
            reason: Reason for skipping
        """
        if not self.current_run:
            return

        with self.lock:
            self.current_run.total_processed += 1
            self.current_run.skipped += 1

            self.logger.debug(f"Skipped archive {archive_path}: {reason}")

    def finish_extraction_run(self) -> Optional[ExtractionRunStats]:
        """Finish the current extraction run and save statistics.

        Returns:
            The completed run statistics, or None if no run was active
        """
        if not self.current_run:
            self.logger.warning("No active extraction run to finish")
            return None

        with self.lock:
            # Finalize run statistics
            end_time = datetime.now(timezone.utc)
            self.current_run.end_time = end_time.isoformat()

            start_dt = datetime.fromisoformat(
                self.current_run.start_time.replace("Z", "+00:00")
            )
            self.current_run.duration_seconds = (end_time - start_dt).total_seconds()

            # Calculate performance metrics
            if self.current_run.duration_seconds > 0:
                self.current_run.archives_per_second = (
                    self.current_run.total_processed / self.current_run.duration_seconds
                )
                self.current_run.bytes_per_second = (
                    self.current_run.total_archive_size_bytes
                    / self.current_run.duration_seconds
                )

            # Calculate average compression ratio
            if self.current_run.successful > 0:
                total_ratio = sum(
                    archive.compression_ratio
                    for archive in self.current_run.archives
                    if archive.success and archive.compression_ratio > 0
                )
                self.current_run.average_compression_ratio = (
                    total_ratio / self.current_run.successful
                )

            # Save to persistent storage
            completed_run = self.current_run
            self._save_run_statistics(completed_run)

            # Clear current run
            self.current_run = None

            self.logger.info(
                f"Completed extraction run {completed_run.run_id} - "
                f"Processed: {completed_run.total_processed}, "
                f"Successful: {completed_run.successful}, "
                f"Failed: {completed_run.failed}, "
                f"Duration: {completed_run.duration_seconds:.1f}s"
            )

            return completed_run

    def _save_run_statistics(self, run_stats: ExtractionRunStats):
        """Save run statistics to persistent storage."""
        try:
            data = self._read_stats_file()

            # Add new run to recent runs
            if "recent_runs" not in data:
                data["recent_runs"] = []

            data["recent_runs"].append(asdict(run_stats))

            # Keep only the last 100 runs to prevent unbounded growth
            data["recent_runs"] = data["recent_runs"][-100:]

            # Update aggregated statistics
            data["aggregated_stats"] = asdict(
                self._update_aggregated_stats(
                    AggregatedStats(**data.get("aggregated_stats", {})), run_stats
                )
            )

            # Update last modified time
            data["last_updated"] = datetime.now(timezone.utc).isoformat()

            self._write_stats_file(data)

        except Exception as e:
            self.logger.error(f"Failed to save run statistics: {e}")

    def _update_aggregated_stats(
        self, aggregated: AggregatedStats, new_run: ExtractionRunStats
    ) -> AggregatedStats:
        """Update aggregated statistics with a new run."""
        aggregated.total_runs += 1

        # Update time tracking
        if aggregated.first_run_time is None:
            aggregated.first_run_time = new_run.start_time
        aggregated.last_run_time = new_run.start_time

        # Update lifetime totals
        aggregated.lifetime_archives_processed += new_run.total_processed
        aggregated.lifetime_successful += new_run.successful
        aggregated.lifetime_failed += new_run.failed
        aggregated.lifetime_skipped += new_run.skipped

        # Update size statistics
        aggregated.lifetime_archive_size_bytes += new_run.total_archive_size_bytes
        aggregated.lifetime_extracted_size_bytes += new_run.total_extracted_size_bytes

        # Update type breakdowns
        for archive_type, count in new_run.archives_by_type.items():
            if archive_type in aggregated.lifetime_archives_by_type:
                aggregated.lifetime_archives_by_type[archive_type] += count
            else:
                aggregated.lifetime_archives_by_type[archive_type] = count

        for error_type, count in new_run.errors_by_type.items():
            if error_type in aggregated.lifetime_errors_by_type:
                aggregated.lifetime_errors_by_type[error_type] += count
            else:
                aggregated.lifetime_errors_by_type[error_type] = count

        # Update averages
        if aggregated.total_runs > 0:
            aggregated.average_archives_per_run = (
                aggregated.lifetime_archives_processed / aggregated.total_runs
            )

        # Update most common types
        if aggregated.lifetime_archives_by_type:
            aggregated.most_common_archive_type = max(
                aggregated.lifetime_archives_by_type.items(), key=lambda x: x[1]
            )[0]

        if aggregated.lifetime_errors_by_type:
            aggregated.most_common_error_type = max(
                aggregated.lifetime_errors_by_type.items(), key=lambda x: x[1]
            )[0]

        # Update performance metrics
        if new_run.duration_seconds > 0:
            if aggregated.fastest_extraction_seconds == float("inf"):
                aggregated.fastest_extraction_seconds = new_run.duration_seconds
            else:
                aggregated.fastest_extraction_seconds = min(
                    aggregated.fastest_extraction_seconds, new_run.duration_seconds
                )

        # Update largest archive
        for archive in new_run.archives:
            aggregated.largest_archive_processed_bytes = max(
                aggregated.largest_archive_processed_bytes, archive.size_bytes
            )

        return aggregated

    def get_current_run_stats(self) -> Optional[Dict[str, Any]]:
        """Get statistics for the current run.

        Returns:
            Current run statistics or None if no run is active
        """
        if not self.current_run:
            return None

        with self.lock:
            return asdict(self.current_run)

    def get_aggregated_stats(self) -> AggregatedStats:
        """Get aggregated statistics across all runs.

        Returns:
            Aggregated statistics object
        """
        try:
            data = self._read_stats_file()
            return AggregatedStats(**data.get("aggregated_stats", {}))
        except Exception as e:
            self.logger.error(f"Error reading aggregated statistics: {e}")
            return AggregatedStats()

    def get_recent_runs(self, limit: int = 10) -> List[ExtractionRunStats]:
        """Get recent extraction runs.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of recent run statistics
        """
        try:
            data = self._read_stats_file()
            recent_runs_data = data.get("recent_runs", [])

            # Convert to objects and return most recent first
            runs = [
                ExtractionRunStats(**run_data) for run_data in recent_runs_data[-limit:]
            ]
            return list(reversed(runs))

        except Exception as e:
            self.logger.error(f"Error reading recent runs: {e}")
            return []

    def export_statistics(self, export_path: Optional[Path] = None) -> Path:
        """Export all statistics to a file.

        Args:
            export_path: Optional path for export file

        Returns:
            Path to the exported file
        """
        if export_path is None:
            export_path = (
                Path.cwd() / f"extraction_stats_export_{int(time.time())}.json"
            )

        try:
            data = self._read_stats_file()

            # Add export metadata
            data["export_info"] = {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "exported_by": "qbit-torrent-extract",
                "stats_file_path": str(self.stats_file),
            }

            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Statistics exported to: {export_path}")
            return export_path

        except Exception as e:
            self.logger.error(f"Error exporting statistics: {e}")
            raise

    def clear_statistics(self, keep_aggregated: bool = True):
        """Clear stored statistics.

        Args:
            keep_aggregated: Whether to keep aggregated statistics
        """
        try:
            if keep_aggregated:
                data = self._read_stats_file()
                data["recent_runs"] = []
                data["cleared_at"] = datetime.now(timezone.utc).isoformat()
            else:
                data = {
                    "version": "1.0",
                    "created": datetime.now(timezone.utc).isoformat(),
                    "aggregated_stats": asdict(AggregatedStats()),
                    "recent_runs": [],
                }

            self._write_stats_file(data)
            self.logger.info("Statistics cleared")

        except Exception as e:
            self.logger.error(f"Error clearing statistics: {e}")
            raise


# Global statistics manager instance
_statistics_manager: Optional[StatisticsManager] = None


def get_statistics_manager(config: Optional[Config] = None) -> StatisticsManager:
    """Get the global statistics manager instance.

    Args:
        config: Configuration object

    Returns:
        Statistics manager instance
    """
    global _statistics_manager

    if _statistics_manager is None:
        _statistics_manager = StatisticsManager(config)

    return _statistics_manager


def categorize_error(
    error_message: str, exception_type: Optional[str] = None
) -> ErrorType:
    """Categorize an error based on its message and type.

    Args:
        error_message: The error message
        exception_type: The exception type name if available

    Returns:
        Categorized error type
    """
    error_lower = error_message.lower()

    if "validation" in error_lower or "invalid" in error_lower:
        return ErrorType.VALIDATION_ERROR
    elif "password" in error_lower or "encrypted" in error_lower:
        return ErrorType.PASSWORD_PROTECTED
    elif "permission" in error_lower or "access" in error_lower:
        return ErrorType.PERMISSION_ERROR
    elif "corrupted" in error_lower or "corrupt" in error_lower:
        return ErrorType.CORRUPTION_ERROR
    elif "ratio" in error_lower or "zipbomb" in error_lower:
        return ErrorType.ZIPBOMB_PROTECTION
    elif "depth" in error_lower or "nested" in error_lower:
        return ErrorType.NESTED_DEPTH_EXCEEDED
    elif "extract" in error_lower:
        return ErrorType.EXTRACTION_ERROR
    else:
        return ErrorType.UNKNOWN_ERROR
