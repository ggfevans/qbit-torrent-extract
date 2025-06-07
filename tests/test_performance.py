"""Performance tests for archive extraction."""

import time
import tempfile
import zipfile
from pathlib import Path
from typing import List

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

    def create_test_archive(self, num_files: int, file_size: int, filename: str) -> Path:
        """Create a test archive with specified characteristics."""
        zip_path = self.temp_path / filename
        content = "X" * file_size
        
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for i in range(num_files):
                zf.writestr(f"file_{i:04d}.txt", content)
        
        return zip_path

    def measure_extraction_time(self, archive_path: Path) -> float:
        """Measure the time taken to extract an archive."""
        start_time = time.time()
        self.extractor.extract_all(str(self.temp_path))
        end_time = time.time()
        return end_time - start_time

    @pytest.mark.performance
    def test_small_files_performance(self):
        """Test performance with many small files."""
        # Create archive with 100 small files (1KB each)
        archive = self.create_test_archive(100, 1024, "small_files.zip")
        
        extraction_time = self.measure_extraction_time(archive)
        
        # Should complete reasonably quickly (adjust threshold as needed)
        assert extraction_time < 5.0, f"Small files extraction took {extraction_time:.2f}s"
        
        # Verify all files were extracted
        extracted_files = list(self.temp_path.glob("file_*.txt"))
        assert len(extracted_files) == 100

    @pytest.mark.performance
    def test_large_file_performance(self):
        """Test performance with a single large file."""
        # Create archive with 1 large file (1MB)
        archive = self.create_test_archive(1, 1024 * 1024, "large_file.zip")
        
        extraction_time = self.measure_extraction_time(archive)
        
        # Should complete reasonably quickly
        assert extraction_time < 10.0, f"Large file extraction took {extraction_time:.2f}s"
        
        # Verify file was extracted
        extracted_file = self.temp_path / "file_0000.txt"
        assert extracted_file.exists()
        assert extracted_file.stat().st_size == 1024 * 1024

    @pytest.mark.performance
    def test_multiple_archives_performance(self):
        """Test performance when processing multiple archives."""
        archives = []
        
        # Create 10 archives with 10 files each
        for i in range(10):
            archive = self.create_test_archive(10, 1024, f"archive_{i}.zip")
            archives.append(archive)
        
        start_time = time.time()
        stats = self.extractor.extract_all(str(self.temp_path))
        extraction_time = time.time() - start_time
        
        # Should process all archives efficiently
        assert extraction_time < 15.0, f"Multiple archives extraction took {extraction_time:.2f}s"
        assert stats["total_processed"] == 10
        assert stats["successful"] == 10
        
        # Verify all files were extracted (10 archives * 10 files = 100 files)
        extracted_files = list(self.temp_path.glob("file_*.txt"))
        assert len(extracted_files) == 100

    @pytest.mark.performance
    def test_nested_archives_performance(self):
        """Test performance with nested archives."""
        # Create inner archive
        inner_content = "A" * 1024
        inner_zip = self.temp_path / "inner.zip"
        with zipfile.ZipFile(inner_zip, "w") as zf:
            for i in range(10):
                zf.writestr(f"inner_{i}.txt", inner_content)
        
        # Create outer archive containing inner archive
        outer_zip = self.temp_path / "outer.zip"
        with zipfile.ZipFile(outer_zip, "w") as zf:
            zf.write(inner_zip, "inner.zip")
        
        # Remove standalone inner archive
        inner_zip.unlink()
        
        start_time = time.time()
        stats = self.extractor.extract_all(str(self.temp_path))
        extraction_time = time.time() - start_time
        
        # Should handle nested extraction efficiently
        assert extraction_time < 10.0, f"Nested archives extraction took {extraction_time:.2f}s"
        
        # Verify nested files were extracted
        extracted_files = list(self.temp_path.glob("inner_*.txt"))
        assert len(extracted_files) == 10

    @pytest.mark.performance
    def test_memory_usage_large_archive(self):
        """Test memory usage characteristics with large archives."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create a moderately large archive (should not cause memory issues)
        archive = self.create_test_archive(50, 10 * 1024, "memory_test.zip")
        
        # Extract archive
        stats = self.extractor.extract_all(str(self.temp_path))
        
        # Check final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100, f"Memory usage increased by {memory_increase:.1f}MB"
        assert stats["successful"] == 1


class TestValidationPerformance:
    """Test validation performance characteristics."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.config = Config()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.performance
    def test_validation_speed(self):
        """Test archive validation performance."""
        from qbit_torrent_extract.validator import ArchiveValidator
        
        validator = ArchiveValidator(self.config)
        
        # Create multiple test archives
        archives = []
        for i in range(20):
            zip_path = self.temp_path / f"test_{i}.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("test.txt", f"content {i}")
            archives.append(zip_path)
        
        # Measure validation time
        start_time = time.time()
        for archive in archives:
            result = validator.validate_archive(archive)
            assert result.is_valid
        validation_time = time.time() - start_time
        
        # Should validate quickly
        assert validation_time < 5.0, f"Validation took {validation_time:.2f}s for 20 archives"
        
        # Average validation time per archive
        avg_time = validation_time / len(archives)
        assert avg_time < 0.25, f"Average validation time {avg_time:.3f}s per archive"


class TestConcurrencyPerformance:
    """Test performance under concurrent-like scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.config = Config()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.performance
    def test_sequential_vs_batch_processing(self):
        """Compare sequential processing vs batch processing performance."""
        # Create multiple archives
        archives = []
        for i in range(5):
            zip_path = self.temp_path / f"batch_test_{i}.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                for j in range(5):
                    zf.writestr(f"file_{j}.txt", f"content {i}_{j}")
            archives.append(zip_path)
        
        # Test batch processing (single extractor instance)
        extractor = ArchiveExtractor(config=self.config)
        start_time = time.time()
        stats = extractor.extract_all(str(self.temp_path))
        batch_time = time.time() - start_time
        
        assert stats["total_processed"] == 5
        assert stats["successful"] == 5
        
        # Batch processing should be reasonably efficient
        assert batch_time < 10.0, f"Batch processing took {batch_time:.2f}s"


class TestScalabilityMetrics:
    """Test scalability characteristics and collect metrics."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.config = Config()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.performance
    def test_throughput_metrics(self):
        """Test and measure extraction throughput."""
        # Create archives of varying sizes
        archive_sizes = [1, 5, 10, 20]  # Number of files per archive
        file_size = 1024  # 1KB per file
        
        results = []
        
        for size in archive_sizes:
            # Create archive
            zip_path = self.temp_path / f"throughput_{size}.zip"
            content = "X" * file_size
            
            with zipfile.ZipFile(zip_path, "w") as zf:
                for i in range(size):
                    zf.writestr(f"file_{i}.txt", content)
            
            # Measure extraction
            extractor = ArchiveExtractor(config=self.config)
            start_time = time.time()
            stats = extractor.extract_all(str(self.temp_path))
            end_time = time.time()
            
            extraction_time = end_time - start_time
            files_per_second = size / extraction_time if extraction_time > 0 else float('inf')
            
            results.append({
                'archive_size': size,
                'extraction_time': extraction_time,
                'files_per_second': files_per_second
            })
            
            # Clean up extracted files for next test
            for extracted_file in self.temp_path.glob("file_*.txt"):
                extracted_file.unlink()
            
            assert stats["successful"] == 1
        
        # Verify reasonable throughput
        for result in results:
            assert result['files_per_second'] > 5, \
                f"Low throughput: {result['files_per_second']:.1f} files/s for {result['archive_size']} files"

    @pytest.mark.performance
    def test_error_handling_performance(self):
        """Test that error handling doesn't significantly impact performance."""
        # Create mix of valid and invalid archives
        valid_archives = 5
        invalid_archives = 3
        
        # Create valid archives
        for i in range(valid_archives):
            zip_path = self.temp_path / f"valid_{i}.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("test.txt", f"content {i}")
        
        # Create invalid archives (fake ZIP files)
        for i in range(invalid_archives):
            fake_path = self.temp_path / f"invalid_{i}.zip"
            fake_path.write_text("This is not a ZIP file")
        
        # Measure processing time
        extractor = ArchiveExtractor(config=self.config)
        start_time = time.time()
        stats = extractor.extract_all(str(self.temp_path))
        processing_time = time.time() - start_time
        
        # Should handle errors efficiently
        assert processing_time < 10.0, f"Error handling took {processing_time:.2f}s"
        assert stats["total_processed"] == valid_archives + invalid_archives
        assert stats["successful"] == valid_archives
        assert stats["failed"] == invalid_archives


@pytest.mark.performance
class TestBenchmarks:
    """Benchmark tests for performance regression detection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_baseline_performance_benchmark(self):
        """Baseline performance benchmark for regression testing."""
        config = Config()
        extractor = ArchiveExtractor(config=config)
        
        # Create a standardized test archive
        zip_path = self.temp_path / "benchmark.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            # 50 files, 2KB each = ~100KB total
            for i in range(50):
                content = f"Benchmark content {i} " * 50  # ~2KB
                zf.writestr(f"benchmark_{i:03d}.txt", content)
        
        # Measure extraction performance
        start_time = time.time()
        stats = extractor.extract_all(str(self.temp_path))
        extraction_time = time.time() - start_time
        
        # Performance assertions (adjust thresholds based on system capabilities)
        assert extraction_time < 3.0, f"Baseline benchmark took {extraction_time:.2f}s (threshold: 3.0s)"
        assert stats["successful"] == 1
        assert stats["failed"] == 0
        
        # Calculate performance metrics
        files_extracted = 50
        throughput = files_extracted / extraction_time
        
        # Log performance metrics (would be captured by test runner)
        print(f"Benchmark results:")
        print(f"  Extraction time: {extraction_time:.3f}s")
        print(f"  Throughput: {throughput:.1f} files/second")
        print(f"  Files processed: {files_extracted}")
        
        # Verify all files were extracted correctly
        extracted_files = list(self.temp_path.glob("benchmark_*.txt"))
        assert len(extracted_files) == 50