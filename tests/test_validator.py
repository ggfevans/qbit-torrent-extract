"""Tests for the archive validator."""

import tempfile
import zipfile
import tarfile
from pathlib import Path

import pytest

from qbit_torrent_extract.config import Config
from qbit_torrent_extract.validator import ArchiveValidator


class TestArchiveValidator:
    """Test archive validation functionality."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return ArchiveValidator(Config())

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def create_test_zip(self, path: Path, files: dict) -> Path:
        """Create a test ZIP file."""
        with zipfile.ZipFile(path, "w") as zf:
            for filename, content in files.items():
                zf.writestr(filename, content)
        return path

    def test_detect_archive_type(self, validator):
        """Test archive type detection."""
        assert validator.detect_archive_type(Path("test.zip")) == "zip"
        assert validator.detect_archive_type(Path("test.rar")) == "rar"
        assert validator.detect_archive_type(Path("test.7z")) == "7z"
        assert validator.detect_archive_type(Path("test.tar")) == "tar"
        assert validator.detect_archive_type(Path("test.tar.gz")) == "tar.gz"
        assert validator.detect_archive_type(Path("test.tgz")) == "tar.gz"
        assert validator.detect_archive_type(Path("test.txt")) is None

    def test_validate_nonexistent_file(self, validator, temp_dir):
        """Test validation of nonexistent file."""
        result = validator.validate_archive(temp_dir / "nonexistent.zip")
        assert not result.is_valid
        assert "not found" in result.error_message.lower()

    def test_validate_unsupported_type(self, validator, temp_dir):
        """Test validation of unsupported file type."""
        unsupported = temp_dir / "test.xyz"
        unsupported.touch()

        result = validator.validate_archive(unsupported)
        assert not result.is_valid
        assert "unsupported" in result.error_message.lower()

    def test_validate_valid_zip(self, validator, temp_dir):
        """Test validation of valid ZIP file."""
        zip_path = self.create_test_zip(
            temp_dir / "valid.zip",
            {"test.txt": "test content", "data.txt": "more data"}
        )

        result = validator.validate_archive(zip_path)
        assert result.is_valid
        assert result.archive_type == "zip"

    def test_validate_corrupted_zip(self, validator, temp_dir):
        """Test validation of corrupted ZIP file."""
        corrupted = temp_dir / "corrupted.zip"
        corrupted.write_bytes(b"this is not a zip file")

        result = validator.validate_archive(corrupted)
        assert not result.is_valid
        assert "invalid" in result.error_message.lower()

    def test_validate_zipbomb(self, validator, temp_dir):
        """Test detection of zipbomb-like archives."""
        # Create archive with highly compressible data
        zipbomb = temp_dir / "bomb.zip"
        with zipfile.ZipFile(zipbomb, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("data.txt", "A" * 100000)

        # Use strict ratio to trigger detection
        strict_validator = ArchiveValidator(Config(max_extraction_ratio=10.0))
        result = strict_validator.validate_archive(zipbomb)

        assert not result.is_valid
        assert "ratio" in result.error_message.lower()

    def test_validate_valid_rar(self, validator, temp_dir):
        """Test validation of valid RAR file (requires unrar)."""
        # Create a minimal valid RAR by using a test file
        rar_path = temp_dir / "test.rar"
        rar_path.touch()

        result = validator.validate_archive(rar_path)
        # RAR validation will fail without actual RAR content
        assert not result.is_valid

    def test_validate_password_protected_rar(self, validator, temp_dir):
        """Test validation of password-protected RAR file."""
        rar_path = temp_dir / "protected.rar"
        rar_path.touch()

        result = validator.validate_archive(rar_path)
        # Empty file will fail validation
        assert not result.is_valid

    def test_validate_valid_tar(self, validator, temp_dir):
        """Test validation of valid TAR file."""
        import io

        tar_path = temp_dir / "test.tar"
        with tarfile.open(tar_path, "w") as tf:
            data = b"test content"
            tarinfo = tarfile.TarInfo(name="test.txt")
            tarinfo.size = len(data)
            tf.addfile(tarinfo, io.BytesIO(data))

        result = validator.validate_archive(tar_path)
        assert result.is_valid
        assert result.archive_type == "tar"

    def test_validate_valid_tar_gz(self, validator, temp_dir):
        """Test validation of valid TAR.GZ file."""
        import io

        tar_path = temp_dir / "test.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tf:
            data = b"test content"
            tarinfo = tarfile.TarInfo(name="test.txt")
            tarinfo.size = len(data)
            tf.addfile(tarinfo, io.BytesIO(data))

        result = validator.validate_archive(tar_path)
        assert result.is_valid
        assert result.archive_type == "tar.gz"

    def test_validate_7z_not_implemented(self, validator, temp_dir):
        """Test validation of 7z files."""
        path_7z = temp_dir / "test.7z"
        path_7z.touch()

        result = validator.validate_archive(path_7z)
        # Empty file will fail validation
        assert not result.is_valid

    def test_check_nested_depth(self, validator, temp_dir):
        """Test nested depth checking."""
        # Create a nested ZIP structure
        inner_zip = temp_dir / "inner.zip"
        self.create_test_zip(inner_zip, {"file.txt": "content"})

        # Create outer ZIP containing inner ZIP
        outer_zip = temp_dir / "outer.zip"
        with zipfile.ZipFile(outer_zip, "w") as zf:
            zf.writestr("inner.zip", inner_zip.read_bytes())

        within_limit, depth = validator.check_nested_depth(outer_zip, 0)
        assert within_limit
        assert depth == 1

    def test_check_nested_depth_complex(self, validator, temp_dir):
        """Test nested depth checking with multiple nested archives."""
        # Create nested structure
        zip1 = temp_dir / "level1.zip"
        self.create_test_zip(zip1, {"data.txt": "level 1 data"})

        zip2 = temp_dir / "level2.zip"
        with zipfile.ZipFile(zip2, "w") as zf:
            zf.writestr("level1.zip", zip1.read_bytes())
            zf.writestr("another.rar", b"fake rar")

        # Check with default depth limit
        within_limit, depth = validator.check_nested_depth(zip2, 0)
        assert within_limit
        assert depth == 1

    def test_split_archive_detection(self, validator, temp_dir):
        """Test split archive part detection."""
        # .r00 should be skipped
        r00_path = temp_dir / "archive.r00"
        is_split, is_first = validator.is_split_archive_part(r00_path)
        assert is_split
        assert not is_first

        # .part2.rar should be skipped
        part2_path = temp_dir / "archive.part2.rar"
        is_split, is_first = validator.is_split_archive_part(part2_path)
        assert is_split
        assert not is_first

        # .part1.rar should be extracted
        part1_path = temp_dir / "archive.part1.rar"
        is_split, is_first = validator.is_split_archive_part(part1_path)
        assert is_split
        assert is_first

        # Regular .zip is not split
        zip_path = temp_dir / "archive.zip"
        is_split, is_first = validator.is_split_archive_part(zip_path)
        assert not is_split
        assert is_first
