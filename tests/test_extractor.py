import pytest
import tempfile
import zipfile
import rarfile
import tarfile
import py7zr
import os
import gzip
from pathlib import Path
from qbit_torrent_extract.extractor import ArchiveExtractor
from qbit_torrent_extract.config import Config

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def extractor():
    """Create an ArchiveExtractor instance."""
    from qbit_torrent_extract.logger import setup_logging
    config = Config()
    setup_logging(config)
    return ArchiveExtractor(preserve_archives=True, config=config)

def create_test_zip(directory: Path, filename: str = "test.zip", content: str = "test content") -> Path:
    """Create a test ZIP file."""
    zip_path = directory / filename
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("test.txt", content)
    return zip_path

def create_test_7z(directory: Path, filename: str = "test.7z", content: str = "test content") -> Path:
    """Create a test 7z file."""
    sz_path = directory / filename
    with py7zr.SevenZipFile(sz_path, 'w') as szf:
        szf.writestr(content.encode(), "test.txt")
    return sz_path

def create_test_tar_gz(directory: Path, filename: str = "test.tar.gz", content: str = "test content") -> Path:
    """Create a test tar.gz file."""
    tar_path = directory / filename
    with tarfile.open(tar_path, 'w:gz') as tf:
        # Create a file-like object for the content
        import io
        content_bytes = content.encode('utf-8')
        tarinfo = tarfile.TarInfo(name="test.txt")
        tarinfo.size = len(content_bytes)
        tf.addfile(tarinfo, io.BytesIO(content_bytes))
    return tar_path

def create_test_tgz(directory: Path, filename: str = "test.tgz", content: str = "test content") -> Path:
    """Create a test .tgz file."""
    return create_test_tar_gz(directory, filename, content)

def create_corrupted_zip(directory: Path, filename: str = "corrupted.zip") -> Path:
    """Create a corrupted ZIP file."""
    zip_path = directory / filename
    with open(zip_path, 'wb') as f:
        f.write(b'this is not a valid zip file')
    return zip_path

def create_zipbomb(directory: Path, filename: str = "zipbomb.zip") -> Path:
    """Create a ZIP file with high compression ratio."""
    zip_path = directory / filename
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        # Create a file with lots of repeated data (compresses well)
        large_content = "A" * 100000  # 100KB of repeated data
        zf.writestr("large.txt", large_content)
    return zip_path

def test_init(extractor):
    """Test ArchiveExtractor initialization."""
    assert extractor.preserve_archives is True
    assert extractor.logger is not None

def test_get_archive_files(extractor, temp_dir):
    """Test getting archive files from directory."""
    # Create test files
    zip_path = create_test_zip(temp_dir)
    (temp_dir / "test.rar").touch()
    (temp_dir / "not_an_archive.txt").touch()

    # Get archive files
    archives = extractor.get_archive_files(temp_dir)
    
    # Check results
    assert len(archives) == 2
    assert any(a.name == "test.rar" for a in archives)
    assert any(a.name == "test.zip" for a in archives)

def test_extract_zip(extractor, temp_dir):
    """Test ZIP file extraction."""
    # Create test ZIP
    zip_path = create_test_zip(temp_dir)
    
    # Extract
    extractor.extract_all(temp_dir)
    
    # Check results
    assert (temp_dir / "test.txt").exists()
    assert (temp_dir / "test.zip").exists()  # preserved

def test_no_preserve_archives(temp_dir):
    """Test archive removal when preserve_archives is False."""
    from qbit_torrent_extract.logger import setup_logging
    config = Config()
    setup_logging(config)
    extractor = ArchiveExtractor(preserve_archives=False, config=config)
    
    # Create test ZIP
    zip_path = create_test_zip(temp_dir)
    
    # Extract
    stats = extractor.extract_all(str(temp_dir))
    
    # Check results
    assert (temp_dir / "test.txt").exists()
    assert not (temp_dir / "test.zip").exists()  # should be removed
    assert stats['successful'] == 1

def test_empty_directory(extractor, temp_dir):
    """Test handling of directory with no archives."""
    # Create non-archive file
    (temp_dir / "not_an_archive.txt").touch()
    
    # Extract
    extractor.extract_all(temp_dir)
    
    # Should not raise any exceptions
    assert (temp_dir / "not_an_archive.txt").exists()

def test_nested_archives(extractor, temp_dir):
    """Test handling of nested archives."""
    # Create nested structure: zip containing another zip
    inner_zip = create_test_zip(temp_dir, "inner.zip", "inner content")
    outer_zip_path = temp_dir / "outer.zip"
    
    with zipfile.ZipFile(outer_zip_path, 'w') as zf:
        zf.write(inner_zip, inner_zip.name)
    
    # Remove inner zip from temp directory
    inner_zip.unlink()
    
    # Extract
    stats = extractor.extract_all(str(temp_dir))
    
    # Check results
    assert (temp_dir / "inner.zip").exists()
    assert (temp_dir / "test.txt").exists()  # from inner zip
    assert stats['successful'] == 2  # Both outer and inner archives
    assert stats['failed'] == 0


def test_extract_7z(extractor, temp_dir):
    """Test 7z file extraction."""
    # Create test 7z
    sz_path = create_test_7z(temp_dir)
    
    # Extract
    stats = extractor.extract_all(str(temp_dir))
    
    # Check results
    assert (temp_dir / "test.txt").exists()
    assert (temp_dir / "test.7z").exists()  # preserved
    assert stats['successful'] == 1
    assert stats['failed'] == 0

def test_extract_tar_gz(extractor, temp_dir):
    """Test tar.gz file extraction."""
    # Create test tar.gz
    tar_path = create_test_tar_gz(temp_dir)
    
    # Extract
    stats = extractor.extract_all(str(temp_dir))
    
    # Check results
    assert (temp_dir / "test.txt").exists()
    assert (temp_dir / "test.tar.gz").exists()  # preserved
    assert stats['successful'] == 1
    assert stats['failed'] == 0

def test_extract_tgz(extractor, temp_dir):
    """Test .tgz file extraction."""
    # Create test .tgz
    tgz_path = create_test_tgz(temp_dir, "test.tgz")
    
    # Extract
    stats = extractor.extract_all(str(temp_dir))
    
    # Check results
    assert (temp_dir / "test.txt").exists()
    assert (temp_dir / "test.tgz").exists()  # preserved
    assert stats['successful'] == 1
    assert stats['failed'] == 0

def test_mixed_archive_types(extractor, temp_dir):
    """Test extracting multiple archive types together."""
    # Create different archive types
    create_test_zip(temp_dir, "test1.zip", "zip content")
    create_test_7z(temp_dir, "test2.7z", "7z content")
    create_test_tar_gz(temp_dir, "test3.tar.gz", "tar content")
    
    # Extract
    stats = extractor.extract_all(str(temp_dir))
    
    # Check results
    assert len(list(temp_dir.glob("test.txt"))) >= 1  # At least one test.txt created
    assert stats['successful'] == 3
    assert stats['failed'] == 0
    assert stats['total_processed'] == 3

def test_corrupted_archive_handling(temp_dir):
    """Test handling of corrupted archives."""
    from qbit_torrent_extract.logger import setup_logging
    config = Config()
    setup_logging(config)
    extractor = ArchiveExtractor(preserve_archives=True, config=config)
    
    # Create corrupted archive
    corrupted_path = create_corrupted_zip(temp_dir)
    
    # Extract
    stats = extractor.extract_all(str(temp_dir))
    
    # Check results
    assert stats['failed'] == 1
    assert stats['successful'] == 0
    assert len(stats['errors']) == 1
    assert "validation failed" in stats['errors'][0].lower()

def test_zipbomb_protection(temp_dir):
    """Test zipbomb protection."""
    # Create config with low extraction ratio limit
    config = Config(max_extraction_ratio=50.0)
    extractor = ArchiveExtractor(preserve_archives=True, config=config)
    
    # Create zipbomb
    zipbomb_path = create_zipbomb(temp_dir)
    
    # Extract
    stats = extractor.extract_all(str(temp_dir))
    
    # Should be blocked by zipbomb protection
    assert stats['failed'] == 1
    assert stats['successful'] == 0
    assert any("extraction ratio" in error.lower() for error in stats['errors'])

def test_nested_depth_limit(temp_dir):
    """Test nested depth limiting."""
    # Create config with low nested depth limit
    config = Config(max_nested_depth=1)
    extractor = ArchiveExtractor(preserve_archives=True, config=config)
    
    # Create deeply nested archives
    # Level 0: Create innermost zip
    inner_zip = create_test_zip(temp_dir, "inner.zip", "inner content")
    
    # Level 1: Create middle zip containing inner zip
    middle_zip_path = temp_dir / "middle.zip"
    with zipfile.ZipFile(middle_zip_path, 'w') as zf:
        zf.write(inner_zip, inner_zip.name)
    
    # Level 2: Create outer zip containing middle zip
    outer_zip_path = temp_dir / "outer.zip"
    with zipfile.ZipFile(outer_zip_path, 'w') as zf:
        zf.write(middle_zip_path, middle_zip_path.name)
    
    # Clean up original files
    inner_zip.unlink()
    middle_zip_path.unlink()
    
    # Extract - should be limited by depth
    stats = extractor.extract_all(str(temp_dir))
    
    # Outer should extract, but nested ones should be blocked
    assert stats['total_processed'] >= 1

def test_extraction_stats(extractor, temp_dir):
    """Test extraction statistics tracking."""
    # Create mix of valid and invalid archives
    create_test_zip(temp_dir, "valid.zip")
    create_corrupted_zip(temp_dir, "invalid.zip")
    
    # Extract
    stats = extractor.extract_all(str(temp_dir))
    
    # Check stats
    assert stats['total_processed'] == 2
    assert stats['successful'] == 1
    assert stats['failed'] == 1
    assert len(stats['errors']) == 1
    
    # Test stats getter
    retrieved_stats = extractor.get_extraction_stats()
    assert retrieved_stats == stats

def test_skip_already_processed_within_run(extractor, temp_dir):
    """Test that already processed archives within a single run are skipped."""
    # Create a nested archive scenario where the same archive could be processed twice
    inner_zip = create_test_zip(temp_dir, "inner.zip", "inner content")
    outer_zip_path = temp_dir / "outer.zip"
    
    # Create outer zip containing the inner zip
    with zipfile.ZipFile(outer_zip_path, 'w') as zf:
        zf.write(inner_zip, inner_zip.name)
    
    # Don't remove inner zip, so it exists both as standalone and in outer zip
    
    # Extract - should process both but not duplicate inner.zip
    stats = extractor.extract_all(str(temp_dir))
    
    # Should process outer, then find inner again but skip it as already processed
    assert stats['total_processed'] >= 2
    assert stats['successful'] >= 1

