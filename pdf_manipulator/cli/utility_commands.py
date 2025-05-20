"""Utility commands for PDF manipulation."""
import sys
from pathlib import Path
from typing import Optional

import click

from pdf_manipulator.core.document import PDFDocument
from pdf_manipulator.renderers.image_renderer import ImageRenderer
from pdf_manipulator.intelligence.processor import create_processor
from pdf_manipulator.intelligence.base import IntelligenceManager
from .base import ProgressReporter, validate_file_exists, validate_directory


@click.command(name='render')
@click.argument('pdf_path', type=click.Path(exists=True), callback=validate_file_exists)
@click.argument('output_dir', type=click.Path(), required=False, callback=validate_directory)
@click.option('--dpi', type=int, help='Resolution in DPI')
@click.option('--alpha/--no-alpha', help='Include alpha channel')
@click.option('--zoom', type=float, help='Additional zoom factor')
@click.option('--page', type=int, help='Specific page to render (0-based)')
@click.option('--prefix', type=str, help='Filename prefix for output images')
@click.pass_context
def render_pdf(
    ctx,
    pdf_path: str,
    output_dir: Optional[str],
    dpi: Optional[int],
    alpha: Optional[bool],
    zoom: Optional[float],
    page: Optional[int],
    prefix: Optional[str]
):
    """Render PDF pages to images."""
    config = ctx.obj['config']
    verbose = ctx.obj.get('verbose', False)
    reporter = ProgressReporter(verbose)
    
    # Default output directory
    if output_dir is None:
        output_dir = Path('output') / Path(pdf_path).stem / 'images'
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Get rendering settings from config with command-line overrides
    rendering_config = config.get('rendering', {})
    dpi = dpi or rendering_config.get('dpi', 300)
    alpha = alpha if alpha is not None else rendering_config.get('alpha', False)
    zoom = zoom or rendering_config.get('zoom', 1.0)
    prefix = prefix or 'page_'
    
    try:
        reporter.start(f"Rendering {pdf_path}")
        
        with PDFDocument(pdf_path) as doc:
            renderer = ImageRenderer(doc)
            
            # Render specific page or all pages
            if page is not None:
                if 0 <= page < doc.page_count:
                    output_path = Path(output_dir) / f"{prefix}{page:04d}.png"
                    renderer.render_page_to_png(
                        page_number=page,
                        output_path=str(output_path),
                        dpi=dpi,
                        alpha=alpha,
                        zoom=zoom
                    )
                    reporter.complete(f"Rendered page {page} to {output_path}")
                else:
                    reporter.error(f"Page {page} out of range (0-{doc.page_count-1})")
            else:
                # Render all pages
                pages_rendered = 0
                for page_num in range(doc.page_count):
                    output_path = Path(output_dir) / f"{prefix}{page_num:04d}.png"
                    renderer.render_page_to_png(
                        page_number=page_num,
                        output_path=str(output_path),
                        dpi=dpi,
                        alpha=alpha,
                        zoom=zoom
                    )
                    pages_rendered += 1
                    reporter.update(f"Rendered page {page_num + 1}/{doc.page_count}")
                
                reporter.complete(f"Rendered {pages_rendered} pages")
    
    except Exception as e:
        reporter.error(str(e))
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)




@click.command(name='transcribe')
@click.argument('image_path', type=click.Path(exists=True), callback=validate_file_exists)
@click.option('--backend', help='AI backend to use (markitdown, ollama, openai)')
@click.option('--model', help='Model name')
@click.option('--output', type=click.Path(), help='Output file (default: print to console)')
@click.option('--prompt', help='Custom prompt for AI processing')
@click.pass_context
def transcribe_image(
    ctx,
    image_path: str,
    backend: Optional[str],
    model: Optional[str],
    output: Optional[str],
    prompt: Optional[str]
):
    """Transcribe an image using AI for intelligent text extraction."""
    config = ctx.obj['config']
    verbose = ctx.obj.get('verbose', False)
    reporter = ProgressReporter(verbose)
    
    # Get backend from config if not specified
    backend = backend or config.get('intelligence', {}).get('default_backend', 'markitdown')
    
    # Get default prompt if not specified
    if not prompt:
        prompt = config.get('processing', {}).get(
            'default_prompt',
            'Transcribe all text in this document image to markdown format.'
        )
    
    try:
        reporter.start(f"Transcribing {image_path} with {backend}")
        
        # Create AI processor
        ai_processor = create_processor(
            config=config,
            backend_name=backend
        )
        
        # Process image
        text = ai_processor.process_image(
            image_path=image_path,
            custom_prompt=prompt
        )
        
        if output:
            # Write to file
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            with open(output, 'w', encoding='utf-8') as f:
                f.write(text)
            reporter.complete(f"Transcription saved to {output}")
        else:
            # Print to console
            click.echo("\nTranscribed text:")
            click.echo("=" * 40)
            click.echo(text)
            click.echo("=" * 40)
            reporter.complete("Transcription complete")
    
    except Exception as e:
        reporter.error(str(e))
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@click.command(name='info')
@click.argument('pdf_path', type=click.Path(exists=True), callback=validate_file_exists)
@click.option('--show-toc/--no-show-toc', default=True, help='Display table of contents')
@click.pass_context
def pdf_info(ctx, pdf_path: str, show_toc: bool):
    """Display information about a PDF file."""
    verbose = ctx.obj.get('verbose', False)
    reporter = ProgressReporter(verbose)
    
    try:
        reporter.start(f"Analyzing {pdf_path}")
        
        with PDFDocument(pdf_path) as doc:
            click.echo(f"\nFile: {pdf_path}")
            click.echo(f"Pages: {doc.page_count}")
            
            # Display metadata
            info = doc.get_info()
            if info:
                click.echo("\nMetadata:")
                for key, value in info.items():
                    if value:
                        click.echo(f"  {key}: {value}")
            
            # Display table of contents
            if show_toc:
                toc = doc.get_toc()
                if toc:
                    click.echo("\nTable of Contents:")
                    for i, entry in enumerate(toc):
                        level, title, page_num, *_ = entry
                        indent = "  " * (level - 1)
                        click.echo(f"{indent}{title} (page {page_num})")
                else:
                    click.echo("\nNo table of contents found")
            
            # Document statistics
            if verbose:
                click.echo("\nDocument Analysis:")
                for page_num in range(min(5, doc.page_count)):  # Sample first 5 pages
                    page = doc.get_page(page_num)
                    text = page.get_text()
                    if text and page_num == 0:
                        # Simple word count
                        word_count = len(text.split())
                        click.echo(f"  Sample word count (page 1): ~{word_count}")
                        
        reporter.complete("Analysis complete")
    
    except Exception as e:
        reporter.error(str(e))
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@click.command(name='backends')
@click.option('--list', 'list_backends', is_flag=True, help='List available intelligence backends')
@click.pass_context
def manage_backends(ctx, list_backends: bool):
    """Manage AI intelligence backends."""
    config = ctx.obj['config']
    
    if list_backends:
        # Create intelligence manager
        manager = IntelligenceManager(config)
        backends = manager.list_available_backends()
        
        click.echo("Available intelligence backends:")
        for name, info in backends.items():
            status = "✓" if info['available'] else "✗"
            click.echo(f"  {status} {name}: {info['description']}")
            if not info['available'] and info.get('error'):
                click.echo(f"    Error: {info['error']}")
    else:
        # Show current backend info
        current_backend = config.get('intelligence', {}).get('default_backend', 'markitdown')
        click.echo(f"Current default backend: {current_backend}")
        
        backend_config = config.get('intelligence', {}).get('backends', {}).get(current_backend, {})
        if backend_config:
            click.echo("\nBackend configuration:")
            for key, value in backend_config.items():
                click.echo(f"  {key}: {value}")