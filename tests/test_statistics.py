"""Tests for the statistics tracking system."""

import json
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from qbit_torrent_extract.config import Config
from qbit_torrent_extract.statistics import (
    StatisticsManager,
    ArchiveStats,
    ExtractionRunStats,
    AggregatedStats,
    ErrorType,
    categorize_error,
    get_statistics_manager,
)


@pytest.fixture
def temp_stats_file():
    """Create a temporary statistics file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)

    # Clean up the file (it was created empty)
    temp_path.unlink()

    yield temp_path
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def config_with_stats_file(temp_stats_file):
    """Create a config with a temporary stats file."""
    return Config(stats_file=str(temp_stats_file))


@pytest.fixture
def stats_manager(config_with_stats_file):
    """Create a statistics manager with temporary file."""
    return StatisticsManager(config_with_stats_file)


class TestErrorCategorization:
    """Test error categorization functionality."""

    def test_validation_errors(self):
        """Test validation error categorization."""
        assert (
            categorize_error("Archive validation failed") == ErrorType.VALIDATION_ERROR
        )
        assert categorize_error("Invalid ZIP file") == ErrorType.VALIDATION_ERROR
        assert categorize_error("Archive is invalid") == ErrorType.VALIDATION_ERROR

    def test_password_errors(self):
        """Test password-protected error categorization."""
        assert categorize_error("Password required") == ErrorType.PASSWORD_PROTECTED
        assert categorize_error("Archive is encrypted") == ErrorType.PASSWORD_PROTECTED
        assert categorize_error("password protected") == ErrorType.PASSWORD_PROTECTED

    def test_permission_errors(self):
        """Test permission error categorization."""
        assert categorize_error("Permission denied") == ErrorType.PERMISSION_ERROR
        assert categorize_error("Access is denied") == ErrorType.PERMISSION_ERROR
        assert (
            categorize_error("Insufficient permissions") == ErrorType.PERMISSION_ERROR
        )

    def test_corruption_errors(self):
        """Test corruption error categorization."""
        assert categorize_error("Archive is corrupted") == ErrorType.CORRUPTION_ERROR
        assert categorize_error("File corrupt") == ErrorType.CORRUPTION_ERROR
        assert (
            categorize_error("Data corruption detected") == ErrorType.CORRUPTION_ERROR
        )

    def test_zipbomb_errors(self):
        """Test zipbomb protection error categorization."""
        assert (
            categorize_error("Extraction ratio exceeded")
            == ErrorType.ZIPBOMB_PROTECTION
        )
        assert (
            categorize_error("Potential zipbomb detected")
            == ErrorType.ZIPBOMB_PROTECTION
        )
        assert categorize_error("Size ratio too high") == ErrorType.ZIPBOMB_PROTECTION

    def test_depth_errors(self):
        """Test nested depth error categorization."""
        assert (
            categorize_error("Maximum nested depth exceeded")
            == ErrorType.NESTED_DEPTH_EXCEEDED
        )
        assert (
            categorize_error("Archive depth limit reached")
            == ErrorType.NESTED_DEPTH_EXCEEDED
        )
        assert (
            categorize_error("Too many nested levels")
            == ErrorType.NESTED_DEPTH_EXCEEDED
        )

    def test_extraction_errors(self):
        """Test extraction error categorization."""
        assert (
            categorize_error("Failed to extract archive") == ErrorType.EXTRACTION_ERROR
        )
        assert (
            categorize_error("Extraction process failed") == ErrorType.EXTRACTION_ERROR
        )
        assert categorize_error("Cannot extract files") == ErrorType.EXTRACTION_ERROR

    def test_unknown_errors(self):
        """Test unknown error categorization."""
        assert categorize_error("Random error message") == ErrorType.UNKNOWN_ERROR
        assert categorize_error("Unexpected failure") == ErrorType.UNKNOWN_ERROR
        assert categorize_error("") == ErrorType.UNKNOWN_ERROR


class TestArchiveStats:
    """Test ArchiveStats dataclass."""

    def test_archive_stats_creation(self):
        """Test creating archive statistics."""
        stats = ArchiveStats(
            path="/test/archive.zip",
            type="zip",
            size_bytes=1024,
            extracted_size_bytes=2048,
            compression_ratio=2.0,
            extraction_time_seconds=1.5,
            success=True,
            nested_depth=1,
        )

        assert stats.path == "/test/archive.zip"
        assert stats.type == "zip"
        assert stats.size_bytes == 1024
        assert stats.extracted_size_bytes == 2048
        assert stats.compression_ratio == 2.0
        assert stats.extraction_time_seconds == 1.5
        assert stats.success is True
        assert stats.nested_depth == 1
        assert stats.error_type is None
        assert stats.error_message is None
        assert stats.timestamp is not None

    def test_archive_stats_with_error(self):
        """Test creating archive statistics with error."""
        stats = ArchiveStats(
            path="/test/broken.zip",
            type="zip",
            success=False,
            error_type=ErrorType.CORRUPTION_ERROR.value,
            error_message="Archive is corrupted",
        )

        assert stats.success is False
        assert stats.error_type == "corruption_error"
        assert stats.error_message == "Archive is corrupted"


class TestStatisticsManager:
    """Test StatisticsManager functionality."""

    def test_initialization(self, stats_manager, temp_stats_file):
        """Test statistics manager initialization."""
        assert stats_manager.stats_file == temp_stats_file
        assert temp_stats_file.exists()

        # Check initial file structure
        with open(temp_stats_file) as f:
            data = json.load(f)

        assert data["version"] == "1.0"
        assert "created" in data
        assert "aggregated_stats" in data
        assert "recent_runs" in data
        assert data["recent_runs"] == []

    def test_start_extraction_run(self, stats_manager):
        """Test starting an extraction run."""
        run_id = stats_manager.start_extraction_run("/test/directory", "test_torrent")

        assert run_id.startswith("run_")
        assert stats_manager.current_run is not None
        assert stats_manager.current_run.run_id == run_id
        assert stats_manager.current_run.directory == "/test/directory"
        assert stats_manager.current_run.torrent_name == "test_torrent"
        assert stats_manager.current_run.total_processed == 0

    def test_record_archive_processed_success(self, stats_manager):
        """Test recording successful archive processing."""
        run_id = stats_manager.start_extraction_run("/test/directory")

        stats_manager.record_archive_processed(
            archive_path=Path("/test/archive.zip"),
            archive_type="zip",
            success=True,
            size_bytes=1024,
            extracted_size_bytes=2048,
            compression_ratio=2.0,
            extraction_time=1.5,
            nested_depth=0,
        )

        assert stats_manager.current_run.total_processed == 1
        assert stats_manager.current_run.successful == 1
        assert stats_manager.current_run.failed == 0
        assert len(stats_manager.current_run.archives) == 1

        archive_stats = stats_manager.current_run.archives[0]
        assert archive_stats.path == "/test/archive.zip"
        assert archive_stats.type == "zip"
        assert archive_stats.success is True
        assert archive_stats.size_bytes == 1024
        assert archive_stats.extracted_size_bytes == 2048

    def test_record_archive_processed_failure(self, stats_manager):
        """Test recording failed archive processing."""
        run_id = stats_manager.start_extraction_run("/test/directory")

        stats_manager.record_archive_processed(
            archive_path=Path("/test/broken.zip"),
            archive_type="zip",
            success=False,
            size_bytes=512,
            extraction_time=0.5,
            error_type=ErrorType.CORRUPTION_ERROR,
            error_message="Archive is corrupted",
            nested_depth=0,
        )

        assert stats_manager.current_run.total_processed == 1
        assert stats_manager.current_run.successful == 0
        assert stats_manager.current_run.failed == 1
        assert "corruption_error" in stats_manager.current_run.errors_by_type
        assert stats_manager.current_run.errors_by_type["corruption_error"] == 1

    def test_record_archive_skipped(self, stats_manager):
        """Test recording skipped archive."""
        run_id = stats_manager.start_extraction_run("/test/directory")

        stats_manager.record_archive_skipped(
            archive_path=Path("/test/existing.zip"), reason="already_processed"
        )

        assert stats_manager.current_run.total_processed == 1
        assert stats_manager.current_run.skipped == 1
        assert stats_manager.current_run.successful == 0
        assert stats_manager.current_run.failed == 0

    def test_finish_extraction_run(self, stats_manager):
        """Test finishing an extraction run."""
        run_id = stats_manager.start_extraction_run("/test/directory")

        # Add some archives
        stats_manager.record_archive_processed(
            archive_path=Path("/test/archive1.zip"),
            archive_type="zip",
            success=True,
            size_bytes=1024,
            extracted_size_bytes=2048,
            compression_ratio=2.0,
            extraction_time=1.0,
        )

        stats_manager.record_archive_processed(
            archive_path=Path("/test/archive2.rar"),
            archive_type="rar",
            success=True,
            size_bytes=2048,
            extracted_size_bytes=4096,
            compression_ratio=2.0,
            extraction_time=2.0,
        )

        # Finish the run
        completed_run = stats_manager.finish_extraction_run()

        assert completed_run is not None
        assert completed_run.run_id == run_id
        assert completed_run.total_processed == 2
        assert completed_run.successful == 2
        assert completed_run.failed == 0
        assert completed_run.end_time is not None
        assert completed_run.duration_seconds > 0
        assert completed_run.average_compression_ratio == 2.0
        assert completed_run.archives_per_second > 0
        assert completed_run.bytes_per_second > 0

        # Check archive type breakdown
        assert completed_run.archives_by_type["zip"] == 1
        assert completed_run.archives_by_type["rar"] == 1

        # Current run should be cleared
        assert stats_manager.current_run is None

    def test_get_aggregated_stats(self, stats_manager):
        """Test getting aggregated statistics."""
        # Start and finish a run
        run_id = stats_manager.start_extraction_run("/test/directory")
        stats_manager.record_archive_processed(
            archive_path=Path("/test/archive.zip"),
            archive_type="zip",
            success=True,
            size_bytes=1024,
            extraction_time=1.0,
        )
        stats_manager.finish_extraction_run()

        # Get aggregated stats
        aggregated = stats_manager.get_aggregated_stats()

        assert aggregated.total_runs == 1
        assert aggregated.lifetime_archives_processed == 1
        assert aggregated.lifetime_successful == 1
        assert aggregated.lifetime_failed == 0
        assert aggregated.lifetime_archive_size_bytes == 1024
        assert aggregated.most_common_archive_type == "zip"
        assert aggregated.average_archives_per_run == 1.0

    def test_get_recent_runs(self, stats_manager):
        """Test getting recent runs."""
        # Create multiple runs
        for i in range(3):
            run_id = stats_manager.start_extraction_run(f"/test/directory{i}")
            stats_manager.record_archive_processed(
                archive_path=Path(f"/test/archive{i}.zip"),
                archive_type="zip",
                success=True,
                size_bytes=1024,
                extraction_time=1.0,
            )
            stats_manager.finish_extraction_run()

        # Get recent runs
        recent_runs = stats_manager.get_recent_runs(limit=2)

        assert len(recent_runs) == 2
        # Should be in reverse chronological order (most recent first)
        assert recent_runs[0].directory == "/test/directory2"
        assert recent_runs[1].directory == "/test/directory1"

    def test_export_statistics(self, stats_manager, tmp_path):
        """Test exporting statistics."""
        # Create some data
        run_id = stats_manager.start_extraction_run("/test/directory")
        stats_manager.record_archive_processed(
            archive_path=Path("/test/archive.zip"),
            archive_type="zip",
            success=True,
            size_bytes=1024,
            extraction_time=1.0,
        )
        stats_manager.finish_extraction_run()

        # Export to a specific path
        export_path = tmp_path / "exported_stats.json"
        result_path = stats_manager.export_statistics(export_path)

        assert result_path == export_path
        assert export_path.exists()

        # Check exported data
        with open(export_path) as f:
            data = json.load(f)

        assert "export_info" in data
        assert data["export_info"]["exported_by"] == "qbit-torrent-extract"
        assert "aggregated_stats" in data
        assert "recent_runs" in data
        assert len(data["recent_runs"]) == 1

    def test_clear_statistics_keep_aggregated(self, stats_manager):
        """Test clearing statistics while keeping aggregated data."""
        # Create some data
        run_id = stats_manager.start_extraction_run("/test/directory")
        stats_manager.record_archive_processed(
            archive_path=Path("/test/archive.zip"),
            archive_type="zip",
            success=True,
            size_bytes=1024,
            extraction_time=1.0,
        )
        stats_manager.finish_extraction_run()

        # Clear but keep aggregated
        stats_manager.clear_statistics(keep_aggregated=True)

        # Recent runs should be cleared
        recent_runs = stats_manager.get_recent_runs()
        assert len(recent_runs) == 0

        # Aggregated stats should remain
        aggregated = stats_manager.get_aggregated_stats()
        assert aggregated.total_runs == 1
        assert aggregated.lifetime_archives_processed == 1

    def test_clear_statistics_all(self, stats_manager):
        """Test clearing all statistics."""
        # Create some data
        run_id = stats_manager.start_extraction_run("/test/directory")
        stats_manager.record_archive_processed(
            archive_path=Path("/test/archive.zip"),
            archive_type="zip",
            success=True,
            size_bytes=1024,
            extraction_time=1.0,
        )
        stats_manager.finish_extraction_run()

        # Clear everything
        stats_manager.clear_statistics(keep_aggregated=False)

        # All stats should be reset
        recent_runs = stats_manager.get_recent_runs()
        assert len(recent_runs) == 0

        aggregated = stats_manager.get_aggregated_stats()
        assert aggregated.total_runs == 0
        assert aggregated.lifetime_archives_processed == 0

    def test_no_active_run_warnings(self, stats_manager):
        """Test handling of operations without active run."""
        # Try to record without starting a run
        stats_manager.record_archive_processed(
            archive_path=Path("/test/archive.zip"),
            archive_type="zip",
            success=True,
            size_bytes=1024,
            extraction_time=1.0,
        )

        # Should not crash, but also not record anything
        assert stats_manager.current_run is None

        # Try to finish without starting
        result = stats_manager.finish_extraction_run()
        assert result is None

    def test_get_current_run_stats(self, stats_manager):
        """Test getting current run statistics."""
        # No active run
        assert stats_manager.get_current_run_stats() is None

        # Start a run
        run_id = stats_manager.start_extraction_run("/test/directory")
        stats_manager.record_archive_processed(
            archive_path=Path("/test/archive.zip"),
            archive_type="zip",
            success=True,
            size_bytes=1024,
            extraction_time=1.0,
        )

        # Get current stats
        current_stats = stats_manager.get_current_run_stats()
        assert current_stats is not None
        assert current_stats["run_id"] == run_id
        assert current_stats["total_processed"] == 1
        assert current_stats["successful"] == 1

    def test_config_snapshot(self, stats_manager):
        """Test configuration snapshot in run stats."""
        run_id = stats_manager.start_extraction_run("/test/directory")

        assert stats_manager.current_run.config_snapshot is not None
        assert "max_extraction_ratio" in stats_manager.current_run.config_snapshot
        assert "max_nested_depth" in stats_manager.current_run.config_snapshot
        assert "preserve_originals" in stats_manager.current_run.config_snapshot
        assert "log_level" in stats_manager.current_run.config_snapshot

    def test_atomic_writes(self, stats_manager, temp_stats_file):
        """Test that statistics writes are atomic."""
        # Create a run and finish it to trigger file write
        run_id = stats_manager.start_extraction_run("/test/directory")
        stats_manager.record_archive_processed(
            archive_path=Path("/test/archive.zip"),
            archive_type="zip",
            success=True,
            size_bytes=1024,
            extraction_time=1.0,
        )
        stats_manager.finish_extraction_run()

        # File should exist and be valid JSON
        assert temp_stats_file.exists()
        with open(temp_stats_file) as f:
            data = json.load(f)

        assert "recent_runs" in data
        assert len(data["recent_runs"]) == 1
        assert data["recent_runs"][0]["run_id"] == run_id

    def test_file_error_handling(self, stats_manager):
        """Test handling of file read/write errors."""
        # Point to an invalid path
        stats_manager.stats_file = Path("/invalid/path/stats.json")

        # Should not crash, return default stats
        aggregated = stats_manager.get_aggregated_stats()
        assert aggregated.total_runs == 0

        recent_runs = stats_manager.get_recent_runs()
        assert len(recent_runs) == 0


class TestGlobalStatisticsManager:
    """Test global statistics manager functionality."""

    def test_get_statistics_manager_singleton(self, config_with_stats_file):
        """Test that get_statistics_manager returns singleton."""
        # Clear any existing global instance
        import qbit_torrent_extract.statistics

        qbit_torrent_extract.statistics._statistics_manager = None

        manager1 = get_statistics_manager(config_with_stats_file)
        manager2 = get_statistics_manager(config_with_stats_file)

        assert manager1 is manager2

    def test_get_statistics_manager_with_none_config(self):
        """Test get_statistics_manager with None config."""
        # Clear any existing global instance
        import qbit_torrent_extract.statistics

        qbit_torrent_extract.statistics._statistics_manager = None

        manager = get_statistics_manager(None)
        assert manager is not None
        assert isinstance(manager, StatisticsManager)


class TestAggregatedStatsCalculations:
    """Test complex aggregated statistics calculations."""

    def test_multiple_runs_aggregation(self, stats_manager):
        """Test aggregation across multiple runs."""
        # Run 1
        run_id1 = stats_manager.start_extraction_run("/test/dir1")
        stats_manager.record_archive_processed(
            Path("/test/a1.zip"), "zip", True, 1000, extraction_time=1.0
        )
        stats_manager.record_archive_processed(
            Path("/test/a2.rar"),
            "rar",
            False,
            2000,
            extraction_time=0.5,
            error_type=ErrorType.CORRUPTION_ERROR,
        )
        stats_manager.finish_extraction_run()

        # Run 2
        run_id2 = stats_manager.start_extraction_run("/test/dir2")
        stats_manager.record_archive_processed(
            Path("/test/a3.zip"), "zip", True, 1500, extraction_time=2.0
        )
        stats_manager.record_archive_processed(
            Path("/test/a4.7z"), "7z", True, 500, extraction_time=0.8
        )
        stats_manager.finish_extraction_run()

        # Check aggregated stats
        aggregated = stats_manager.get_aggregated_stats()

        assert aggregated.total_runs == 2
        assert aggregated.lifetime_archives_processed == 4
        assert aggregated.lifetime_successful == 3
        assert aggregated.lifetime_failed == 1
        assert aggregated.lifetime_archive_size_bytes == 5000

        # Check type breakdowns
        assert aggregated.lifetime_archives_by_type["zip"] == 2
        assert aggregated.lifetime_archives_by_type["rar"] == 1
        assert aggregated.lifetime_archives_by_type["7z"] == 1

        assert aggregated.lifetime_errors_by_type["corruption_error"] == 1

        # Check computed values
        assert aggregated.average_archives_per_run == 2.0
        assert aggregated.most_common_archive_type == "zip"
        assert aggregated.most_common_error_type == "corruption_error"
        assert aggregated.largest_archive_processed_bytes == 2000

    def test_performance_metrics(self, stats_manager):
        """Test performance metric calculations."""
        run_id = stats_manager.start_extraction_run("/test/directory")

        # Add archives with different processing times
        stats_manager.record_archive_processed(
            Path("/test/fast.zip"), "zip", True, 1000, extraction_time=0.5
        )
        stats_manager.record_archive_processed(
            Path("/test/slow.zip"), "zip", True, 2000, extraction_time=2.0
        )

        completed_run = stats_manager.finish_extraction_run()

        # Performance should be calculated
        assert completed_run.archives_per_second > 0
        assert completed_run.bytes_per_second > 0
        assert completed_run.duration_seconds > 0

        # Check that performance metrics are calculated (actual values depend on test timing)
        # The archives_per_second calculation is based on wall-clock time, not extraction_time
        assert completed_run.archives_per_second > 0

    def test_compression_ratio_averaging(self, stats_manager):
        """Test compression ratio averaging."""
        run_id = stats_manager.start_extraction_run("/test/directory")

        stats_manager.record_archive_processed(
            Path("/test/a1.zip"),
            "zip",
            True,
            1000,
            extracted_size_bytes=3000,
            compression_ratio=3.0,
            extraction_time=1.0,
        )
        stats_manager.record_archive_processed(
            Path("/test/a2.zip"),
            "zip",
            True,
            1000,
            extracted_size_bytes=1000,
            compression_ratio=1.0,
            extraction_time=1.0,
        )

        completed_run = stats_manager.finish_extraction_run()

        # Average should be (3.0 + 1.0) / 2 = 2.0
        assert completed_run.average_compression_ratio == 2.0
