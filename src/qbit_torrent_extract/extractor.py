import logging
import os
from pathlib import Path
from typing import Optional, List
import zipfile
import rarfile
from tqdm import tqdm
from .config import Config

class ArchiveExtractor:
    def __init__(self, preserve_archives: bool = True, log_level: int = logging.INFO, config: Optional[Config] = None):
        """Initialize the archive extractor.
        
        Args:
            preserve_archives: If True, keep original archives after extraction
            log_level: Logging level to use
            config: Configuration object
        """
        self.config = config or Config()
        self.preserve_archives = preserve_archives
        self._setup_logging(log_level)

    def _setup_logging(self, log_level: int) -> None:
        """Setup logging configuration."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def extract_all(self, directory: str) -> None:
        """Extract all supported archives in the given directory recursively."""
        self.logger.info(f"Starting extraction in directory: {directory}")
        
        # First pass: Extract all ZIP files
        self._extract_zip_files(directory)
        
        # Second pass: Extract all RAR files (including newly extracted ones)
        self._extract_rar_files(directory)

    def _extract_zip_files(self, directory: str) -> None:
        """Extract all ZIP files in the directory recursively."""
        zip_files = list(Path(directory).rglob("*.zip"))
        if not zip_files:
            self.logger.info("No ZIP files found")
            return

        for zip_path in tqdm(zip_files, desc="Extracting ZIP files"):
            try:
                with zipfile.ZipFile(zip_path) as zf:
                    self.logger.info(f"Extracting ZIP: {zip_path}")
                    zf.extractall(path=zip_path.parent)
                    
                if not self.preserve_archives:
                    os.remove(zip_path)
                    self.logger.info(f"Removed ZIP: {zip_path}")
                    
            except Exception as e:
                self.logger.error(f"Error extracting {zip_path}: {e}")

    def _extract_rar_files(self, directory: str) -> None:
        """Extract all RAR files in the directory recursively."""
        rar_files = list(Path(directory).rglob("*.rar"))
        if not rar_files:
            self.logger.info("No RAR files found")
            return

        for rar_path in tqdm(rar_files, desc="Extracting RAR files"):
            try:
                with rarfile.RarFile(rar_path) as rf:
                    self.logger.info(f"Extracting RAR: {rar_path}")
                    rf.extractall(path=rar_path.parent)
                    
                if not self.preserve_archives:
                    os.remove(rar_path)
                    self.logger.info(f"Removed RAR: {rar_path}")
                    
            except Exception as e:
                self.logger.error(f"Error extracting {rar_path}: {e}")

    def get_archive_files(self, directory: str) -> List[Path]:
        """Get all archive files in the directory."""
        archives = []
        archives.extend(Path(directory).rglob("*.zip"))
        archives.extend(Path(directory).rglob("*.rar"))
        return sorted(archives)

