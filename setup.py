from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Separate dev requirements
dev_requirements = [req for req in requirements if any(dev_dep in req for dev_dep in 
                 ['pytest', 'black', 'flake8', 'mypy', 'isort', 'types-'])]
install_requirements = [req for req in requirements if req not in dev_requirements]

setup(
    name="qbit-torrent-extract",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Automated nested archive extraction for qBittorrent downloads",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/qbit-torrent-extract",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=install_requirements,
    extras_require={
        "dev": dev_requirements,
    },
    entry_points={
        "console_scripts": [
            "qbit-torrent-extract=qbit_torrent_extract.main:main",
        ],
    },
)
