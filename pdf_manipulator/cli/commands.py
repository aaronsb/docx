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
from pdf_manipulator.memory.memory_adapter import MemoryConfig
from pdf_manipulator.utils.logging_config import configure_logging


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
    """Document AI Toolkit: Process and analyze documents with AI."""
    # Configure logging first
    configure_logging(
        console_level='DEBUG' if verbose else log_level,
        enable_file=not no_file_log
    )
    
    # Create context object to pass data between commands
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['log_level'] = log_level
    
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
@click.option('--backend', help='AI backend to use (markitdown, ollama, llama_cpp, llama_cpp_http)')
@click.option('--model', help='Model name')
@click.option('--dpi', type=int, help='Rendering DPI')
@click.option('--lang', help='OCR language')
@click.option('--tessdata-dir', type=click.Path(), help='Tesseract data directory')
@click.option('--tesseract-cmd', type=click.Path(), help='Path to tesseract executable')
@click.option('--pages', help='Pages to process (comma-separated, 0-based)')
@click.option('--prompt', help='Custom prompt for AI processing')
@click.option('--memory/--no-memory', help='Store results in memory graph database')
@click.option('--direct/--render', default=None, help='Use direct document conversion (markitdown) or render to images first')
@click.option('--progress/--no-progress', default=True, help='Show progress bars and status updates')
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
    memory: Optional[bool],
    direct: Optional[bool],
    progress: bool,
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
    
    # Process memory option
    if memory is None:
        memory = config.get('memory', {}).get('enabled', False)
    
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
    
    # Set up memory configuration if enabled
    memory_config = None
    intelligence_proc = None
    if memory:
        memory_cfg = config.get('memory', {})
        # Note: database_path will be updated in CoreDocumentProcessor with the actual output path
        memory_config = MemoryConfig(
            database_path=Path(output_dir) / memory_cfg.get('database_name', 'memory_graph.db'),
            domain_name=memory_cfg.get('domain', {}).get('name', 'pdf_processing'),
            domain_description=memory_cfg.get('domain', {}).get('description', 'Domain for PDF document processing'),
            enable_relationships=memory_cfg.get('creation', {}).get('enable_relationships', True),
            enable_summaries=memory_cfg.get('creation', {}).get('enable_summaries', True),
            tags_prefix=memory_cfg.get('creation', {}).get('tags_prefix', 'pdf:'),
            min_content_length=memory_cfg.get('creation', {}).get('min_content_length', 50),
        )
    
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
                
                # Check if we should use direct conversion with markitdown
                if direct is None and backend == "markitdown":
                    direct = True  # Default to direct conversion for markitdown
                elif direct is None:
                    direct = False  # Default to rendering for other backends
                
                # Check if we're doing direct conversion
                pdf_path = Path(pdf_path)
                base_filename = pdf_path.stem
                doc_dir = output_dir / base_filename
                
                if direct and backend == "markitdown":
                    # Direct conversion without rendering
                    click.echo(f"Processing document: {pdf_path} (direct conversion)")
                    
                    # Use the markitdown backend directly
                    from pdf_manipulator.intelligence.markitdown import MarkitdownBackend
                    markitdown_backend = processor.intelligence if isinstance(processor.intelligence, MarkitdownBackend) else MarkitdownBackend()
                    
                    # Process the document directly
                    toc = markitdown_backend.process_direct_document(
                        document_path=pdf_path,
                        output_dir=doc_dir / "markdown",
                        base_filename=base_filename,
                        show_progress=progress,
                    )
                    
                    # Add output directory info
                    toc["output_directory"] = str(doc_dir)
                    
                    # Handle memory storage if enabled
                    if memory and memory_config:
                        click.echo("Memory storage is not yet supported for direct conversion")
                    
                    # Direct conversion completed - skip to display results
                    display_direct_results = True
                else:
                    # Standard processing with rendering
                    display_direct_results = False
                    intelligence_proc = processor
                    document_processor = CoreDocumentProcessor(
                        output_dir=output_dir,
                        renderer_kwargs=renderer_kwargs,
                        ocr_processor=ocr_processor,
                        ai_transcriber=processor,
                        memory_config=memory_config,
                        intelligence_processor=processor if memory_config else None,
                    )
            
            except Exception as e:
                click.echo(f"Warning: Could not initialize AI backend: {e}")
                click.echo("Falling back to OCR only")
                use_ai = False
                document_processor = CoreDocumentProcessor(
                    output_dir=output_dir,
                    renderer_kwargs=renderer_kwargs,
                    ocr_processor=ocr_processor,
                    memory_config=memory_config,
                    intelligence_processor=intelligence_proc,
                )
        else:
            # OCR only processor
            document_processor = CoreDocumentProcessor(
                output_dir=output_dir,
                renderer_kwargs=renderer_kwargs,
                ocr_processor=ocr_processor,
                memory_config=memory_config,
                intelligence_processor=intelligence_proc,
            )
        
        # Process the document (if not already done via direct conversion)
        if 'display_direct_results' not in locals() or not display_direct_results:
            if not (direct and backend == "markitdown"):
                click.echo(f"Processing document: {pdf_path}")
            if memory:
                click.echo("Memory storage enabled")
            toc = document_processor.process_pdf(
                pdf_path=pdf_path,
                use_ai=use_ai,
                page_range=page_range,
                store_in_memory=memory,
                show_progress=progress,
            )
        
        # Display results
        if 'pdf_path' not in locals() or not isinstance(pdf_path, Path):
            pdf_path = Path(pdf_path)
        base_filename = pdf_path.stem
        doc_dir = output_dir / base_filename
        
        # Display success message and output locations
        click.echo(f"\nDocument processed successfully!")
        
        # Check if we used direct conversion or standard processing
        if 'display_direct_results' in locals() and display_direct_results:
            # Direct conversion results
            click.echo(f"- Markdown: {doc_dir}/markdown/")
            if toc.get("output_files", {}).get("markdown"):
                click.echo(f"  Main file: {toc['output_files']['markdown']}")
        else:
            # Standard processing results
            click.echo(f"- Images: {doc_dir}/images/")
            click.echo(f"- Markdown: {doc_dir}/markdown/")
        
        click.echo(f"- TOC: {doc_dir}/{base_filename}_contents.json")
        
        # Display memory storage information if enabled
        if memory and "memory_storage" in toc and toc["memory_storage"].get("enabled"):
            memory_info = toc["memory_storage"]
            click.echo(f"- Memory DB: {memory_info.get('database_path')}")
            click.echo(f"  Document ID: {memory_info.get('document_id')}")
            click.echo(f"  Pages stored: {len(memory_info.get('page_memories', {}))}")
            click.echo(f"  Sections found: {len(memory_info.get('section_memories', {}))}")
        
        # Display performance summary (if available for standard processing)
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
        
        # Display content statistics for direct conversion
        elif "content_stats" in toc:
            stats = toc["content_stats"]
            click.echo("\nContent Statistics:")
            click.echo("─" * 60)
            click.echo(f"{"Document":20} : {pdf_path.name}")
            click.echo(f"{"Backend":20} : {backend.upper()}")
            click.echo(f"{"Conversion Mode":20} : Direct (markitdown)")
            click.echo(f"{"Total Characters":20} : {stats.get('total_characters', 0):,}")
            click.echo(f"{"Total Words":20} : {stats.get('total_words', 0):,}")
            click.echo(f"{"Total Lines":20} : {stats.get('total_lines', 0):,}")
            click.echo("─" * 60)
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.argument('image_path', type=click.Path(exists=True))
@click.option('--backend', help='AI backend to use (markitdown, ollama, llama_cpp, llama_cpp_http)')
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


@cli.command()
@click.argument('subcommand', type=click.Choice(['create', 'query', 'export', 'info']))
@click.argument('args', nargs=-1)
@click.option('--database', '-d', type=click.Path(), help='Path to memory database')
@click.option('--query', '-q', help='Search query for memory operations')
@click.option('--limit', type=int, default=10, help='Limit results (default: 10)')
@click.option('--output', '-o', type=click.Path(), help='Output file for export')
@click.pass_context
def memory(ctx, subcommand: str, args: tuple, database: Optional[str], query: Optional[str], limit: int, output: Optional[str]):
    """Manage memory graph databases.
    
    Examples:
        pdfx memory create output/memory_graph.db
        pdfx memory query output/memory_graph.db --query "search term"
        pdfx memory info output/memory_graph.db
        pdfx memory export output/memory_graph.db --output export.json
    """
    from pdf_manipulator.memory.memory_adapter import MemoryAdapter, MemoryConfig
    from pdf_manipulator.memory.memory_processor import MemoryProcessor
    import json
    from datetime import datetime
    
    config = ctx.obj['config']
    
    # Get database path
    if not database and len(args) > 0:
        database = args[0]
    
    if not database and subcommand != 'create':
        click.echo("Error: Database path required", err=True)
        return
    
    try:
        if subcommand == 'create':
            # Create a new memory database
            db_path = database or (args[0] if args else 'memory_graph.db')
            
            memory_config = MemoryConfig(
                database_path=Path(db_path),
                domain_name=config.get('memory', {}).get('domain', {}).get('name', 'pdf_processing'),
                domain_description=config.get('memory', {}).get('domain', {}).get('description', 'PDF document processing'),
            )
            
            # Initialize database
            adapter = MemoryAdapter(memory_config)
            adapter.connect()
            adapter.disconnect()
            
            click.echo(f"Created memory database: {db_path}")
            
        elif subcommand == 'query':
            # Query memory database
            if not query:
                click.echo("Error: --query option required", err=True)
                return
            
            memory_config = MemoryConfig(database_path=Path(database))
            adapter = MemoryAdapter(memory_config)
            adapter.connect()
            
            # Search memories
            results = adapter.search_memories(query, limit=limit)
            
            click.echo(f"Found {len(results)} memories matching '{query}':")
            for i, memory in enumerate(results):
                click.echo(f"\n{i+1}. {memory['path']}")
                click.echo(f"   ID: {memory['id'][:8]}...")
                click.echo(f"   Tags: {', '.join(memory['tags'])}")
                content_preview = memory['content'][:200] + "..." if len(memory['content']) > 200 else memory['content']
                click.echo(f"   Content: {content_preview}")
                if memory.get('content_summary'):
                    click.echo(f"   Summary: {memory['content_summary']}")
            
            adapter.disconnect()
            
        elif subcommand == 'info':
            # Show database information
            memory_config = MemoryConfig(database_path=Path(database))
            adapter = MemoryAdapter(memory_config)
            adapter.connect()
            
            # Get database statistics
            cursor = adapter.conn.execute("SELECT COUNT(*) FROM MEMORY_NODES")
            node_count = cursor.fetchone()[0]
            
            cursor = adapter.conn.execute("SELECT COUNT(*) FROM MEMORY_EDGES")
            edge_count = cursor.fetchone()[0]
            
            cursor = adapter.conn.execute("SELECT COUNT(DISTINCT domain) FROM MEMORY_NODES")
            domain_count = cursor.fetchone()[0]
            
            cursor = adapter.conn.execute("SELECT id, name FROM DOMAINS")
            domains = cursor.fetchall()
            
            click.echo(f"Memory database: {database}")
            click.echo(f"Total memories: {node_count}")
            click.echo(f"Total relationships: {edge_count}")
            click.echo(f"Domains: {domain_count}")
            
            if domains:
                click.echo("\nAvailable domains:")
                for domain_id, domain_name in domains:
                    cursor = adapter.conn.execute(
                        "SELECT COUNT(*) FROM MEMORY_NODES WHERE domain = ?",
                        (domain_id,)
                    )
                    count = cursor.fetchone()[0]
                    click.echo(f"  - {domain_name}: {count} memories")
            
            # Recent memories
            recent = adapter.get_recent_memories(limit=5)
            if recent:
                click.echo("\nRecent memories:")
                for i, memory in enumerate(recent):
                    click.echo(f"  {i+1}. {memory['path']} ({memory['timestamp']})")
            
            adapter.disconnect()
            
        elif subcommand == 'export':
            # Export memory database
            if not output:
                output = database.replace('.db', '_export.json')
            
            memory_config = MemoryConfig(database_path=Path(database))
            
            with MemoryProcessor(memory_config) as processor:
                # Get all memories
                adapter = processor.adapter
                cursor = adapter.conn.execute(
                    """SELECT m.*, GROUP_CONCAT(mt.tag) as tags
                       FROM MEMORY_NODES m
                       LEFT JOIN MEMORY_TAGS mt ON m.id = mt.nodeId
                       GROUP BY m.id"""
                )
                
                memories = []
                for row in cursor:
                    memory = {
                        'id': row[0],
                        'domain': row[1],
                        'content': row[2],
                        'timestamp': row[3],
                        'path': row[4],
                        'content_summary': row[5],
                        'tags': row[7].split(',') if row[7] else []
                    }
                    memories.append(memory)
                
                # Get relationships
                cursor = adapter.conn.execute("SELECT * FROM MEMORY_EDGES")
                edges = []
                for row in cursor:
                    edge = {
                        'id': row[0],
                        'source': row[1],
                        'target': row[2],
                        'type': row[3],
                        'strength': row[4],
                        'timestamp': row[5],
                        'domain': row[6]
                    }
                    edges.append(edge)
                
                # Export data
                export_data = {
                    'memories': memories,
                    'relationships': edges,
                    'metadata': {
                        'exported_at': datetime.now().isoformat(),
                        'total_memories': len(memories),
                        'total_relationships': len(edges)
                    }
                }
                
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2)
                
                click.echo(f"Exported {len(memories)} memories to {output}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


if __name__ == '__main__':
    cli()