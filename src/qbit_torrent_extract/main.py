import sys
import click
import logging
from pathlib import Path
from .extractor import ArchiveExtractor

@click.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
@click.option('--preserve/--no-preserve', default=True, help='Preserve original archives after extraction')
@click.option('--verbose/--quiet', default=False, help='Increase output verbosity')
@click.version_option(version='0.1.0')
def main(directory: Path, preserve: bool, verbose: bool) -> None:
    """Extract nested ZIP and RAR archives in the specified directory.
    
    This tool is designed to work with qBittorrent's "Run external program on torrent completion"
    feature, but can also be used standalone.
    
    DIRECTORY: Path to the directory containing the archives to extract.
    """
    # Set up logging level based on verbosity
    log_level = logging.DEBUG if verbose else logging.INFO
    
    try:
        # Initialize extractor
        extractor = ArchiveExtractor(preserve_archives=preserve, log_level=log_level)
        
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
