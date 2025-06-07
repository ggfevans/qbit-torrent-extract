"""Security-focused tests for archive extraction."""

import io
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

        # Create a large amount of repetitive data that compresses well
        data_size = int(1024 * compression_ratio)  # Size in bytes
        repetitive_data = "A" * data_size

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("large_file.txt", repetitive_data)

        return zip_path

    def test_zipbomb_detection_by_validator(self):
        """Test that validator detects zipbombs."""
        zipbomb_path = self.create_zipbomb(50.0)  # Should exceed ratio of 10.0

        result = self.validator.validate_archive(zipbomb_path)
        assert not result.is_valid
        assert "zipbomb" in result.error_message.lower()

    def test_zipbomb_detection_by_extractor(self):
        """Test that extractor refuses to extract zipbombs."""
        zipbomb_path = self.create_zipbomb(50.0)

        stats = self.extractor.extract_all(str(self.temp_path))
        assert stats["failed"] == 1
        assert any("zipbomb" in error.lower() for error in stats["errors"])

    def test_safe_archive_passes_zipbomb_check(self):
        """Test that normal archives pass zipbomb protection."""
        zip_path = self.temp_path / "safe.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("small_file.txt", "small content")

        result = self.validator.validate_archive(zip_path)
        assert result.is_valid

    def test_zipbomb_ratio_configuration(self):
        """Test that zipbomb ratio can be configured."""
        # Create archive with moderate compression
        zipbomb_path = self.create_zipbomb(15.0)

        # Should fail with strict ratio
        strict_config = Config(max_extraction_ratio=10.0)
        strict_validator = ArchiveValidator(strict_config)
        result = strict_validator.validate_archive(zipbomb_path)
        assert not result.is_valid

        # Should pass with lenient ratio
        lenient_config = Config(max_extraction_ratio=20.0)
        lenient_validator = ArchiveValidator(lenient_config)
        result = lenient_validator.validate_archive(zipbomb_path)
        assert result.is_valid


class TestNestedDepthProtection:
    """Test protection against excessive nesting depth."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.config = Config(max_nested_depth=3)
        self.extractor = ArchiveExtractor(config=self.config)
        self.validator = ArchiveValidator(self.config)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_deeply_nested_archives(self, depth: int) -> Path:
        """Create deeply nested archives for testing."""
        # Start with the innermost file
        current_path = self.temp_path / "innermost.txt"
        current_path.write_text("innermost content")

        # Create nested ZIP files
        for i in range(depth):
            zip_name = f"level_{depth - i}.zip"
            zip_path = self.temp_path / zip_name

            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.write(current_path, current_path.name)

            # Remove the previous file and use the ZIP as the new current file
            if current_path.suffix != ".txt":
                current_path.unlink()
            current_path = zip_path

        return current_path

    def test_excessive_nesting_detection(self):
        """Test detection of excessive nesting depth."""
        deep_archive = self.create_deeply_nested_archives(5)  # Exceeds limit of 3

        # Test with validator
        nested_paths = [deep_archive]
        for _ in range(5):  # Simulate nested extraction
            result = self.validator.check_nested_depth(nested_paths)
            if not result.is_valid:
                break
            nested_paths.append(deep_archive)  # Simulate going deeper

        # Should eventually fail
        result = self.validator.check_nested_depth(nested_paths)
        assert not result.is_valid
        assert "depth" in result.error_message.lower()

    def test_safe_nesting_depth(self):
        """Test that safe nesting depth is allowed."""
        shallow_archive = self.create_deeply_nested_archives(2)  # Within limit

        nested_paths = [shallow_archive, shallow_archive]  # 2 levels deep
        result = self.validator.check_nested_depth(nested_paths)
        assert result.is_valid

    def test_nesting_depth_configuration(self):
        """Test that nesting depth limit can be configured."""
        archive = self.create_deeply_nested_archives(3)

        # Should fail with strict depth limit
        strict_config = Config(max_nested_depth=2)
        strict_validator = ArchiveValidator(strict_config)
        nested_paths = [archive] * 3
        result = strict_validator.check_nested_depth(nested_paths)
        assert not result.is_valid

        # Should pass with lenient depth limit
        lenient_config = Config(max_nested_depth=5)
        lenient_validator = ArchiveValidator(lenient_config)
        result = lenient_validator.check_nested_depth(nested_paths)
        assert result.is_valid


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

    def create_malicious_zip(self) -> Path:
        """Create a ZIP with path traversal attempts."""
        zip_path = self.temp_path / "malicious.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            # Try to write outside the extraction directory
            zf.writestr("../../../etc/passwd", "malicious content")
            zf.writestr("..\\..\\windows\\system32\\config", "windows malicious")
            zf.writestr("normal_file.txt", "normal content")

        return zip_path

    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are prevented."""
        malicious_zip = self.create_malicious_zip()

        # Extract should complete but not create files outside directory
        stats = self.extractor.extract_all(str(self.temp_path))

        # Check that no files were created outside the temp directory
        sensitive_paths = [
            Path("/etc/passwd"),
            Path("C:\\windows\\system32\\config"),
            self.temp_path.parent / "etc" / "passwd",
        ]

        for path in sensitive_paths:
            assert not path.exists()

        # Normal file should still be extracted
        normal_file = self.temp_path / "normal_file.txt"
        assert normal_file.exists()
        assert normal_file.read_text() == "normal content"


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

    def create_corrupted_zip(self) -> Path:
        """Create a corrupted ZIP file."""
        zip_path = self.temp_path / "corrupted.zip"

        # Create a valid ZIP first
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test.txt", "test content")

        # Corrupt the file by truncating it
        with open(zip_path, "r+b") as f:
            f.seek(0, 2)  # Go to end
            size = f.tell()
            f.truncate(size // 2)  # Truncate to half size

        return zip_path

    def create_fake_zip(self) -> Path:
        """Create a file with .zip extension but invalid content."""
        fake_zip = self.temp_path / "fake.zip"
        fake_zip.write_text("This is not a ZIP file")
        return fake_zip

    def test_corrupted_zip_detection(self):
        """Test detection of corrupted ZIP files."""
        corrupted_zip = self.create_corrupted_zip()

        result = self.validator.validate_archive(corrupted_zip)
        assert not result.is_valid
        assert "corrupt" in result.error_message.lower() or "invalid" in result.error_message.lower()

    def test_fake_archive_detection(self):
        """Test detection of files with wrong extensions."""
        fake_zip = self.create_fake_zip()

        result = self.validator.validate_archive(fake_zip)
        assert not result.is_valid

    def test_corrupted_archive_skipping(self):
        """Test that corrupted archives are skipped gracefully."""
        corrupted_zip = self.create_corrupted_zip()
        
        # Also create a valid archive
        valid_zip = self.temp_path / "valid.zip"
        with zipfile.ZipFile(valid_zip, "w") as zf:
            zf.writestr("valid.txt", "valid content")

        stats = self.extractor.extract_all(str(self.temp_path))

        # Should have processed both, but failed on corrupted one
        assert stats["total_processed"] == 2
        assert stats["failed"] == 1
        assert stats["successful"] == 1

        # Valid file should be extracted
        assert (self.temp_path / "valid.txt").exists()


class TestPasswordProtectedArchives:
    """Test handling of password-protected archives."""

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

    def create_password_protected_zip(self) -> Path:
        """Create a password-protected ZIP file."""
        zip_path = self.temp_path / "protected.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("secret.txt", "secret content")
            zf.setpassword(b"password123")

        return zip_path

    def test_password_protected_detection(self):
        """Test detection of password-protected archives."""
        protected_zip = self.create_password_protected_zip()

        # The validation might succeed as structure is valid,
        # but extraction should fail and be handled gracefully
        stats = self.extractor.extract_all(str(self.temp_path))

        # Should detect and skip password-protected archive
        assert stats["total_processed"] == 1
        assert stats["failed"] == 1 or stats["skipped"] == 1


class TestResourceExhaustionProtection:
    """Test protection against resource exhaustion attacks."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.config = Config()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_large_number_of_files(self):
        """Test handling of archives with many small files."""
        zip_path = self.temp_path / "many_files.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            # Create many small files
            for i in range(1000):
                zf.writestr(f"file_{i:04d}.txt", f"content {i}")

        extractor = ArchiveExtractor(config=self.config)
        stats = extractor.extract_all(str(self.temp_path))

        # Should handle gracefully (may succeed or fail based on system limits)
        assert stats["total_processed"] == 1
        # Don't assert success/failure as this depends on system resources

    def test_deeply_nested_directories(self):
        """Test handling of deeply nested directory structures."""
        zip_path = self.temp_path / "deep_dirs.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            # Create deeply nested directory structure
            deep_path = "/".join([f"dir_{i}" for i in range(100)])
            zf.writestr(f"{deep_path}/deep_file.txt", "deep content")

        extractor = ArchiveExtractor(config=self.config)
        stats = extractor.extract_all(str(self.temp_path))

        # Should handle gracefully
        assert stats["total_processed"] == 1


class TestSecurityIntegration:
    """Integration tests for multiple security features."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.config = Config(max_extraction_ratio=10.0, max_nested_depth=3)
        self.extractor = ArchiveExtractor(config=self.config)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_mixed_safe_and_dangerous_archives(self):
        """Test processing directory with both safe and dangerous archives."""
        # Create a safe archive
        safe_zip = self.temp_path / "safe.zip"
        with zipfile.ZipFile(safe_zip, "w") as zf:
            zf.writestr("safe.txt", "safe content")

        # Create a zipbomb
        zipbomb_zip = self.temp_path / "zipbomb.zip"
        large_data = "A" * (1024 * 50)  # Should exceed ratio of 10.0
        with zipfile.ZipFile(zipbomb_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("large.txt", large_data)

        # Create a corrupted archive
        corrupted_zip = self.temp_path / "corrupted.zip"
        corrupted_zip.write_bytes(b"invalid zip data")

        # Process all archives
        stats = self.extractor.extract_all(str(self.temp_path))

        # Should process all three but only succeed on the safe one
        assert stats["total_processed"] == 3
        assert stats["successful"] == 1
        assert stats["failed"] == 2

        # Safe file should be extracted
        assert (self.temp_path / "safe.txt").exists()

    def test_security_with_verbose_logging(self):
        """Test that security violations are properly logged."""
        # This test would require checking log output
        # For now, ensure the extractor handles security issues gracefully
        
        # Create zipbomb
        zipbomb_zip = self.temp_path / "zipbomb.zip"
        large_data = "A" * (1024 * 50)
        with zipfile.ZipFile(zipbomb_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("large.txt", large_data)

        stats = self.extractor.extract_all(str(self.temp_path))
        
        # Should have security-related error messages
        assert stats["failed"] == 1
        assert len(stats["errors"]) > 0
        assert any("zipbomb" in error.lower() or "ratio" in error.lower() 
                  for error in stats["errors"])