import sys
import click
import logging
from pathlib import Path
from .extractor import ArchiveExtractor
from .config import load_config
from .logger import setup_logging, get_logger, cleanup_logging

@click.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
@click.option('--preserve/--no-preserve', default=True, help='Preserve original archives after extraction')
@click.option('--verbose/--quiet', default=False, help='Increase output verbosity')
@click.option('--config', type=click.Path(exists=True), help='Path to configuration file')
@click.option('--max-ratio', type=float, help='Maximum extraction ratio for zipbomb protection')
@click.option('--max-depth', type=int, help='Maximum nested archive depth')
@click.option('--log-dir', type=click.Path(), help='Directory for log files')
@click.option('--torrent-name', type=str, help='Name of the torrent for per-torrent logging')
@click.version_option(version='0.1.0')
def main(directory: Path, preserve: bool, verbose: bool, config: str, 
         max_ratio: float, max_depth: int, log_dir: str, torrent_name: str) -> None:
    """Extract nested ZIP and RAR archives in the specified directory.
    
    This tool is designed to work with qBittorrent's "Run external program on torrent completion"
    feature, but can also be used standalone.
    
    DIRECTORY: Path to the directory containing the archives to extract.
    """
    # Load configuration with overrides
    config_obj = load_config(
        config_file=config,
        preserve_originals=preserve,
        log_level='DEBUG' if verbose else 'INFO',
        max_extraction_ratio=max_ratio,
        max_nested_depth=max_depth,
        log_dir=log_dir
    )
    
    # Setup enhanced logging system
    logging_manager = setup_logging(config_obj)
    logger = get_logger("main", torrent_name)
    
    try:
        logger.info(f"Starting qbit-torrent-extract v0.1.0")
        logger.info(f"Processing directory: {directory}")
        if torrent_name:
            logger.info(f"Torrent name: {torrent_name}")
        
        # Initialize extractor with configuration and torrent name
        extractor = ArchiveExtractor(
            preserve_archives=config_obj.preserve_originals,
            config=config_obj,
            torrent_name=torrent_name
        )
        
        # List files before extraction if verbose
        if verbose:
            archives = extractor.get_archive_files(str(directory))
            logger.info(f"Found {len(archives)} archives to process")
            click.echo("Found archives:")
            for archive in archives:
                click.echo(f"  {archive}")
        
        # Perform extraction
        stats = extractor.extract_all(str(directory))
        
        # Log extraction results
        logger.info(f"Extraction completed - Processed: {stats['total_processed']}, "
                   f"Successful: {stats['successful']}, Failed: {stats['failed']}, "
                   f"Skipped: {stats['skipped']}")
        
        if stats['errors']:
            logger.warning(f"Extraction completed with {len(stats['errors'])} errors")
            for error in stats['errors']:
                logger.error(f"  {error}")
        
        # Show logging statistics if verbose
        if verbose:
            log_stats = logging_manager.get_log_stats()
            logger.debug(f"Logging stats: {log_stats}")
        
        click.echo("Extraction completed successfully!")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        # Clean up logging system
        cleanup_logging()

if __name__ == '__main__':
    main()
