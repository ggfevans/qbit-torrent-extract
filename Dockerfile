# qbit-torrent-extract Docker image
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    unrar p7zip-full && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 extractor

WORKDIR /app

# Copy and install
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

# Setup directories
RUN mkdir -p /config /data && chown -R extractor:extractor /config /data

USER extractor

VOLUME ["/config", "/data"]

ENTRYPOINT ["python", "-m", "qbit_torrent_extract"]
CMD ["--help"]

LABEL description="Archive extraction for qBittorrent" version="0.2.0"
