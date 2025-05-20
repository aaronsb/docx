"""Main CLI entry point for DocX."""
import click
import logging

from .base import create_cli_context
from .process_commands import process_document, process_directory
from .memory_commands import memory_group
from .config_commands import manage_config, init_config
from .utility_commands import render_pdf, transcribe_image, pdf_info, manage_backends
from .semantic_commands import semantic_group
from ..utils.env_loader import load_dotenv

logger = logging.getLogger(__name__)


@click.group()
@click.option('--config', type=click.Path(), 
              help='Path to configuration file')
@click.option('--verbose/--no-verbose', default=False, 
              help='Enable verbose output')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
              default='INFO', help='Set logging level')
@click.option('--no-file-log', is_flag=True, default=False,
              help='Disable file logging')
@click.pass_context
def cli(ctx, config, verbose, log_level, no_file_log):
    """Memory Graph Extract: Semantic extraction for the memory-graph ecosystem.
    
    Transform documents into queryable semantic knowledge graphs compatible
    with memory-graph (AI access) and memory-graph-interface (human access).
    """
    # Create CLI context
    ctx.obj = create_cli_context(
        config_path=config,
        verbose=verbose,
        log_level=log_level,
        no_file_log=no_file_log
    )


# Register commands - new names
cli.add_command(process_document, name='extract')
cli.add_command(process_directory, name='extract-dir')

# Legacy compatibility aliases
cli.add_command(process_document, name='process')
cli.add_command(process_directory, name='process-dir')

# Other commands
cli.add_command(memory_group)
cli.add_command(semantic_group)
cli.add_command(manage_config)
cli.add_command(init_config)
cli.add_command(render_pdf)
cli.add_command(transcribe_image)
cli.add_command(pdf_info)
cli.add_command(manage_backends)


def main():
    """Main entry point."""
    # Load environment variables from .env file
    env_vars = load_dotenv()
    if env_vars:
        logger.debug(f"Loaded {len(env_vars)} environment variables from .env file")
    
    # Run CLI with proper program name
    cli(prog_name='mge')


if __name__ == '__main__':
    main()