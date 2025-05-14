"""Command-line interface for document AI toolkit."""
import os
import sys
from pathlib import Path
from typing import Optional, List

import click
from tqdm import tqdm

from pdf_manipulator.core.document import PDFDocument
from pdf_manipulator.renderers.image_renderer import ImageRenderer
from pdf_manipulator.extractors.ocr import OCRProcessor, DocumentAnalyzer
from pdf_manipulator.core.pipeline import DocumentProcessor as CoreDocumentProcessor
from pdf_manipulator.utils.config import (
    load_config, find_config_file, create_default_config, 
    get_all_config_paths, ConfigurationError,
    USER_CONFIG_DIR, PROJECT_CONFIG_DIR
)
from pdf_manipulator.intelligence.processor import create_processor, DocumentProcessor
from pdf_manipulator.intelligence.base import IntelligenceManager


@click.group()
@click.option('--config', type=click.Path(), 
              help='Path to configuration file')
@click.option('--verbose/--no-verbose', default=False, 
              help='Enable verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """Document AI Toolkit: Process and analyze documents with AI."""
    # Create context object to pass data between commands
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    try:
        # Load configuration
        if config:
            ctx.obj['config_path'] = config
            ctx.obj['config'] = load_config(config)
            if verbose:
                click.echo(f"Using configuration from: {config}")
        else:
            try:
                config_path = find_config_file()
                ctx.obj['config_path'] = str(config_path)
                ctx.obj['config'] = load_config(config_path)
                if verbose:
                    click.echo(f"Using configuration from: {config_path}")
            except ConfigurationError:
                # No config found, create default in user directory
                user_config = Path(USER_CONFIG_DIR) / "config.yaml"
                create_default_config(user_config)
                ctx.obj['config_path'] = str(user_config)
                ctx.obj['config'] = load_config(user_config)
                click.echo(f"Created default configuration at: {user_config}")
    
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--user', is_flag=True, help='Create/edit user configuration')
@click.option('--project', is_flag=True, help='Create/edit project configuration')
@click.option('--list', 'list_configs', is_flag=True, help='List available configuration files')
@click.option('--editor', is_flag=True, help='Open configuration in default editor')
@click.pass_context
def config(ctx, user, project, list_configs, editor):
    """Manage configuration files."""
    if list_configs:
        # List available configuration files
        config_paths = get_all_config_paths()
        click.echo("Available configuration files:")
        click.echo(f"  System: {config_paths.system_config}")
        click.echo(f"  User:   {config_paths.user_config}" + 
                  (" (default)" if config_paths.user_config.exists() else " (not found)"))
        click.echo(f"  Project: {config_paths.project_config}" + 
                  (" (active)" if config_paths.project_config.exists() else " (not found)"))
        return
    
    if user:
        # Create or update user configuration
        config_path = Path(USER_CONFIG_DIR) / "config.yaml"
        if not config_path.exists():
            create_default_config(config_path)
            click.echo(f"Created user configuration at: {config_path}")
        else:
            click.echo(f"User configuration already exists at: {config_path}")
        
        config_to_edit = str(config_path)
    
    elif project:
        # Create or update project configuration
        config_path = Path(PROJECT_CONFIG_DIR) / "config.yaml"
        if not config_path.exists():
            create_default_config(config_path)
            click.echo(f"Created project configuration at: {config_path}")
        else:
            click.echo(f"Project configuration already exists at: {config_path}")
        
        config_to_edit = str(config_path)
    
    else:
        # Use active configuration
        config_to_edit = ctx.obj['config_path']
    
    if editor:
        # Open in editor
        click.edit(filename=config_to_edit)


@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path(), required=False)
@click.option('--dpi', type=int, help='Resolution in DPI')
@click.option('--alpha/--no-alpha', help='Include alpha channel')
@click.option('--zoom', type=float, help='Additional zoom factor')
@click.option('--page', type=int, help='Specific page to render (0-based)')
@click.option('--prefix', type=str, help='Filename prefix for output images')
@click.pass_context
def render(
    ctx,
    pdf_path: str, 
    output_dir: Optional[str], 
    dpi: Optional[int],
    alpha: Optional[bool],
    zoom: Optional[float],
    page: Optional[int],
    prefix: Optional[str],
):
    """Render PDF pages to PNG images."""
    config = ctx.obj['config']
    verbose = ctx.obj['verbose']
    
    # Get values from config if not provided
    if output_dir is None:
        output_dir = config.get('general', {}).get('output_dir', 'output')
    
    if dpi is None:
        dpi = config.get('rendering', {}).get('dpi', 300)
    
    if alpha is None:
        alpha = config.get('rendering', {}).get('alpha', False)
    
    if zoom is None:
        zoom = config.get('rendering', {}).get('zoom', 1.0)
    
    if prefix is None:
        prefix = "page_"
    
    # Create output directory
    output_dir = Path(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Render pages
    with PDFDocument(pdf_path) as doc:
        renderer = ImageRenderer(doc)
        
        if page is not None:
            # Render specific page
            output_file = output_dir / f"{prefix}{page:04d}.png"
            renderer.render_page_to_png(
                page_number=page,
                output_path=output_file,
                dpi=dpi,
                alpha=alpha,
                zoom=zoom,
            )
            click.echo(f"Rendered page {page} to {output_file}")
        else:
            # Render all pages
            click.echo(f"Rendering {doc.page_count} pages from {pdf_path}...")
            
            with tqdm(total=doc.page_count) as pbar:
                for i in range(doc.page_count):
                    output_file = output_dir / f"{prefix}{i:04d}.png"
                    renderer.render_page_to_png(
                        page_number=i,
                        output_path=output_file,
                        dpi=dpi,
                        alpha=alpha,
                        zoom=zoom,
                    )
                    pbar.update(1)
            
            click.echo(f"All pages rendered to {output_dir}")


@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.option('--show-toc/--no-show-toc', default=True, help='Display table of contents')
@click.pass_context
def info(ctx, pdf_path: str, show_toc: bool):
    """Display information about a PDF file."""
    with PDFDocument(pdf_path) as doc:
        click.echo(f"File: {pdf_path}")
        click.echo(f"Pages: {doc.page_count}")
        click.echo("Metadata:")
        for key, value in doc.metadata.items():
            if value:
                click.echo(f"  {key}: {value}")
        
        # Display page dimensions for the first page
        if doc.page_count > 0:
            width, height = doc.get_page_dimensions(0)
            click.echo(f"Page dimensions: {width:.2f} x {height:.2f} points")
        
        # Display table of contents if available
        toc = doc.get_toc()
        if toc and show_toc:
            click.echo("\nTable of Contents:")
            for entry in toc:
                # Create indented display for hierarchical TOC
                indent = "  " * (entry["level"] - 1)
                click.echo(f"{indent}- {entry['title']} (page {entry['page']})")
        elif show_toc:
            click.echo("\nNo table of contents found in document.")


@cli.command()
@click.argument('image_path', type=click.Path(exists=True))
@click.option('--lang', type=str, help='OCR language')
@click.option('--tessdata-dir', type=click.Path(), help='Tesseract data directory')
@click.option('--tesseract-cmd', type=click.Path(), help='Path to tesseract executable')
@click.option('--output', type=click.Path(), help='Output file (default: print to console)')
@click.pass_context
def ocr(ctx, image_path: str, lang: Optional[str], tessdata_dir: Optional[str], 
        tesseract_cmd: Optional[str], output: Optional[str]):
    """Extract text from an image using OCR."""
    config = ctx.obj['config']
    
    # Get values from config if not provided
    if lang is None:
        lang = config.get('ocr', {}).get('language', 'eng')
    
    if tessdata_dir is None:
        tessdata_dir = config.get('ocr', {}).get('tessdata_dir')
    
    if tesseract_cmd is None:
        tesseract_cmd = config.get('ocr', {}).get('tesseract_cmd')
    
    # Initialize OCR processor
    processor = OCRProcessor(
        language=lang,
        tesseract_cmd=tesseract_cmd,
        tessdata_dir=tessdata_dir,
    )
    
    try:
        text = processor.extract_text(image_path)
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(text)
            click.echo(f"OCR text saved to {output}")
        else:
            click.echo("Extracted text:")
            click.echo("-" * 40)
            click.echo(text)
            click.echo("-" * 40)
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path(), required=False)
@click.option('--use-ai/--no-ai', help='Use AI for transcription')
@click.option('--backend', help='AI backend to use (ollama, llama_cpp, llama_cpp_http)')
@click.option('--model', help='Model name')
@click.option('--dpi', type=int, help='Rendering DPI')
@click.option('--lang', help='OCR language')
@click.option('--tessdata-dir', type=click.Path(), help='Tesseract data directory')
@click.option('--tesseract-cmd', type=click.Path(), help='Path to tesseract executable')
@click.option('--pages', help='Pages to process (comma-separated, 0-based)')
@click.option('--prompt', help='Custom prompt for AI processing')
@click.pass_context
def process(
    ctx,
    pdf_path: str,
    output_dir: Optional[str],
    use_ai: Optional[bool],
    backend: Optional[str],
    model: Optional[str],
    dpi: Optional[int],
    lang: Optional[str],
    tessdata_dir: Optional[str],
    tesseract_cmd: Optional[str],
    pages: Optional[str],
    prompt: Optional[str],
):
    """Process a PDF document through the complete pipeline."""
    config = ctx.obj['config']
    verbose = ctx.obj['verbose']
    
    # Override config with command-line options
    if output_dir is None:
        output_dir = config.get('general', {}).get('output_dir', 'output')
    
    if use_ai is None:
        use_ai = True
    
    if backend is None:
        backend = config.get('intelligence', {}).get('default_backend', 'ollama')
    
    if dpi is None:
        dpi = config.get('rendering', {}).get('dpi', 300)
    
    if lang is None:
        lang = config.get('ocr', {}).get('language', 'eng')
    
    if tessdata_dir is None:
        tessdata_dir = config.get('ocr', {}).get('tessdata_dir')
    
    if tesseract_cmd is None:
        tesseract_cmd = config.get('ocr', {}).get('tesseract_cmd')
    
    if prompt is None:
        prompt = config.get('processing', {}).get('default_prompt', None)
    
    # If model is specified on the command line, update the config
    if model is not None:
        backend_config = config.get('intelligence', {}).get('backends', {}).get(backend, {})
        if 'model' in backend_config:
            backend_config['model'] = model
    
    # Create output directory
    output_dir = Path(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Parse page range if specified
    page_range = None
    if pages:
        try:
            page_range = [int(p.strip()) for p in pages.split(',')]
        except ValueError:
            click.echo("Error: Pages should be comma-separated integers", err=True)
            return
    
    # Initialize OCR processor
    ocr_processor = OCRProcessor(
        language=lang,
        tesseract_cmd=tesseract_cmd,
        tessdata_dir=tessdata_dir,
    )
    
    # Set up renderer options
    renderer_kwargs = {
        "dpi": dpi,
        "alpha": config.get('rendering', {}).get('alpha', False),
        "zoom": config.get('rendering', {}).get('zoom', 1.0),
    }
    
    try:
        # Initialize document processor
        if use_ai:
            try:
                # Create intelligence-based processor
                processor = create_processor(
                    config=config,
                    ocr_processor=ocr_processor,
                    backend_name=backend,
                )
                
                if verbose:
                    click.echo(f"Using AI backend: {backend}")
                
                # Create document processor from core
                document_processor = CoreDocumentProcessor(
                    output_dir=output_dir,
                    renderer_kwargs=renderer_kwargs,
                    ocr_processor=ocr_processor,
                    ai_transcriber=processor,
                )
            
            except Exception as e:
                click.echo(f"Warning: Could not initialize AI backend: {e}")
                click.echo("Falling back to OCR only")
                use_ai = False
                document_processor = CoreDocumentProcessor(
                    output_dir=output_dir,
                    renderer_kwargs=renderer_kwargs,
                    ocr_processor=ocr_processor,
                )
        else:
            # OCR only processor
            document_processor = CoreDocumentProcessor(
                output_dir=output_dir,
                renderer_kwargs=renderer_kwargs,
                ocr_processor=ocr_processor,
            )
        
        # Process the document
        click.echo(f"Processing document: {pdf_path}")
        toc = document_processor.process_pdf(
            pdf_path=pdf_path,
            use_ai=use_ai,
            page_range=page_range,
        )
        
        # Display results
        pdf_path = Path(pdf_path)
        base_filename = pdf_path.stem
        doc_dir = output_dir / base_filename
        
        # Display success message and output locations
        click.echo(f"\nDocument processed successfully!")
        click.echo(f"- Images: {doc_dir}/images/")
        click.echo(f"- Markdown: {doc_dir}/markdown/")
        click.echo(f"- TOC: {doc_dir}/{base_filename}_contents.json")
        
        # Display performance summary
        if "performance" in toc and "stats" in toc:
            perf = toc["performance"]
            stats = toc["stats"]
            
            # Create a performance table
            click.echo("\nPerformance Summary:")
            click.echo("─" * 60)
            click.echo(f"{"Document":20} : {pdf_path.name}")
            click.echo(f"{"Pages Processed":20} : {stats.get('processed_pages', 0)} of {stats.get('total_pages', 0)}")
            
            if use_ai and backend:
                click.echo(f"{"AI Backend":20} : {backend.upper()}")
                click.echo(f"{"Model":20} : {model or 'Default'}")
            else:
                click.echo(f"{"Method":20} : {stats.get('transcription_method', 'unknown').upper()}")
            
            click.echo(f"{"Total Time":20} : {perf.get('total_duration_formatted', 'N/A')}")
            click.echo("─" * 60)
            
            # Display timing for each step
            click.echo("Processing Steps:")
            steps_formatted = perf.get("steps_formatted", {})
            if steps_formatted:
                for step, duration in steps_formatted.items():
                    step_name = step.replace("_", " ").title()
                    click.echo(f"  - {step_name:18} : {duration}")
            
            # Display per-page timing
            click.echo("─" * 60)
            if "avg_render_time_per_page_formatted" in perf and "avg_transcription_time_per_page_formatted" in perf:
                click.echo(f"{"Avg. Render Time":20} : {perf['avg_render_time_per_page_formatted']} per page")
                click.echo(f"{"Avg. Transcription":20} : {perf['avg_transcription_time_per_page_formatted']} per page")
            click.echo("─" * 60)
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.argument('image_path', type=click.Path(exists=True))
@click.option('--backend', help='AI backend to use (ollama, llama_cpp, llama_cpp_http)')
@click.option('--model', help='Model name')
@click.option('--output', type=click.Path(), help='Output file (default: print to console)')
@click.option('--prompt', help='Custom prompt for AI processing')
@click.pass_context
def transcribe(
    ctx,
    image_path: str,
    backend: Optional[str],
    model: Optional[str],
    output: Optional[str],
    prompt: Optional[str],
):
    """Transcribe an image using AI."""
    config = ctx.obj['config']
    verbose = ctx.obj['verbose']
    
    # Get values from config if not provided
    if backend is None:
        backend = config.get('intelligence', {}).get('default_backend', 'ollama')
    
    if prompt is None:
        prompt = config.get('processing', {}).get('default_prompt')
    
    # If model is specified on the command line, update the config
    if model is not None:
        backend_config = config.get('intelligence', {}).get('backends', {}).get(backend, {})
        if 'model' in backend_config:
            backend_config['model'] = model
    
    try:
        # Initialize OCR processor for fallback
        ocr_processor = OCRProcessor(
            language=config.get('ocr', {}).get('language', 'eng'),
            tesseract_cmd=config.get('ocr', {}).get('tesseract_cmd'),
            tessdata_dir=config.get('ocr', {}).get('tessdata_dir'),
        )
        
        # Create intelligence processor
        processor = create_processor(
            config=config,
            ocr_processor=ocr_processor,
            backend_name=backend,
        )
        
        # Get backend info
        backend_name = processor.intelligence.get_name()
        backend_info = processor.intelligence.get_model_info()
        model_name = backend_info.get('name', 'unknown')
        
        click.echo(f"Transcribing with {backend_name} backend")
        if verbose:
            click.echo(f"Model: {model_name}")
        
        # Check if backend supports images
        if not processor.intelligence.supports_image_input() and not processor.use_ocr_fallback:
            click.echo(f"Error: {backend_name} backend doesn't support image transcription.")
            click.echo("Use a multimodal backend or ensure OCR fallback is enabled.")
            return
        
        # Process the image
        text = processor.process_image(image_path, custom_prompt=prompt)
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(text)
            click.echo(f"Transcription saved to {output}")
        else:
            click.echo("Transcription result:")
            click.echo("-" * 40)
            click.echo(text)
            click.echo("-" * 40)
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        
        # Suggest OCR fallback
        click.echo("Try using OCR instead:")
        click.echo(f"  docaitool ocr {image_path}")


@cli.command()
@click.option('--list', 'list_backends', is_flag=True, help='List available intelligence backends')
@click.pass_context
def intelligence(ctx, list_backends):
    """Manage intelligence backends."""
    config = ctx.obj['config']
    
    if list_backends:
        # Create intelligence manager
        manager = IntelligenceManager(config)
        
        # Get available backends
        available = manager.list_available_backends()
        
        # Get configured backends
        configured = []
        intelligence_config = config.get('intelligence', {})
        default_backend = intelligence_config.get('default_backend', 'ollama')
        
        for backend_name, backend_config in intelligence_config.get('backends', {}).items():
            if backend_name in available:
                configured.append({
                    'name': backend_name,
                    'default': backend_name == default_backend,
                    'config': backend_config
                })
        
        # Display information
        click.echo("Available intelligence backends:")
        for backend in configured:
            is_default = " (default)" if backend['default'] else ""
            click.echo(f"  {backend['name']}{is_default}")
            
            # Show configuration details
            for key, value in backend['config'].items():
                if key == 'model' or key == 'model_path' or key == 'base_url':
                    click.echo(f"    {key}: {value}")
        
        # Show unavailable backends
        for backend in available:
            if backend not in [b['name'] for b in configured]:
                click.echo(f"  {backend} (not configured)")


if __name__ == '__main__':
    cli()