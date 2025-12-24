# qbit-torrent-extract

Your torrent finished downloading. It's an archive. Inside that archive is another archive. Sonarr doesn't know what to do. Sonarr gives up. You don't get your show.

This tool opens the archives. Now you get your show.

## Install

```bash
pip install qbit-torrent-extract
```

## Use It

Tell qBittorrent to run it when torrents finish:

**Tools → Options → Downloads → Run external program on torrent completion**

```
qbit-torrent-extract "%F"
```

That's the whole thing.

## What It Opens

- ZIP files
- RAR files (even the weird split ones)
- 7z files
- TAR files

## Options

Most people don't need these.

```
--no-preserve    Delete archives after extracting (careful)
--verbose        Show more information
--max-ratio      Zipbomb protection limit
--max-depth      How deep to go into nested archives
```

## It's Safe

It checks for zipbombs. It won't follow weird paths that try to write files outside the folder. It skips files that are still downloading. It keeps your original archives unless you tell it not to.

## License

MIT
