# Docker Integration for qbit-torrent-extract

This directory contains Docker configurations for running qbit-torrent-extract with qBittorrent.

## Quick Start

### Option 1: qBittorrent with Built-in Extraction (Recommended)

This is the easiest way to use qbit-torrent-extract with your *arr apps:

```bash
# Build and run qBittorrent with extraction built-in
docker-compose -f docker-compose.qbittorrent.yml up -d

# Configure qBittorrent:
# 1. Open http://localhost:8080
# 2. Settings -> Downloads -> Run external program on torrent completion
# 3. Enter: /scripts/extract.sh "%F" "%N" "%L" "%I"
# 4. Save
```

That's it! Your torrents will now automatically extract when complete, and your *arr apps will see the files.

### Option 2: Add to Existing qBittorrent Container

If you already have qBittorrent running, you can add extraction to it:

```bash
# Install in running container
docker exec qbittorrent sh -c "
  apk add --no-cache python3 py3-pip unrar p7zip
  pip3 install qbit-torrent-extract
"

# Create extraction script
docker exec qbittorrent sh -c 'echo "#!/bin/sh
python3 -m qbit_torrent_extract \"\$1\" --torrent-name \"\$2\"
" > /config/extract.sh'
docker exec qbittorrent chmod +x /config/extract.sh

# Configure in qBittorrent WebUI:
# Command: /config/extract.sh "%F" "%N"
```

### Option 3: Standalone Container (Not Recommended)

The standalone container in the parent directory can be used, but it's more complex to integrate with qBittorrent's completion hooks.

## Configuration

### Extraction Settings

Edit `/config/qte-config.json` in the container:

```json
{
  "preserve_originals": true,       // Keep archives for seeding
  "max_extraction_ratio": 100.0,    // Zipbomb protection
  "max_nested_depth": 3,            // How deep to extract
  "log_level": "INFO",              // Logging verbosity
  "skip_on_error": true,            // Continue on errors
  "progress_indicators": false      // Disable for background operation
}
```

### Logs

- Extraction logs: `/config/extraction.log`
- Detailed logs: `/config/qte-logs/`
- Statistics: `/config/qte-stats.json`

### Integration with *arr Apps

The extracted files will appear in the same directory as the archive, making them visible to Readarr/Sonarr/etc.

Example flow:
1. Readarr sends book to qBittorrent
2. qBittorrent downloads: `Chuck.Palahniuk.-.Fight.Club.2011.Retail.EPUB.eBook-BitBook.zip`
3. On completion, extraction runs automatically
4. `Fight Club - Chuck Palahniuk.epub` appears in the directory
5. Readarr imports the book successfully!

## Environment Variables

```bash
# .env file
PUID=1000
PGID=1000
TZ=America/New_York
DOWNLOAD_DIR=/media/downloads
```

## Troubleshooting

### "No files found are eligible for import" still appearing?

1. Check extraction log:
   ```bash
   docker exec qbittorrent tail -f /config/extraction.log
   ```

2. Verify script is configured:
   ```bash
   docker exec qbittorrent cat /config/qBittorrent/qBittorrent.conf | grep -A5 "AutoRun"
   ```

3. Test extraction manually:
   ```bash
   docker exec qbittorrent python3 -m qbit_torrent_extract /downloads/your-torrent --verbose
   ```

### Permission Issues

Ensure PUID/PGID match your *arr apps:
```bash
# Check file ownership
docker exec qbittorrent ls -la /downloads

# Fix permissions if needed
docker exec qbittorrent chown -R abc:abc /downloads
```

### Archives Not Extracting

Check supported formats and limits:
```bash
docker exec qbittorrent python3 -m qbit_torrent_extract --help
```

## Advanced Usage

### Custom Categories

Modify the extraction script to handle different categories differently:

```bash
# In /scripts/extract.sh
if [ "$CATEGORY" = "books" ]; then
    # Special handling for ebooks
    python3 -m qbit_torrent_extract "$TORRENT_PATH" --max-depth 5
elif [ "$CATEGORY" = "movies" ]; then
    # Movies might have different settings
    python3 -m qbit_torrent_extract "$TORRENT_PATH" --max-ratio 200
fi
```

### Notifications

Add notifications after successful extraction:

```bash
# Notify Readarr to rescan
if [ "$CATEGORY" = "readarr" ]; then
    curl -X POST "http://readarr:8787/api/v1/command" \
         -H "X-Api-Key: YOUR_API_KEY" \
         -H "Content-Type: application/json" \
         -d '{"name": "RescanFolders", "folders": ["'$TORRENT_PATH'"]}'
fi
```

## Building Custom Image

```bash
# Build with your modifications
docker build -f docker/Dockerfile.qbittorrent -t my-qbittorrent-qte .

# Push to your registry
docker tag my-qbittorrent-qte myregistry/qbittorrent-qte:latest
docker push myregistry/qbittorrent-qte:latest
```

## Notes

- The LinuxServer.io base image runs as user `abc` (PUID/PGID)
- Extraction happens synchronously - large archives may delay qBittorrent
- Consider the impact on seeding ratios when not preserving originals
- Test with a small torrent first before enabling globally

Remember: This tool exists because we've all stared at "No files found are eligible for import" one too many times!