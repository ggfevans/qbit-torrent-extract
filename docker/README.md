# Docker Integration

## Quick Start

```bash
docker-compose -f docker-compose.qbittorrent.yml up -d
```

Then in qBittorrent WebUI (http://localhost:8080):
1. Settings → Downloads → Run external program on torrent completion
2. Enter: `/scripts/extract.sh "%F"`
3. Save

## Add to Existing Container

```bash
docker exec qbittorrent pip3 install qbit-torrent-extract
```

Then configure qBittorrent to run:
```
python3 -m qbit_torrent_extract "%F"
```

## Config

Edit `/config/qte-config.json`:
```json
{
  "preserve_originals": true,
  "max_extraction_ratio": 100.0,
  "max_nested_depth": 3
}
```
