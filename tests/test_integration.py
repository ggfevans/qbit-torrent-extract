"""Integration tests for the complete system."""

import json
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from qbit_torrent_extract.config import Config, load_config
from qbit_torrent_extract.extractor import ArchiveExtractor
from qbit_torrent_extract.logger import setup_logging, cleanup_logging
from qbit_torrent_extract.statistics import get_statistics_manager


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
        cleanup_logging()

    def create_complex_archive_structure(self):
        """Create a complex nested archive structure for testing."""
        # Create the deepest content
        content_file = self.temp_path / "final_content.txt"
        content_file.write_text("This is the final extracted content!")

        # Create first level ZIP
        level1_zip = self.temp_path / "level1.zip"
        with zipfile.ZipFile(level1_zip, "w") as zf:
            zf.write(content_file, "final_content.txt")
        content_file.unlink()

        # Create second level ZIP containing first level
        level2_zip = self.temp_path / "level2.zip"
        with zipfile.ZipFile(level2_zip, "w") as zf:
            zf.write(level1_zip, "level1.zip")
            zf.writestr("readme.txt", "This archive contains another archive")
        level1_zip.unlink()

        # Create main ZIP with multiple files including nested archive
        main_zip = self.temp_path / "main_archive.zip"
        with zipfile.ZipFile(main_zip, "w") as zf:
            zf.write(level2_zip, "nested/level2.zip")
            zf.writestr("main_readme.txt", "Main archive readme")
            zf.writestr("docs/documentation.txt", "Some documentation")
        level2_zip.unlink()

        return main_zip

    def test_complete_extraction_workflow(self):
        """Test complete extraction workflow with logging and statistics."""
        # Setup configuration
        config = Config(
            log_level="DEBUG",
            log_dir=str(self.temp_path / "logs"),
            stats_file=str(self.temp_path / "stats.json"),
            max_nested_depth=5,
            preserve_originals=True
        )

        # Setup logging
        logging_manager = setup_logging(config)

        # Create test structure
        main_archive = self.create_complex_archive_structure()

        # Initialize components
        extractor = ArchiveExtractor(
            preserve_archives=config.preserve_originals,
            config=config,
            torrent_name="TestTorrent"
        )

        # Perform extraction
        stats = extractor.extract_all(str(self.temp_path))

        # Verify extraction results
        assert stats["total_processed"] >= 1
        assert stats["successful"] >= 1

        # Verify all files were extracted
        expected_files = [
            "final_content.txt",
            "main_readme.txt", 
            "docs/documentation.txt",
            "readme.txt"
        ]

        for expected_file in expected_files:
            file_path = self.temp_path / expected_file
            assert file_path.exists(), f"Expected file not found: {expected_file}"

        # Verify final content
        final_content = self.temp_path / "final_content.txt"
        assert final_content.read_text() == "This is the final extracted content!"

        # Verify original archive is preserved
        assert main_archive.exists()

        # Verify logs were created
        log_dir = Path(config.log_dir)
        assert log_dir.exists()
        assert (log_dir / "qbit-torrent-extract.log").exists()

        # Verify statistics were recorded
        stats_file = Path(config.stats_file)
        assert stats_file.exists()
        
        stats_data = json.loads(stats_file.read_text())
        assert "runs" in stats_data
        assert len(stats_data["runs"]) > 0

    def test_configuration_integration(self):
        """Test integration of configuration system with all components."""
        # Create configuration file
        config_file = self.temp_path / "test_config.json"
        config_data = {
            "max_extraction_ratio": 50.0,
            "max_nested_depth": 2,
            "log_level": "INFO",
            "preserve_originals": False,
            "skip_on_error": True
        }
        config_file.write_text(json.dumps(config_data))

        # Load configuration
        config = load_config(config_file=str(config_file))

        # Verify configuration was loaded correctly
        assert config.max_extraction_ratio == 50.0
        assert config.max_nested_depth == 2
        assert config.log_level == "INFO"
        assert config.preserve_originals is False

        # Create test archive
        test_zip = self.temp_path / "test.zip"
        with zipfile.ZipFile(test_zip, "w") as zf:
            zf.writestr("test.txt", "test content")

        # Test extraction with loaded configuration
        extractor = ArchiveExtractor(config=config)
        stats = extractor.extract_all(str(self.temp_path))

        assert stats["successful"] == 1
        assert (self.temp_path / "test.txt").exists()
        
        # Archive should be deleted (preserve_originals=False)
        assert not test_zip.exists()

    def test_error_recovery_integration(self):
        """Test error recovery across all system components."""
        config = Config(
            skip_on_error=True,
            log_level="DEBUG",
            log_dir=str(self.temp_path / "logs")
        )

        setup_logging(config)

        # Create mix of valid and invalid archives
        valid_zip = self.temp_path / "valid.zip"
        with zipfile.ZipFile(valid_zip, "w") as zf:
            zf.writestr("valid.txt", "valid content")

        # Create corrupted archive
        corrupted_zip = self.temp_path / "corrupted.zip"
        corrupted_zip.write_bytes(b"invalid zip data")

        # Create fake archive
        fake_zip = self.temp_path / "fake.zip"
        fake_zip.write_text("not a zip file")

        extractor = ArchiveExtractor(config=config)
        stats = extractor.extract_all(str(self.temp_path))

        # Should process all archives but only succeed on valid one
        assert stats["total_processed"] == 3
        assert stats["successful"] == 1
        assert stats["failed"] == 2

        # Valid content should be extracted
        assert (self.temp_path / "valid.txt").exists()

        # Errors should be recorded
        assert len(stats["errors"]) == 2

    def test_statistics_integration_across_runs(self):
        """Test statistics tracking across multiple extraction runs."""
        stats_file = self.temp_path / "integration_stats.json"
        config = Config(stats_file=str(stats_file))

        # First run
        extractor1 = ArchiveExtractor(config=config)
        
        zip1 = self.temp_path / "run1.zip"
        with zipfile.ZipFile(zip1, "w") as zf:
            zf.writestr("run1.txt", "first run")
        
        stats1 = extractor1.extract_all(str(self.temp_path))
        zip1_extracted = self.temp_path / "run1.txt"
        if zip1_extracted.exists():
            zip1_extracted.unlink()

        # Second run
        extractor2 = ArchiveExtractor(config=config)
        
        zip2 = self.temp_path / "run2.zip"
        with zipfile.ZipFile(zip2, "w") as zf:
            zf.writestr("run2.txt", "second run")
        
        stats2 = extractor2.extract_all(str(self.temp_path))

        # Get aggregated statistics
        stats_manager = get_statistics_manager(config)
        aggregated = stats_manager.get_aggregated_stats()

        # Should have data from both runs
        assert aggregated.total_runs >= 2
        assert aggregated.lifetime_archives_processed >= 2
        assert aggregated.lifetime_successful >= 2

    def test_logging_integration_with_components(self):
        """Test logging integration across all components."""
        log_dir = self.temp_path / "integration_logs"
        config = Config(
            log_level="DEBUG",
            log_dir=str(log_dir)
        )

        logging_manager = setup_logging(config)

        # Create test archive with nested structure
        main_archive = self.create_complex_archive_structure()

        extractor = ArchiveExtractor(
            config=config,
            torrent_name="IntegrationTest"
        )

        # Perform extraction
        stats = extractor.extract_all(str(self.temp_path))

        # Verify log files were created
        assert log_dir.exists()
        main_log = log_dir / "qbit-torrent-extract.log"
        torrent_log = log_dir / "IntegrationTest.log"
        
        assert main_log.exists()
        assert torrent_log.exists()

        # Verify log content
        main_log_content = main_log.read_text()
        assert "Starting extraction" in main_log_content or "Processing directory" in main_log_content

        torrent_log_content = torrent_log.read_text()
        assert "IntegrationTest" in torrent_log_content or len(torrent_log_content) > 0


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
        cleanup_logging()

    def test_qbittorrent_torrent_simulation(self):
        """Simulate a real qBittorrent torrent completion scenario."""
        # Simulate qBittorrent directory structure
        torrent_dir = self.temp_path / "TorrentName"
        torrent_dir.mkdir()

        # Create various archive types as might be found in a torrent
        archives_data = [
            ("Movie.zip", "movie_file.mkv", "fake movie content"),
            ("Subtitles.rar", "subtitles.srt", "fake subtitle content"),
            ("Extras.7z", "extras.txt", "extra content"),
            ("nested/Archive.zip", "nested_file.txt", "nested content")
        ]

        # Create directory structure and archives
        for archive_name, content_name, content in archives_data:
            archive_path = torrent_dir / archive_name
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            
            if archive_name.endswith('.zip'):
                with zipfile.ZipFile(archive_path, "w") as zf:
                    zf.writestr(content_name, content)

        # Configure as if called by qBittorrent
        config = Config(
            preserve_originals=True,
            log_level="INFO",
            max_nested_depth=3
        )

        # Simulate qBittorrent extraction
        extractor = ArchiveExtractor(
            config=config,
            torrent_name="TorrentName"
        )

        stats = extractor.extract_all(str(torrent_dir))

        # Verify extraction results
        assert stats["total_processed"] >= 1  # At least ZIP files should be processed
        
        # Verify ZIP content was extracted
        assert (torrent_dir / "movie_file.mkv").exists()
        assert (torrent_dir / "nested" / "nested_file.txt").exists()

    def test_mixed_archive_types_real_scenario(self):
        """Test with a realistic mix of archive types and sizes."""
        # Create archives of different types and characteristics
        archives = [
            # Small ZIP with documents
            ("Documents.zip", [("readme.txt", "Documentation"), ("license.txt", "MIT License")]),
            # Medium ZIP with multiple files
            ("Source.zip", [(f"src/file_{i}.py", f"# Python file {i}\nprint('hello')") for i in range(10)]),
            # Large-ish ZIP with binary-like content
            ("Data.zip", [("data.bin", "B" * 10000)])  # 10KB of binary-like data
        ]

        for archive_name, file_data in archives:
            archive_path = self.temp_path / archive_name
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for filename, content in file_data:
                    zf.writestr(filename, content)

        config = Config(preserve_originals=True)
        extractor = ArchiveExtractor(config=config)
        
        stats = extractor.extract_all(str(self.temp_path))

        # Verify all archives were processed
        assert stats["total_processed"] == 3
        assert stats["successful"] == 3
        assert stats["failed"] == 0

        # Verify specific files were extracted
        assert (self.temp_path / "readme.txt").exists()
        assert (self.temp_path / "src" / "file_0.py").exists()
        assert (self.temp_path / "data.bin").exists()
        
        # Verify file contents
        assert "Documentation" in (self.temp_path / "readme.txt").read_text()
        assert "print('hello')" in (self.temp_path / "src" / "file_0.py").read_text()

    def test_progressive_extraction_scenario(self):
        """Test scenario where archives contain other archives progressively."""
        # Create a chain of archives: main.zip -> level1.zip -> level2.zip -> content
        
        # Innermost content
        final_content = "Final extracted content from deep nesting"
        
        # Build nested structure
        level2_zip = self.temp_path / "level2.zip"
        with zipfile.ZipFile(level2_zip, "w") as zf:
            zf.writestr("final.txt", final_content)
            zf.writestr("level2_readme.txt", "Level 2 archive")

        level1_zip = self.temp_path / "level1.zip"
        with zipfile.ZipFile(level1_zip, "w") as zf:
            zf.write(level2_zip, "level2.zip")
            zf.writestr("level1_readme.txt", "Level 1 archive")
        level2_zip.unlink()

        main_zip = self.temp_path / "main.zip"
        with zipfile.ZipFile(main_zip, "w") as zf:
            zf.write(level1_zip, "level1.zip")
            zf.writestr("main_readme.txt", "Main archive")
            zf.writestr("other_file.txt", "Other content in main archive")
        level1_zip.unlink()

        # Configure for deep extraction
        config = Config(
            max_nested_depth=5,
            preserve_originals=True
        )

        extractor = ArchiveExtractor(config=config)
        stats = extractor.extract_all(str(self.temp_path))

        # Verify progressive extraction worked
        expected_files = [
            "final.txt",
            "level2_readme.txt", 
            "level1_readme.txt",
            "main_readme.txt",
            "other_file.txt"
        ]

        for expected_file in expected_files:
            file_path = self.temp_path / expected_file
            assert file_path.exists(), f"Expected file not found: {expected_file}"

        # Verify final content is correct
        final_file = self.temp_path / "final.txt"
        assert final_file.read_text() == final_content


class TestSystemIntegration:
    """Test integration with system-level features."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        cleanup_logging()

    def test_disk_space_handling(self):
        """Test behavior when dealing with disk space constraints."""
        # This is more of a behavioral test since we can't easily simulate
        # low disk space in a unit test, but we can verify the system
        # handles large extractions gracefully
        
        config = Config()
        extractor = ArchiveExtractor(config=config)

        # Create an archive that will extract to a known size
        large_content = "X" * (100 * 1024)  # 100KB
        large_zip = self.temp_path / "large.zip"
        
        with zipfile.ZipFile(large_zip, "w", compression=zipfile.ZIP_STORED) as zf:
            for i in range(10):  # 10 files * 100KB = ~1MB total
                zf.writestr(f"large_file_{i}.txt", large_content)

        stats = extractor.extract_all(str(self.temp_path))

        # Should handle large extraction without issues
        assert stats["successful"] == 1
        
        # Verify all files were extracted
        extracted_files = list(self.temp_path.glob("large_file_*.txt"))
        assert len(extracted_files) == 10

    def test_concurrent_access_simulation(self):
        """Test behavior when files might be accessed concurrently."""
        # Simulate scenario where extraction happens while files are being read
        
        config = Config(preserve_originals=True)
        
        # Create test archive
        test_zip = self.temp_path / "concurrent.zip"
        with zipfile.ZipFile(test_zip, "w") as zf:
            zf.writestr("shared_file.txt", "content that might be read concurrently")

        extractor = ArchiveExtractor(config=config)

        # Perform extraction
        stats = extractor.extract_all(str(self.temp_path))

        # Verify extraction succeeded
        assert stats["successful"] == 1
        extracted_file = self.temp_path / "shared_file.txt"
        assert extracted_file.exists()

        # Verify original archive still exists (preserve mode)
        assert test_zip.exists()

        # Simulate concurrent read access
        content = extracted_file.read_text()
        assert content == "content that might be read concurrently"

    @pytest.mark.skipif(not hasattr(zipfile, 'ZipFile'), reason="ZIP support required")
    def test_different_compression_methods(self):
        """Test handling of different compression methods in archives."""
        # Create archives with different compression methods
        compressions = [
            (zipfile.ZIP_STORED, "stored.zip"),
            (zipfile.ZIP_DEFLATED, "deflated.zip")
        ]

        content = "Test content for compression testing " * 100  # Make it worth compressing

        for compression, filename in compressions:
            zip_path = self.temp_path / filename
            with zipfile.ZipFile(zip_path, "w", compression=compression) as zf:
                zf.writestr("test.txt", content)

        config = Config()
        extractor = ArchiveExtractor(config=config)
        
        stats = extractor.extract_all(str(self.temp_path))

        # Should handle all compression methods
        assert stats["total_processed"] == len(compressions)
        assert stats["successful"] == len(compressions)

        # Verify content is extracted correctly regardless of compression
        test_files = list(self.temp_path.glob("test.txt"))
        # Note: Multiple test.txt files might be created, but at least one should exist
        assert len(test_files) >= 1
        
        # Verify content of at least one extracted file
        assert content in test_files[0].read_text()