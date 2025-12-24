"""CLI entry point for qbit-torrent-extract."""

import sys

import click
from pathlib import Path

from .config import load_config
from .extractor import ArchiveExtractor
from .logger import setup_logging, get_logger


@click.command()
@click.argument(
    "directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--preserve/--no-preserve",
    default=True,
    help="Preserve original archives after extraction",
)
@click.option(
    "--verbose/--quiet",
    default=False,
    help="Increase output verbosity",
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.option(
    "--max-ratio",
    type=float,
    help="Maximum extraction ratio for zipbomb protection",
)
@click.option(
    "--max-depth",
    type=int,
    help="Maximum nested archive depth",
)
@click.option(
    "--log-dir",
    type=click.Path(),
    help="Directory for log files",
)
@click.version_option(version="0.2.0")
def main(
    directory: Path,
    preserve: bool,
    verbose: bool,
    config: str,
    max_ratio: float,
    max_depth: int,
    log_dir: str,
) -> None:
    """Extract nested archives (ZIP, RAR, 7z, TAR) in the specified directory.

    Designed for qBittorrent's "Run external program on torrent completion"
    feature, but works standalone too.

    DIRECTORY: Path to the directory containing archives to extract.
    """
    # Load configuration
    config_obj = load_config(
        config_file=config,
        preserve_originals=preserve,
        log_level="DEBUG" if verbose else "INFO",
        max_extraction_ratio=max_ratio,
        max_nested_depth=max_depth,
        log_dir=log_dir,
    )

    # Setup logging
    setup_logging(level=config_obj.log_level, log_dir=config_obj.log_dir)
    logger = get_logger()

    try:
        logger.info("qbit-torrent-extract v0.2.0")
        logger.info(f"Processing: {directory}")

        # Initialize and run extractor
        extractor = ArchiveExtractor(
            preserve_archives=config_obj.preserve_originals,
            config=config_obj,
        )

        # Show archives if verbose
        if verbose:
            archives = extractor.get_archive_files(str(directory))
            logger.info(f"Found {len(archives)} archives")
            for archive in archives:
                click.echo(f"  {archive.name}")

        # Extract
        stats = extractor.extract_all(str(directory))

        # Report results
        if stats["errors"]:
            logger.warning(f"Completed with {len(stats['errors'])} errors:")
            for error in stats["errors"]:
                logger.error(f"  {error}")
        else:
            click.echo("Extraction completed successfully!")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
