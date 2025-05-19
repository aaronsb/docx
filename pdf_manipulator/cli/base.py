"""Base CLI utilities and shared functionality."""
import sys
from pathlib import Path
from typing import Optional, Dict, Any

import click

from pdf_manipulator.utils.config import (
    load_config, find_config_file, create_default_config,
    ConfigurationError, USER_CONFIG_DIR
)
from pdf_manipulator.utils.logging_config import configure_logging


def create_cli_context(
    config_path: Optional[str] = None,
    verbose: bool = False,
    log_level: str = 'INFO',
    no_file_log: bool = False
) -> Dict[str, Any]:
    """Create a CLI context with configuration and logging.
    
    Args:
        config_path: Optional path to configuration file
        verbose: Enable verbose output
        log_level: Logging level
        no_file_log: Disable file logging
        
    Returns:
        Context dictionary with configuration
    """
    # Configure logging first
    configure_logging(
        console_level='DEBUG' if verbose else log_level,
        enable_file=not no_file_log
    )
    
    context = {
        'verbose': verbose,
        'log_level': log_level
    }
    
    try:
        # Load configuration
        if config_path:
            context['config_path'] = config_path
            context['config'] = load_config(config_path)
            if verbose:
                click.echo(f"Using configuration from: {config_path}")
        else:
            try:
                found_config_path = find_config_file()
                context['config_path'] = str(found_config_path)
                context['config'] = load_config(found_config_path)
                if verbose:
                    click.echo(f"Using configuration from: {found_config_path}")
            except ConfigurationError:
                # No config found, create default in user directory
                user_config = Path(USER_CONFIG_DIR) / "config.yaml"
                create_default_config(user_config)
                context['config_path'] = str(user_config)
                context['config'] = load_config(user_config)
                click.echo(f"Created default configuration at: {user_config}")
    
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)
        
    return context


def add_common_options(func):
    """Decorator to add common CLI options to commands."""
    func = click.option('--config', type=click.Path(), 
                       help='Path to configuration file')(func)
    func = click.option('--verbose/--no-verbose', default=False, 
                       help='Enable verbose output')(func)
    func = click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
                       default='INFO', help='Set logging level')(func)
    func = click.option('--no-file-log', is_flag=True, default=False,
                       help='Disable file logging')(func)
    return func


def validate_file_exists(ctx, param, value):
    """Validate that a file exists."""
    if value is None:
        return value
    path = Path(value)
    if not path.exists():
        raise click.BadParameter(f"File not found: {value}")
    return value


def validate_directory(ctx, param, value):
    """Validate or create a directory."""
    if value is None:
        return value
    path = Path(value)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    elif not path.is_dir():
        raise click.BadParameter(f"Not a directory: {value}")
    return value


class ProgressReporter:
    """Simple progress reporter for CLI operations."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        
    def start(self, message: str):
        """Start a progress operation."""
        if self.verbose:
            click.echo(f"Starting: {message}")
        else:
            click.echo(message, nl=False)
            
    def update(self, message: str):
        """Update progress."""
        if self.verbose:
            click.echo(f"  {message}")
        else:
            click.echo(".", nl=False)
            
    def complete(self, message: str = "Done"):
        """Complete the progress operation."""
        if self.verbose:
            click.echo(f"Completed: {message}")
        else:
            click.echo(f" {message}")
            
    def error(self, message: str):
        """Report an error."""
        click.echo(f"\nError: {message}", err=True)