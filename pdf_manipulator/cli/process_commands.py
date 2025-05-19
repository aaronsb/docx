"""Document processing command-line interface."""
import sys
from pathlib import Path
from typing import Optional, List, Union

import click
from tqdm import tqdm

from pdf_manipulator.core.document import PDFDocument
from pdf_manipulator.core.pipeline import DocumentProcessor as CoreDocumentProcessor
from pdf_manipulator.intelligence.processor import create_processor
from pdf_manipulator.memory.memory_adapter import MemoryConfig
from pdf_manipulator.extractors.ocr import OCRProcessor
from .base import ProgressReporter, validate_file_exists, validate_directory


@click.command(name='process')
@click.argument('path', type=click.Path(exists=True), callback=validate_file_exists)
@click.argument('output_dir', type=click.Path(), required=False, callback=validate_directory)
@click.option('--use-ai/--no-ai', help='Use AI for transcription')
@click.option('--backend', help='AI backend to use (markitdown, ollama, llama_cpp, llama_cpp_http)')
@click.option('--model', help='Model name')
@click.option('--dpi', type=int, help='Rendering DPI')
@click.option('--lang', help='OCR language')
@click.option('--tessdata-dir', type=click.Path(), help='Tesseract data directory')
@click.option('--tesseract-cmd', type=click.Path(), help='Path to tesseract executable')
@click.option('--pages', type=str, help='Pages to process (e.g., "0,1,5-10")')
@click.option('--alpha/--no-alpha', help='Include alpha channel in rendering')
@click.option('--zoom', type=float, help='Additional zoom factor for rendering')
@click.option('--prefix', default='page_', help='Prefix for page images')
@click.option('--suffix', default='', help='Suffix for page images')
@click.option('--ocr-fallback/--no-ocr-fallback', default=True, help='Use OCR if AI fails')
@click.option('--direct/--render', 'use_direct', default=None, 
              help='Use direct conversion (markitdown) or render pipeline')
@click.option('--memory/--no-memory', default=None, help='Enable memory graph storage')
@click.option('--domain', default='pdf_processing', help='Memory domain name')
@click.option('--progress/--no-progress', default=True, help='Show progress bar')
@click.pass_context
def process_document(
    ctx,
    path: str,
    output_dir: Optional[str],
    use_ai: Optional[bool],
    backend: Optional[str],
    model: Optional[str],
    dpi: Optional[int],
    lang: Optional[str],
    tessdata_dir: Optional[str],
    tesseract_cmd: Optional[str],
    pages: Optional[str],
    alpha: Optional[bool],
    zoom: Optional[float],
    prefix: str,
    suffix: str,
    ocr_fallback: bool,
    use_direct: Optional[bool],
    memory: Optional[bool],
    domain: str,
    progress: bool
):
    """Process a document and extract semantic content.
    
    This is the primary command for transforming documents into semantic knowledge graphs.
    It supports both direct conversion (markitdown) and rendering pipelines.
    """
    config = ctx.obj['config']
    verbose = ctx.obj.get('verbose', False)
    reporter = ProgressReporter(verbose)
    
    # Determine if path is file or directory
    path_obj = Path(path)
    
    if path_obj.is_dir():
        click.echo("Directory processing moved to 'process-dir' command", err=True)
        sys.exit(1)
    
    # Default output directory
    if output_dir is None:
        output_dir = config.get('general', {}).get('output_dir', 'output')
    
    # Process options from config and command line
    backend = backend or config.get('intelligence', {}).get('default_backend', 'markitdown')
    use_ai = use_ai if use_ai is not None else (backend != 'none')
    memory = memory if memory is not None else config.get('memory', {}).get('enabled', True)
    
    # Determine processing mode
    if use_direct is None:
        # Auto-detect based on backend
        use_direct = (backend == 'markitdown' and not pages)
    
    # Parse page range
    page_list = None
    if pages:
        page_list = _parse_page_range(pages)
    
    try:
        reporter.start(f"Processing {path}")
        
        # Prepare OCR processor
        ocr_processor = None
        if ocr_fallback or not use_ai:
            ocr_processor = OCRProcessor(
                language=lang or config.get('ocr', {}).get('language', 'eng'),
                tessdata_dir=tessdata_dir or config.get('ocr', {}).get('tessdata_dir'),
                tesseract_cmd=tesseract_cmd or config.get('ocr', {}).get('tesseract_cmd')
            )
        
        # Prepare AI processor
        ai_transcriber = None
        if use_ai:
            try:
                ai_transcriber = create_processor(
                    config=config,
                    backend_name=backend,
                    model_name=model,
                    ocr_processor=ocr_processor
                )
            except Exception as e:
                reporter.error(f"Failed to initialize AI backend: {e}")
                if not ocr_fallback:
                    raise
                click.echo("Falling back to OCR only", err=True)
                use_ai = False
        
        # Prepare memory configuration
        memory_config = None
        if memory:
            memory_path = Path(output_dir) / Path(path).stem / "memory_graph.db"
            memory_config = MemoryConfig(
                database_path=memory_path,
                domain_name=domain,
                domain_description=f"Semantic graph for {Path(path).name}",
                enable_relationships=config.get('memory', {}).get('creation', {}).get('enable_relationships', True),
                enable_summaries=config.get('memory', {}).get('creation', {}).get('enable_summaries', True)
            )
        
        # Set up processor initialization parameters
        init_kwargs = {
            'output_dir': output_dir,
            'memory_config': memory_config,
            'renderer_kwargs': {
                'dpi': dpi or config.get('rendering', {}).get('dpi', 300),
                'alpha': alpha if alpha is not None else config.get('rendering', {}).get('alpha', False),
                'zoom': zoom or config.get('rendering', {}).get('zoom', 1.0)
            }
        }
        
        # Create document processor
        document_processor = CoreDocumentProcessor(
            ai_transcriber=ai_transcriber,
            ocr_processor=ocr_processor,
            **init_kwargs
        )
        
        # Process the document with runtime parameters
        toc = document_processor.process_pdf(
            pdf_path=path,
            use_ai=use_ai,
            page_range=page_list,
            store_in_memory=memory,
            show_progress=progress
        )
        
        reporter.complete("Processing complete")
        
        # Display TOC summary if verbose
        if verbose and toc.get('entries'):
            click.echo("\nTable of Contents:")
            for entry in toc['entries']:
                indent = "  " * entry.get('level', 0)
                click.echo(f"{indent}{entry.get('number', '')} {entry.get('title', '')} (p{entry.get('page', '')})")
        
        # Show memory info if created
        if memory and memory_path.exists():
            click.echo(f"\nSemantic graph created: {memory_path}")
            click.echo(f"Use 'pdfx memory info -d {memory_path}' to explore")
    
    except Exception as e:
        reporter.error(str(e))
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@click.command(name='process-dir')
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('output_dir', type=click.Path(), required=False)
@click.option('--pattern', default='*.pdf', help='File pattern to match')
@click.option('--recursive/--no-recursive', default=False, help='Process subdirectories')
@click.option('--backend', help='AI backend to use')
@click.option('--memory/--no-memory', default=True, help='Enable memory graph storage')
@click.option('--domain', default='document_collection', help='Memory domain name')
@click.option('--progress/--no-progress', default=True, help='Show progress')
@click.pass_context
def process_directory(
    ctx,
    directory: str,
    output_dir: Optional[str],
    pattern: str,
    recursive: bool,
    backend: Optional[str],
    memory: bool,
    domain: str,
    progress: bool
):
    """Process all documents in a directory."""
    config = ctx.obj['config']
    verbose = ctx.obj.get('verbose', False)
    reporter = ProgressReporter(verbose)
    
    if output_dir is None:
        output_dir = config.get('general', {}).get('output_dir', 'output')
    
    # Find matching files
    path = Path(directory)
    if recursive:
        files = list(path.rglob(pattern))
    else:
        files = list(path.glob(pattern))
    
    if not files:
        click.echo(f"No files matching '{pattern}' found in {directory}")
        return
    
    reporter.start(f"Found {len(files)} files to process")
    
    # Process each file
    for i, file_path in enumerate(files):
        click.echo(f"\nProcessing {i+1}/{len(files)}: {file_path.name}")
        
        ctx.invoke(
            process_document,
            path=str(file_path),
            output_dir=output_dir,
            backend=backend,
            memory=memory,
            domain=domain,
            progress=progress
        )
    
    reporter.complete(f"Processed {len(files)} files")


def _parse_page_range(pages_str: str) -> List[int]:
    """Parse page range string into list of page numbers.
    
    Examples:
        "0,1,2" -> [0, 1, 2]
        "0-5" -> [0, 1, 2, 3, 4, 5]
        "0,2-5,10" -> [0, 2, 3, 4, 5, 10]
    """
    page_list = []
    for part in pages_str.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            page_list.extend(range(start, end + 1))
        else:
            page_list.append(int(part))
    return sorted(set(page_list))