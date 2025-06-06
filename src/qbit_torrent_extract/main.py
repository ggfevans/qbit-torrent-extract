import sys
import click
import logging
from pathlib import Path
from .extractor import ArchiveExtractor
from .config import load_config

@click.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
@click.option('--preserve/--no-preserve', default=True, help='Preserve original archives after extraction')
@click.option('--verbose/--quiet', default=False, help='Increase output verbosity')
@click.option('--config', type=click.Path(exists=True), help='Path to configuration file')
@click.option('--max-ratio', type=float, help='Maximum extraction ratio for zipbomb protection')
@click.option('--max-depth', type=int, help='Maximum nested archive depth')
@click.option('--log-dir', type=click.Path(), help='Directory for log files')
@click.version_option(version='0.1.0')
def main(directory: Path, preserve: bool, verbose: bool, config: str, 
         max_ratio: float, max_depth: int, log_dir: str) -> None:
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
    
    # Set up logging
    log_level = getattr(logging, config_obj.log_level)
    
    try:
        # Initialize extractor with configuration
        extractor = ArchiveExtractor(
            preserve_archives=config_obj.preserve_originals,
            log_level=log_level,
            config=config_obj
        )
        
        # List files before extraction if verbose
        if verbose:
            click.echo("Found archives:")
            for archive in extractor.get_archive_files(directory):
                click.echo(f"  {archive}")
        
        # Perform extraction
        extractor.extract_all(directory)
        
        click.echo("Extraction completed successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
