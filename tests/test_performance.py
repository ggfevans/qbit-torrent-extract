"""Performance tests for archive extraction."""

import time
import tempfile
import zipfile
from pathlib import Path

import pytest

from qbit_torrent_extract.config import Config
from qbit_torrent_extract.extractor import ArchiveExtractor


class TestExtractionPerformance:
    """Test extraction performance characteristics."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.config = Config()
        self.extractor = ArchiveExtractor(config=self.config)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.performance
    def test_small_files_performance(self):
        """Test performance with many small files."""
        zip_path = self.temp_path / "small_files.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for i in range(100):
                zf.writestr(f"file_{i}.txt", f"content {i}")

        start = time.time()
        stats = self.extractor.extract_all(str(self.temp_path))
        elapsed = time.time() - start

        assert elapsed < 5.0
        assert stats["successful"] == 1

    @pytest.mark.performance
    def test_nested_archives_performance(self):
        """Test performance with nested archives."""
        # Create inner archive
        inner = self.temp_path / "inner.zip"
        with zipfile.ZipFile(inner, "w") as zf:
            for i in range(10):
                zf.writestr(f"inner_{i}.txt", f"content {i}")

        # Create outer archive
        outer = self.temp_path / "outer.zip"
        with zipfile.ZipFile(outer, "w") as zf:
            zf.write(inner, "inner.zip")
        inner.unlink()

        start = time.time()
        stats = self.extractor.extract_all(str(self.temp_path))
        elapsed = time.time() - start

        assert elapsed < 5.0
        assert stats["successful"] == 2


class TestValidationPerformance:
    """Test validation performance."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.performance
    def test_validation_speed(self):
        """Test that validation is fast."""
        from qbit_torrent_extract.validator import ArchiveValidator

        zip_path = self.temp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test.txt", "content")

        config = Config()
        validator = ArchiveValidator(config)

        start = time.time()
        for _ in range(100):
            validator.validate_archive(zip_path)
        elapsed = time.time() - start

        # 100 validations should take less than 2 seconds
        assert elapsed < 2.0


class TestBenchmarks:
    """Simple benchmarks for regression testing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.performance
    def test_baseline_performance_benchmark(self):
        """Establish baseline extraction performance."""
        config = Config()
        extractor = ArchiveExtractor(config=config)

        # Create 5 simple archives
        for i in range(5):
            zip_path = self.temp_path / f"archive_{i}.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("test.txt", "content")

        start = time.time()
        stats = extractor.extract_all(str(self.temp_path))
        elapsed = time.time() - start

        assert elapsed < 3.0
        assert stats["successful"] == 5
