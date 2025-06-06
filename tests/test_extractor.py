import pytest
import tempfile
import zipfile
import rarfile
import os
from pathlib import Path
from qbit_torrent_extract.extractor import ArchiveExtractor

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def extractor():
    """Create an ArchiveExtractor instance."""
    return ArchiveExtractor(preserve_archives=True)

def create_test_zip(directory: Path, filename: str = "test.zip", content: str = "test content") -> Path:
    """Create a test ZIP file."""
    zip_path = directory / filename
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("test.txt", content)
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
    extractor = ArchiveExtractor(preserve_archives=False)
    
    # Create test ZIP
    zip_path = create_test_zip(temp_dir)
    
    # Extract
    extractor.extract_all(temp_dir)
    
    # Check results
    assert (temp_dir / "test.txt").exists()
    assert not (temp_dir / "test.zip").exists()  # should be removed

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
    extractor.extract_all(temp_dir)
    
    # Check results
    assert (temp_dir / "inner.zip").exists()
    assert (temp_dir / "test.txt").exists()  # from inner zip

