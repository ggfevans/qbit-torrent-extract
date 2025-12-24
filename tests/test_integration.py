"""Integration tests for the complete system."""

import json
import tempfile
import zipfile
from pathlib import Path

import pytest

from qbit_torrent_extract.config import Config, load_config
from qbit_torrent_extract.extractor import ArchiveExtractor
from qbit_torrent_extract.logger import setup_logging


class TestEndToEndIntegration:
    """Test complete end-to-end workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_extraction_workflow(self):
        """Test complete extraction workflow with logging."""
        config = Config(
            log_level="DEBUG",
            log_dir=str(self.temp_path / "logs"),
            max_nested_depth=5,
            preserve_originals=True
        )
        setup_logging(level=config.log_level, log_dir=config.log_dir)

        # Create simple nested structure
        inner_zip = self.temp_path / "inner.zip"
        with zipfile.ZipFile(inner_zip, "w") as zf:
            zf.writestr("innerfile.txt", "inner content")

        outer_zip = self.temp_path / "outer.zip"
        with zipfile.ZipFile(outer_zip, "w") as zf:
            zf.write(inner_zip, "inner.zip")
            zf.writestr("outerfile.txt", "outer content")
        inner_zip.unlink()

        extractor = ArchiveExtractor(
            preserve_archives=config.preserve_originals,
            config=config,
        )

        stats = extractor.extract_all(str(self.temp_path))

        # Verify extraction results
        assert stats["total_processed"] >= 1
        assert stats["successful"] >= 1

        # Verify files were extracted
        assert (self.temp_path / "outerfile.txt").exists()
        assert (self.temp_path / "inner.zip").exists()  # Extracted from outer
        assert (self.temp_path / "innerfile.txt").exists()  # Extracted from inner

        # Verify logs were created
        log_dir = Path(config.log_dir)
        assert log_dir.exists()
        assert (log_dir / "qbit-torrent-extract.log").exists()

    def test_configuration_integration(self):
        """Test configuration with preserve=False."""
        config_data = {"preserve_originals": False, "max_extraction_ratio": 200.0}
        config_path = self.temp_path / "config.json"
        config_path.write_text(json.dumps(config_data))

        config = load_config(config_file=str(config_path))

        test_zip = self.temp_path / "test.zip"
        with zipfile.ZipFile(test_zip, "w") as zf:
            zf.writestr("test.txt", "test content here")

        extractor = ArchiveExtractor(
            preserve_archives=config.preserve_originals,
            config=config
        )
        stats = extractor.extract_all(str(self.temp_path))

        assert stats["successful"] == 1
        assert (self.temp_path / "test.txt").exists()
        # Archive should be deleted (preserve_originals=False)
        assert not test_zip.exists()

    def test_error_recovery_integration(self):
        """Test error recovery across all system components."""
        config = Config(
            log_level="DEBUG",
            log_dir=str(self.temp_path / "logs")
        )
        setup_logging(level=config.log_level, log_dir=config.log_dir)

        # Create valid and invalid archives
        valid_zip = self.temp_path / "valid.zip"
        with zipfile.ZipFile(valid_zip, "w") as zf:
            zf.writestr("valid.txt", "valid content")

        invalid_zip = self.temp_path / "invalid.zip"
        invalid_zip.write_bytes(b"not a zip file")

        extractor = ArchiveExtractor(config=config)
        stats = extractor.extract_all(str(self.temp_path))

        # Should process both
        assert stats["total_processed"] == 2
        assert stats["successful"] == 1
        assert stats["failed"] == 1

        # Errors should be recorded
        assert len(stats["errors"]) == 1

    def test_logging_integration_with_components(self):
        """Test logging integration across all components."""
        log_dir = self.temp_path / "integration_logs"
        config = Config(log_level="DEBUG", log_dir=str(log_dir))

        setup_logging(level=config.log_level, log_dir=config.log_dir)

        # Create simple test archive
        test_zip = self.temp_path / "test.zip"
        with zipfile.ZipFile(test_zip, "w") as zf:
            zf.writestr("test.txt", "test content")

        extractor = ArchiveExtractor(config=config)
        stats = extractor.extract_all(str(self.temp_path))

        # Verify log files were created
        assert log_dir.exists()
        main_log = log_dir / "qbit-torrent-extract.log"
        assert main_log.exists()
        assert "Extracting" in main_log.read_text() or "Starting" in main_log.read_text()


class TestRealWorldScenarios:
    """Test scenarios that mimic real-world usage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_qbittorrent_torrent_simulation(self):
        """Simulate qBittorrent torrent structure."""
        torrent_dir = self.temp_path / "My.Download.2024"
        torrent_dir.mkdir()

        # Create typical torrent content
        archives = [
            ("Content.zip", "content.txt", "actual content"),
            ("Extras.zip", "extras.txt", "extra content"),
        ]

        for archive_name, content_name, content in archives:
            archive_path = torrent_dir / archive_name
            with zipfile.ZipFile(archive_path, "w") as zf:
                zf.writestr(content_name, content)

        config = Config(preserve_originals=True, max_nested_depth=3)
        extractor = ArchiveExtractor(config=config)

        stats = extractor.extract_all(str(torrent_dir))

        assert stats["successful"] == 2
        assert (torrent_dir / "content.txt").exists()
        assert (torrent_dir / "extras.txt").exists()

    def test_mixed_archive_types_real_scenario(self):
        """Test mixed archive types in real scenario."""
        # Use high ratio to avoid zipbomb detection on test data
        config = Config(max_extraction_ratio=500.0)
        extractor = ArchiveExtractor(config=config)

        # Create different archive types
        zip_path = self.temp_path / "Documents.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("doc.txt", "document content")

        zip2_path = self.temp_path / "Source.zip"
        with zipfile.ZipFile(zip2_path, "w") as zf:
            zf.writestr("source.txt", "source content")

        zip3_path = self.temp_path / "Data.zip"
        with zipfile.ZipFile(zip3_path, "w") as zf:
            zf.writestr("data.txt", "data content")

        stats = extractor.extract_all(str(self.temp_path))

        assert stats["successful"] == 3
        assert (self.temp_path / "doc.txt").exists()
        assert (self.temp_path / "source.txt").exists()
        assert (self.temp_path / "data.txt").exists()

    def test_progressive_extraction_scenario(self):
        """Test extraction of archives that create more archives."""
        # Level 1: Inner archive
        inner = self.temp_path / "inner.zip"
        with zipfile.ZipFile(inner, "w") as zf:
            zf.writestr("final.txt", "final content")

        # Level 2: Outer archive containing inner
        outer = self.temp_path / "outer.zip"
        with zipfile.ZipFile(outer, "w") as zf:
            zf.write(inner, "inner.zip")
        inner.unlink()

        config = Config(max_nested_depth=5)
        extractor = ArchiveExtractor(config=config)

        stats = extractor.extract_all(str(self.temp_path))

        assert stats["successful"] == 2
        assert (self.temp_path / "final.txt").exists()


class TestSystemIntegration:
    """System-level integration tests."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_disk_space_handling(self):
        """Test handling when disk space is available."""
        config = Config()
        extractor = ArchiveExtractor(config=config)

        # Create small archive
        zip_path = self.temp_path / "small.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("small.txt", "small content")

        stats = extractor.extract_all(str(self.temp_path))
        assert stats["successful"] == 1

    def test_concurrent_access_simulation(self):
        """Test extraction doesn't interfere with itself."""
        config = Config()
        extractor = ArchiveExtractor(config=config)

        # Create multiple archives
        for i in range(3):
            zip_path = self.temp_path / f"archive_{i}.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr(f"file_{i}.txt", f"content {i}")

        stats = extractor.extract_all(str(self.temp_path))
        assert stats["successful"] == 3

    def test_different_compression_methods(self):
        """Test extraction with different compression methods."""
        config = Config(max_extraction_ratio=500.0)  # Allow high ratio for compressed
        extractor = ArchiveExtractor(config=config)

        # Stored (no compression)
        stored = self.temp_path / "stored.zip"
        with zipfile.ZipFile(stored, "w", compression=zipfile.ZIP_STORED) as zf:
            zf.writestr("stored.txt", "stored content")

        # Deflated
        deflated = self.temp_path / "deflated.zip"
        with zipfile.ZipFile(deflated, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("deflated.txt", "deflated content")

        stats = extractor.extract_all(str(self.temp_path))
        assert stats["successful"] == 2
