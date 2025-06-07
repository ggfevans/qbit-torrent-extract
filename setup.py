"""Setup configuration for qbit-torrent-extract.

This module configures the package for distribution via pip and PyPI.
"""

import os
import sys
from pathlib import Path
from setuptools import setup, find_packages

# Package metadata
NAME = "qbit-torrent-extract"
VERSION = "0.1.0"
AUTHOR = "Your Name"
EMAIL = "your.email@example.com"
DESCRIPTION = "Automated nested archive extraction for qBittorrent downloads - solves the 'No files found' problem for *arr apps"
URL = "https://github.com/yourusername/qbit-torrent-extract"
LICENSE = "MIT"

# Get the absolute path to the directory containing this file
HERE = Path(__file__).parent.resolve()

# Read the long description from README
try:
    long_description = (HERE / "README.md").read_text(encoding="utf-8")
except FileNotFoundError:
    long_description = DESCRIPTION

# Read requirements
def read_requirements(filename):
    """Read requirements from a file, handling comments and blank lines."""
    requirements_path = HERE / filename
    if requirements_path.exists():
        with open(requirements_path, "r", encoding="utf-8") as fh:
            return [
                line.strip()
                for line in fh
                if line.strip() and not line.startswith("#")
            ]
    return []

# Core requirements
install_requirements = [
    "click>=8.0.0",
    "tqdm>=4.60.0",
    "rarfile>=4.0",
    "py7zr>=0.20.0",
]

# Development requirements
dev_requirements = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
    "types-tqdm>=4.65.0",
    "psutil>=5.9.0",  # For performance tests
]

# Documentation requirements
docs_requirements = [
    "sphinx>=6.0.0",
    "sphinx-rtd-theme>=1.3.0",
    "sphinx-click>=4.4.0",
]

setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=EMAIL,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=URL,
    license=LICENSE,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Archiving",
        "Topic :: System :: Filesystems",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Environment :: Console",
        "Natural Language :: English",
    ],
    keywords=[
        "qbittorrent",
        "archive",
        "extraction",
        "zip",
        "rar",
        "7z",
        "automation",
        "torrent",
        "readarr",
        "sonarr",
        "radarr",
        "lidarr",
        "*arr",
    ],
    python_requires=">=3.8",
    install_requires=install_requirements,
    extras_require={
        "dev": dev_requirements,
        "docs": docs_requirements,
        "all": dev_requirements + docs_requirements,
    },
    entry_points={
        "console_scripts": [
            "qbit-torrent-extract=qbit_torrent_extract.main:main",
            "qte=qbit_torrent_extract.main:main",  # Short alias
        ],
    },
    include_package_data=True,
    package_data={
        "qbit_torrent_extract": ["py.typed"],  # For type checking support
    },
    project_urls={
        "Documentation": f"{URL}/tree/main/docs",
        "Bug Reports": f"{URL}/issues",
        "Source": URL,
        "Changelog": f"{URL}/blob/main/CHANGELOG.md",
    },
    # Platform-specific dependencies
    # Note: unrar and p7zip must be installed separately at system level
    zip_safe=False,  # Don't install as zip for better debugging
)
