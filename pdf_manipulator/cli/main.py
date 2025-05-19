"""Main CLI entry point for DocX."""
import click

from .base import create_cli_context
from .process_commands import process_document, process_directory
from .memory_commands import memory_group
from .config_commands import manage_config, init_config
from .utility_commands import render_pdf, ocr_image, transcribe_image, pdf_info, manage_backends


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
    """DocX: Semantic Knowledge Graph Extraction for Documents.
    
    Transform PDF documents into queryable semantic knowledge graphs,
    enabling intelligent understanding of document content and relationships.
    """
    # Create CLI context
    ctx.obj = create_cli_context(
        config_path=config,
        verbose=verbose,
        log_level=log_level,
        no_file_log=no_file_log
    )


# Register commands
cli.add_command(process_document)
cli.add_command(process_directory)
cli.add_command(memory_group)
cli.add_command(manage_config)
cli.add_command(init_config)
cli.add_command(render_pdf)
cli.add_command(ocr_image)
cli.add_command(transcribe_image)
cli.add_command(pdf_info)
cli.add_command(manage_backends)


def main():
    """Main entry point."""
    cli(prog_name='pdfx')


if __name__ == '__main__':
    main()