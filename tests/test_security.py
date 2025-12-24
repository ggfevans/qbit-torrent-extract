"""Security-focused tests for archive extraction."""

import tempfile
import zipfile
from pathlib import Path

import pytest

from qbit_torrent_extract.config import Config
from qbit_torrent_extract.extractor import ArchiveExtractor
from qbit_torrent_extract.validator import ArchiveValidator


class TestZipbombProtection:
    """Test protection against zipbomb attacks."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.config = Config(max_extraction_ratio=10.0)  # Low ratio for testing
        self.extractor = ArchiveExtractor(config=self.config)
        self.validator = ArchiveValidator(self.config)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_zipbomb(self, compression_ratio: float = 100.0) -> Path:
        """Create a zipbomb-like archive for testing."""
        zip_path = self.temp_path / "zipbomb.zip"
        data_size = int(1024 * compression_ratio)
        repetitive_data = "A" * data_size

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("large_file.txt", repetitive_data)

        return zip_path

    def test_zipbomb_detection_by_validator(self):
        """Test that validator detects high extraction ratios."""
        zipbomb_path = self.create_zipbomb(50.0)

        result = self.validator.validate_archive(zipbomb_path)
        assert not result.is_valid
        assert "ratio" in result.error_message.lower()

    def test_zipbomb_detection_by_extractor(self):
        """Test that extractor refuses to extract high-ratio archives."""
        zipbomb_path = self.create_zipbomb(50.0)

        stats = self.extractor.extract_all(str(self.temp_path))
        assert stats["failed"] == 1
        assert any("ratio" in error.lower() for error in stats["errors"])

    def test_safe_archive_passes_check(self):
        """Test that normal archives pass validation."""
        zip_path = self.temp_path / "safe.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("small_file.txt", "small content")

        result = self.validator.validate_archive(zip_path)
        assert result.is_valid

    def test_extraction_ratio_configuration(self):
        """Test that extraction ratio limit can be configured."""
        # Create archive with high compression
        zip_path = self.temp_path / "compressed.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("data.txt", "A" * 10000)  # Highly compressible

        # Should fail with strict ratio (10.0)
        strict_config = Config(max_extraction_ratio=10.0)
        strict_validator = ArchiveValidator(strict_config)
        result = strict_validator.validate_archive(zip_path)
        assert not result.is_valid

        # Should pass with lenient ratio (1000.0)
        lenient_config = Config(max_extraction_ratio=1000.0)
        lenient_validator = ArchiveValidator(lenient_config)
        result = lenient_validator.validate_archive(zip_path)
        assert result.is_valid


class TestNestedDepthProtection:
    """Test protection against excessive nesting depth."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.config = Config(max_nested_depth=2)
        self.extractor = ArchiveExtractor(config=self.config)
        self.validator = ArchiveValidator(self.config)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_nested_zip(self, depth: int) -> Path:
        """Create nested ZIP archives."""
        # Create innermost content
        inner_content = self.temp_path / "content.txt"
        inner_content.write_text("innermost")

        current = inner_content
        for i in range(depth):
            zip_path = self.temp_path / f"level{i}.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.write(current, current.name)
            if current != inner_content:
                current.unlink()
            current = zip_path

        inner_content.unlink()
        return current

    def test_nested_depth_check(self):
        """Test nested depth checking on a single archive."""
        nested_zip = self.create_nested_zip(3)

        # Check depth at level 0 - should be within limit
        within_limit, depth = self.validator.check_nested_depth(nested_zip, 0)
        assert within_limit
        assert depth >= 1

    def test_nested_depth_limit_enforcement(self):
        """Test that nested depth limit is enforced during extraction."""
        # Create deeply nested structure
        nested_zip = self.create_nested_zip(5)

        # Extract with max_nested_depth=2
        stats = self.extractor.extract_all(str(self.temp_path))

        # Should process some but hit depth limit
        assert stats["total_processed"] >= 1

    def test_nesting_depth_configuration(self):
        """Test that nesting depth limit can be configured."""
        nested_zip = self.create_nested_zip(2)

        # Should pass with depth limit of 3
        config = Config(max_nested_depth=3)
        validator = ArchiveValidator(config)
        within_limit, _ = validator.check_nested_depth(nested_zip, 0)
        assert within_limit


class TestPathTraversalProtection:
    """Test protection against path traversal attacks."""

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

    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are blocked."""
        zip_path = self.temp_path / "malicious.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("../escape.txt", "escaped content")
            zf.writestr("normal.txt", "normal content")

        stats = self.extractor.extract_all(str(self.temp_path))

        # Normal file should be extracted
        assert (self.temp_path / "normal.txt").exists()

        # Escaped file should NOT exist in parent directory
        escaped = self.temp_path.parent / "escape.txt"
        assert not escaped.exists()


class TestCorruptedArchiveHandling:
    """Test handling of corrupted archives."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.config = Config()
        self.extractor = ArchiveExtractor(config=self.config)
        self.validator = ArchiveValidator(self.config)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_corrupted_zip_detection(self):
        """Test detection of corrupted ZIP files."""
        zip_path = self.temp_path / "corrupted.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test.txt", "content")

        # Corrupt by truncating
        with open(zip_path, "r+b") as f:
            f.truncate(f.seek(0, 2) // 2)

        result = self.validator.validate_archive(zip_path)
        assert not result.is_valid

    def test_fake_archive_detection(self):
        """Test detection of fake archives."""
        fake_zip = self.temp_path / "fake.zip"
        fake_zip.write_text("not a zip")

        result = self.validator.validate_archive(fake_zip)
        assert not result.is_valid

    def test_corrupted_archive_skipping(self):
        """Test that corrupted archives are skipped gracefully."""
        # Create corrupted archive
        corrupted = self.temp_path / "corrupted.zip"
        corrupted.write_bytes(b"invalid zip data")

        # Create valid archive
        valid = self.temp_path / "valid.zip"
        with zipfile.ZipFile(valid, "w") as zf:
            zf.writestr("valid.txt", "content")

        stats = self.extractor.extract_all(str(self.temp_path))

        assert stats["failed"] == 1
        assert stats["successful"] == 1
        assert (self.temp_path / "valid.txt").exists()


class TestResourceExhaustionProtection:
    """Test protection against resource exhaustion."""

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

    def test_large_number_of_files(self):
        """Test handling of archives with many files."""
        zip_path = self.temp_path / "many_files.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for i in range(100):
                zf.writestr(f"file_{i}.txt", f"content {i}")

        stats = self.extractor.extract_all(str(self.temp_path))
        assert stats["successful"] == 1

    def test_deeply_nested_directories(self):
        """Test handling of deeply nested directory structures."""
        zip_path = self.temp_path / "nested_dirs.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            deep_path = "/".join(["dir"] * 20) + "/file.txt"
            zf.writestr(deep_path, "deep content")

        stats = self.extractor.extract_all(str(self.temp_path))
        assert stats["successful"] == 1


class TestSecurityIntegration:
    """Integration tests for security features."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_mixed_safe_and_dangerous_archives(self):
        """Test processing mix of safe and dangerous archives."""
        config = Config(max_extraction_ratio=10.0)
        extractor = ArchiveExtractor(config=config)

        # Safe archive
        safe = self.temp_path / "safe.zip"
        with zipfile.ZipFile(safe, "w") as zf:
            zf.writestr("safe.txt", "safe")

        # "Dangerous" (high ratio) archive
        dangerous = self.temp_path / "dangerous.zip"
        with zipfile.ZipFile(dangerous, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("bomb.txt", "A" * 50000)

        stats = extractor.extract_all(str(self.temp_path))

        assert stats["successful"] >= 1
        assert (self.temp_path / "safe.txt").exists()

    def test_security_with_verbose_logging(self):
        """Test that security checks work with logging enabled."""
        from qbit_torrent_extract.logger import setup_logging

        setup_logging(level="DEBUG", log_dir=str(self.temp_path / "logs"))

        config = Config(max_extraction_ratio=10.0)
        extractor = ArchiveExtractor(config=config)

        zip_path = self.temp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test.txt", "content")

        stats = extractor.extract_all(str(self.temp_path))
        assert stats["successful"] == 1
