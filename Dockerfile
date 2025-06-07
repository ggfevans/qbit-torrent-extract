# Multi-stage Dockerfile for qbit-torrent-extract
# Supports both development and production builds

# Build stage
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements first for better caching
COPY requirements.txt .
COPY setup.py .
COPY pyproject.toml .
COPY README.md .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt && \
    pip install --user --no-cache-dir .

# Runtime stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    unrar \
    p7zip-full \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash extractor

# Copy Python packages from builder
COPY --from=builder /root/.local /home/extractor/.local

# Copy application
WORKDIR /app
COPY --chown=extractor:extractor src/ ./src/

# Set environment
ENV PATH=/home/extractor/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    QBIT_EXTRACT_LOG_LEVEL=INFO

# Create directories for configs and logs
RUN mkdir -p /config /logs /data && \
    chown -R extractor:extractor /config /logs /data

# Switch to non-root user
USER extractor

# Volume mounts
VOLUME ["/config", "/logs", "/data"]

# Default configuration
RUN echo '{\n\
    "preserve_originals": true,\n\
    "max_extraction_ratio": 100.0,\n\
    "max_nested_depth": 3,\n\
    "log_dir": "/logs",\n\
    "log_level": "INFO",\n\
    "skip_on_error": true\n\
}' > /config/default.json

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import qbit_torrent_extract; print('OK')" || exit 1

# Entry point
ENTRYPOINT ["python", "-m", "qbit_torrent_extract"]

# Default command (can be overridden)
CMD ["--config", "/config/default.json", "--help"]

# Labels
LABEL maintainer="your.email@example.com" \
      description="Automated nested archive extraction for qBittorrent - The Readarr Whisperer" \
      version="0.1.0" \
      org.opencontainers.image.source="https://github.com/yourusername/qbit-torrent-extract" \
      org.opencontainers.image.documentation="https://github.com/yourusername/qbit-torrent-extract/tree/main/docs" \
      org.opencontainers.image.licenses="MIT"