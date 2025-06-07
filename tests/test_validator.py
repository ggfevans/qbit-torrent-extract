"""Tests for archive validation."""

import pytest
import tempfile
import zipfile
import tarfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from qbit_torrent_extract.validator import ArchiveValidator, ValidationResult
from qbit_torrent_extract.config import Config


class TestArchiveValidator:
    """Test archive validation functionality."""

    @pytest.fixture
    def validator(self):
        """Create a validator with test configuration."""
        config = Config(max_extraction_ratio=10.0, max_nested_depth=3)
        return ArchiveValidator(config)

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def create_test_zip(
        self, path: Path, files: dict, compression=zipfile.ZIP_DEFLATED
    ):
        """Create a test ZIP file with specified contents."""
        with zipfile.ZipFile(path, "w", compression=compression) as zf:
            for filename, content in files.items():
                zf.writestr(filename, content)

    def create_test_tar(self, path: Path, files: dict, compressed=False):
        """Create a test TAR file with specified contents."""
        mode = "w:gz" if compressed else "w"
        with tarfile.open(path, mode) as tf:
            for filename, content in files.items():
                info = tarfile.TarInfo(filename)
                info.size = len(content.encode())
                import io

                tf.addfile(info, fileobj=io.BytesIO(content.encode()))

    def test_detect_archive_type(self, validator):
        """Test archive type detection."""
        assert validator.detect_archive_type(Path("test.zip")) == "zip"
        assert validator.detect_archive_type(Path("test.rar")) == "rar"
        assert validator.detect_archive_type(Path("test.7z")) == "7z"
        assert validator.detect_archive_type(Path("test.tar")) == "tar"
        assert validator.detect_archive_type(Path("test.tar.gz")) == "tar.gz"
        assert validator.detect_archive_type(Path("test.tgz")) == "tar.gz"
        assert validator.detect_archive_type(Path("test.gz")) == "gz"
        assert validator.detect_archive_type(Path("test.txt")) is None

    def test_validate_nonexistent_file(self, validator):
        """Test validation of non-existent file."""
        result = validator.validate_archive(Path("/nonexistent/file.zip"))
        assert not result.is_valid
        assert "not found" in result.error_message

    def test_validate_unsupported_type(self, validator, temp_dir):
        """Test validation of unsupported file type."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("not an archive")

        result = validator.validate_archive(test_file)
        assert not result.is_valid
        assert "Unsupported archive type" in result.error_message

    def test_validate_valid_zip(self, validator, temp_dir):
        """Test validation of valid ZIP file."""
        zip_path = temp_dir / "test.zip"
        self.create_test_zip(
            zip_path,
            {"file1.txt": "Hello World" * 10, "file2.txt": "Test content" * 10},
        )

        result = validator.validate_archive(zip_path)
        assert result.is_valid
        assert result.archive_type == "zip"
        assert result.file_count == 2
        assert result.extraction_ratio > 0

    def test_validate_corrupted_zip(self, validator, temp_dir):
        """Test validation of corrupted ZIP file."""
        zip_path = temp_dir / "corrupted.zip"

        # Create corrupted ZIP by writing invalid data
        with open(zip_path, "wb") as f:
            f.write(b"PK\x03\x04" + b"corrupted data")

        result = validator.validate_archive(zip_path)
        assert not result.is_valid
        assert "Invalid ZIP file" in result.error_message

    def test_validate_zipbomb(self, validator, temp_dir):
        """Test detection of potential zipbomb."""
        zip_path = temp_dir / "bomb.zip"

        # Create a file with high compression ratio
        large_content = "0" * 1000000  # 1MB of zeros compresses very well
        self.create_test_zip(zip_path, {"large.txt": large_content})

        # Use a validator with low ratio limit
        strict_config = Config(max_extraction_ratio=5.0)
        strict_validator = ArchiveValidator(strict_config)

        result = strict_validator.validate_archive(zip_path)
        assert not result.is_valid
        assert "exceeds limit" in result.error_message
        assert result.extraction_ratio > 5.0

    @patch("rarfile.RarFile")
    def test_validate_valid_rar(self, mock_rar_class, validator, temp_dir):
        """Test validation of valid RAR file."""
        rar_path = temp_dir / "test.rar"
        rar_path.touch()  # Create the file

        # Mock RAR file
        mock_rar = MagicMock()
        mock_rar_class.return_value.__enter__.return_value = mock_rar
        mock_rar.needs_password.return_value = False

        # Mock file info
        mock_info1 = MagicMock()
        mock_info1.file_size = 100
        mock_info1.compress_size = 50

        mock_info2 = MagicMock()
        mock_info2.file_size = 200
        mock_info2.compress_size = 100

        mock_rar.infolist.return_value = [mock_info1, mock_info2]

        result = validator.validate_archive(rar_path)
        assert result.is_valid
        assert result.archive_type == "rar"
        assert result.file_count == 2
        assert result.total_size == 300
        assert result.compressed_size == 150
        assert result.extraction_ratio == 2.0

    @patch("rarfile.RarFile")
    def test_validate_password_protected_rar(self, mock_rar_class, validator, temp_dir):
        """Test validation of password-protected RAR file."""
        rar_path = temp_dir / "protected.rar"
        rar_path.touch()  # Create the file

        # Mock password-protected RAR
        mock_rar = MagicMock()
        mock_rar_class.return_value.__enter__.return_value = mock_rar
        mock_rar.needs_password.return_value = True

        result = validator.validate_archive(rar_path)
        assert not result.is_valid
        assert "Password protected" in result.error_message

    def test_validate_valid_tar(self, validator, temp_dir):
        """Test validation of valid TAR file."""
        tar_path = temp_dir / "test.tar"

        with tarfile.open(tar_path, "w") as tf:
            # Add test files
            import io

            for i in range(3):
                data = f"Test content {i}" * 10
                info = tarfile.TarInfo(f"file{i}.txt")
                info.size = len(data.encode())
                tf.addfile(info, fileobj=io.BytesIO(data.encode()))

        result = validator.validate_archive(tar_path)
        assert result.is_valid
        assert result.archive_type == "tar"
        assert result.file_count == 3

    def test_validate_valid_tar_gz(self, validator, temp_dir):
        """Test validation of valid TAR.GZ file."""
        tar_path = temp_dir / "test.tar.gz"

        with tarfile.open(tar_path, "w:gz") as tf:
            # Add test file
            import io

            data = "Test content" * 100
            info = tarfile.TarInfo("test.txt")
            info.size = len(data.encode())
            tf.addfile(info, fileobj=io.BytesIO(data.encode()))

        result = validator.validate_archive(tar_path)
        assert result.is_valid
        assert result.archive_type == "tar.gz"
        assert result.file_count == 1

    def test_validate_7z_not_implemented(self, validator, temp_dir):
        """Test that 7z validation returns proper error for invalid file."""
        path_7z = temp_dir / "test.7z"
        path_7z.touch()

        result = validator.validate_archive(path_7z)
        assert not result.is_valid
        assert "Invalid 7z file" in result.error_message

    def test_scan_directory(self, validator, temp_dir):
        """Test scanning directory for archives."""
        # Create various archive files
        self.create_test_zip(temp_dir / "test1.zip", {"file1.txt": "content1"})
        self.create_test_zip(temp_dir / "test2.zip", {"file2.txt": "content2"})

        # Create a non-archive file
        (temp_dir / "readme.txt").write_text("Not an archive")

        # Create nested directory with archive
        nested_dir = temp_dir / "nested"
        nested_dir.mkdir()
        self.create_test_zip(
            nested_dir / "nested.zip", {"nested.txt": "nested content"}
        )

        results = validator.scan_directory(temp_dir)

        # Should find all ZIP files
        assert len(results) == 3
        assert all(result.is_valid for result in results.values())
        assert all(result.archive_type == "zip" for result in results.values())

    def test_check_nested_depth(self, validator, temp_dir):
        """Test nested depth checking."""
        # Create a nested ZIP structure
        inner_zip = temp_dir / "inner.zip"
        self.create_test_zip(inner_zip, {"file.txt": "content"})

        # Create outer ZIP containing inner ZIP
        import io

        outer_zip = temp_dir / "outer.zip"
        with zipfile.ZipFile(outer_zip, "w") as zf:
            zf.writestr("inner.zip", inner_zip.read_bytes())

        # Check depth of outer ZIP
        within_limit, depth = validator.check_nested_depth(outer_zip, 0)
        assert within_limit
        assert depth == 1  # Contains one nested archive

        # Test at limit
        within_limit, depth = validator.check_nested_depth(outer_zip, 2)
        assert not within_limit  # Would exceed limit if extracted
        assert depth == 3

    def test_check_nested_depth_complex(self, validator, temp_dir):
        """Test nested depth checking with multiple nested archives."""
        # Create deeply nested structure
        zip1 = temp_dir / "level1.zip"
        self.create_test_zip(zip1, {"data.txt": "level 1 data"})

        zip2 = temp_dir / "level2.zip"
        with zipfile.ZipFile(zip2, "w") as zf:
            zf.writestr("level1.zip", zip1.read_bytes())
            zf.writestr("another.rar", b"fake rar")  # Multiple archives at same level

        # Check with strict depth limit
        strict_config = Config(max_nested_depth=2)
        strict_validator = ArchiveValidator(strict_config)

        within_limit, depth = strict_validator.check_nested_depth(zip2, 0)
        assert within_limit
        assert depth == 1
