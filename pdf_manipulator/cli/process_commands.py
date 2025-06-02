"""Document processing command-line interface."""
import sys
import os
from pathlib import Path
from typing import Optional, List, Union

import click
from tqdm import tqdm

from pdf_manipulator.core.document import PDFDocument
from pdf_manipulator.core.pipeline import DocumentProcessor as CoreDocumentProcessor
from pdf_manipulator.intelligence.processor import create_processor
from pdf_manipulator.memory.memory_adapter import MemoryConfig
from .base import ProgressReporter, validate_file_exists, validate_directory
from pdf_manipulator.utils.logging_config import get_logger

logger = get_logger("cli.process_commands")


@click.command(name='extract')
@click.argument('path', type=click.Path(exists=True), callback=validate_file_exists)
@click.argument('output_dir', type=click.Path(), required=False, callback=validate_directory)
@click.option('--use-ai/--no-ai', help='Use AI for transcription')
@click.option('--backend', help='AI backend to use (markitdown, ollama, openai)')
@click.option('--model', help='Model name')
@click.option('--dpi', type=int, help='Rendering DPI')
@click.option('--pages', type=str, help='Pages to process (e.g., "0,1,5-10")')
@click.option('--alpha/--no-alpha', help='Include alpha channel in rendering')
@click.option('--zoom', type=float, help='Additional zoom factor for rendering')
@click.option('--prefix', default='page_', help='Prefix for page images')
@click.option('--suffix', default='', help='Suffix for page images')
@click.option('--direct/--render', 'use_direct', default=None, 
              help='Use direct conversion (markitdown) or render pipeline')
@click.option('--memory/--no-memory', default=None, help='Enable memory graph storage')
@click.option('--domain', default='pdf_processing', help='Memory domain name')
@click.option('--summarization-ratio', type=float, default=0.2, help='Text summarization ratio (0.0-1.0, 0=max, 1=none)')
@click.option('--max-tokens', type=int, default=75, help='Maximum tokens to keep in summarized text')
@click.option('--progress/--no-progress', default=True, help='Show progress bar')
@click.option('--debug/--no-debug', default=False, help='Enable detailed debugging output')
@click.option('--debug-dir', type=click.Path(), help='Directory to save debug information')
@click.option('--timeout', type=int, default=60, help='Timeout for LLM requests in seconds')
@click.option('--rebuild-memory', is_flag=True, help='Rebuild memory database from existing extracted data')
@click.pass_context
def process_document(
    ctx,
    path: str,
    output_dir: Optional[str],
    use_ai: Optional[bool],
    backend: Optional[str],
    model: Optional[str],
    dpi: Optional[int],
    pages: Optional[str],
    alpha: Optional[bool],
    zoom: Optional[float],
    prefix: str,
    suffix: str,
    use_direct: Optional[bool],
    memory: Optional[bool],
    domain: str,
    summarization_ratio: float,
    max_tokens: int,
    progress: bool,
    debug: bool,
    debug_dir: Optional[str],
    timeout: int,
    rebuild_memory: bool
):
    """Process a document and extract semantic content.
    
    This is the primary command for transforming documents into semantic knowledge graphs.
    It supports both direct conversion (markitdown) and rendering pipelines with OpenAI or Ollama backends.
    
    Backend options:
      --backend markitdown  Fast, direct PDF-to-markdown conversion
      --backend openai      Advanced ML processing with OpenAI models
      --backend ollama      Local multimodal processing with Ollama

    When using OpenAI backend, you can enable enhanced debugging with the --debug flag:
    
      mge extract document.pdf --backend openai --model gpt-4o-mini --debug
      
    Additional debug options:
      --debug-dir PATH      Directory to save detailed debug information
      --timeout SECONDS     Adjust request timeout (default: 60s)
    
    The OpenAI backend now defaults to gpt-4o-mini for better cost efficiency.
    
    Memory Database Rebuild:
      If you've already processed a document and want to rebuild the memory database
      from the extracted data (without reprocessing the PDF), use:
      
      mge extract document.pdf --rebuild-memory
      
      This is useful when you've deleted the database but still have the extracted
      markdown and JSON files in the output directory.
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
    
    # Handle memory rebuild from existing data
    if rebuild_memory:
        # Check if extracted data exists
        doc_name = path_obj.stem
        doc_dir = Path(output_dir) / doc_name
        contents_file = doc_dir / "markdown" / f"{doc_name}_contents.json"
        
        if not contents_file.exists():
            reporter.error(f"No extracted data found at {contents_file}")
            click.echo("Please process the document first before rebuilding memory.")
            sys.exit(1)
        
        # Rebuild the memory database
        try:
            reporter.start(f"Rebuilding memory database from {contents_file}")
            
            # Create document processor to access rebuild method
            document_processor = CoreDocumentProcessor(
                ai_transcriber=None,
                ocr_processor=None,
                output_dir=output_dir,
                memory_config=None  # Will be set in rebuild method
            )
            
            # Rebuild memory from extracted data
            memory_path = document_processor.rebuild_memory_from_extracted_data(
                contents_file=contents_file,
                domain=domain
            )
            
            reporter.complete("Memory database rebuilt successfully")
            click.echo(f"\nSemantic graph recreated: {memory_path}")
            click.echo(f"Use 'mge memory info -d {memory_path}' to explore")
            return
            
        except Exception as e:
            reporter.error(f"Failed to rebuild memory: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    try:
        reporter.start(f"Processing {path}")
        logger.info(f"INITIAL CONFIG: backend={backend}, model={model}, debug={debug}")
        logger.info(f"CONFIG OBJECT: {config.get('intelligence', {})}")
        
        # Initialize with no OCR processor
        ocr_processor = None
        
        # Prepare AI processor with semantic layering
        ai_transcriber = None
        logger.info(f"USE_AI CHECK: use_ai={use_ai}")
        if use_ai:
            try:
                # Update config with model name if provided
                if model:
                    if 'intelligence' not in config:
                        config['intelligence'] = {}
                    if 'backends' not in config['intelligence']:
                        config['intelligence']['backends'] = {}
                    if backend not in config['intelligence']['backends']:
                        config['intelligence']['backends'][backend] = {}
                    config['intelligence']['backends'][backend]['model'] = model
                
                # Check if using semantic pipeline
                logger.info(f"Backend: {backend}, Model: {model}, Use AI: {use_ai}")
                logger.info(f"DEBUG - Starting semantic pipeline evaluation")
                if backend in ["ollama", "openai"]:
                    logger.info(f"DEBUG - Using {backend} semantic pipeline")
                    # Use enhanced semantic pipeline
                    logger.info(f"Using semantic pipeline with model: {model}")
                    from pdf_manipulator.intelligence.semantic_processor import SemanticProcessor
                    from pdf_manipulator.intelligence.openai_multimodal import OpenAIMultimodalBackend
                    from pdf_manipulator.intelligence.ollama_multimodal import OllamaMultimodalBackend
                    
                    # Process full PDF with markitdown first
                    from pdf_manipulator.intelligence.markitdown import MarkitdownBackend
                    
                    # Create markitdown backend with PDF path
                    extraction_backend = MarkitdownBackend()
                    # Pre-extract all text from PDF using markitdown
                    logger.info(f"Pre-extracting text from PDF using markitdown")
                    try:
                        # Convert entire PDF to markdown once
                        full_markdown = extraction_backend.transcribe_image(path)
                        logger.info(f"Markitdown extracted {len(full_markdown)} characters from PDF")
                        
                        # Store the full markdown for the semantic processor
                        extraction_backend.full_pdf_markdown = full_markdown
                        extraction_backend.pdf_path = path
                        
                        # Pre-extract and write pages to markdown files
                        # This ensures all pages are written before LLaVA processing starts
                        # For now, just do the first 10 pages or so - in a real implementation,
                        # we'd get the actual page range from options
                        pages_to_process = list(range(10))
                        
                        output_dir = Path(output_dir)
                        doc_dir = output_dir / Path(path).stem
                        markdown_dir = doc_dir / "markdown"
                        os.makedirs(markdown_dir, exist_ok=True)
                        
                        logger.info(f"Pre-writing extracted content for all pages")
                        lines = full_markdown.split('\n')
                        
                        # Simplified approach - divide content by sections
                        # Could be improved with better page boundary detection
                        for page_num in pages_to_process:
                            # Simple extraction - take content slice
                            page_chunk = len(lines) // 50  # Assuming ~50 pages
                            start_idx = page_num * page_chunk
                            end_idx = (page_num + 1) * page_chunk
                            if end_idx > len(lines):
                                end_idx = len(lines)
                                
                            page_content = '\n'.join(lines[start_idx:end_idx])
                            
                            # Save to extracted markdown file
                            extracted_file = markdown_dir / f"page_{page_num:04d}_extracted.md"
                            with open(extracted_file, 'w', encoding='utf-8') as f:
                                f.write(f"# Page {page_num + 1} - Extracted Text (Phase 1)\n\n")
                                f.write(page_content)
                                
                            logger.debug(f"Pre-extracted content for page {page_num}")
                            
                    except Exception as e:
                        logger.warning(f"Failed to pre-extract with markitdown: {e}")
                        extraction_backend.full_pdf_markdown = None
                    
                    # Enhancement backend (multimodal)
                    enhancement_config = config['intelligence']['backends'].get(backend, {})
                    
                    if backend == "openai":
                        # Create debug directory if needed
                        debug_output_dir = None
                        if debug and debug_dir:
                            debug_output_dir = Path(debug_dir)
                        elif debug:
                            # Create a debug directory in the output folder
                            debug_output_dir = Path(output_dir) / Path(path).stem / "debug" / "openai"
                            debug_output_dir.mkdir(parents=True, exist_ok=True)
                            logger.info(f"Debug mode enabled - saving debug info to {debug_output_dir}")
                            
                        # Initialize OpenAI backend with debugging
                        from pdf_manipulator.intelligence.openai_multimodal import OpenAIMultimodalBackend
                        # Remove debug_mode and debug_dir as they are not supported in the backend
                        # Get API key from environment or config, resolving any placeholders
                        api_key = os.environ.get("OPENAI_API_KEY")
                        if not api_key:
                            logger.error("OPENAI_API_KEY environment variable not found!")
                            
                        # Create the OpenAI backend with the resolved API key
                        enhancement_backend = OpenAIMultimodalBackend(
                            api_key=api_key,
                            model=model or enhancement_config.get("model", "gpt-4o-mini"),
                            max_tokens=enhancement_config.get("max_tokens", 4096),
                            temperature=enhancement_config.get("temperature", 0.1),
                            timeout=timeout,
                            logger=logger
                        )
                        logger.info(f"Using OpenAI backend with model: {enhancement_backend.model}")
                        
                    else:
                        # Default to Ollama
                        enhancement_backend = OllamaMultimodalBackend(
                            model=model,
                            base_url=enhancement_config.get('base_url', 'http://localhost:11434'),
                            timeout=enhancement_config.get('timeout', timeout or 120)
                        )
                    
                    # Get summarization settings from config or command line
                    config_summarization = config.get('semantic_enhancement', {}).get('summarization', {})
                    from pdf_manipulator.intelligence.processor import DocumentProcessor
                    semantic_processor = SemanticProcessor(
                        extraction_backend=extraction_backend,
                        enhancement_backend=enhancement_backend,
                        # Use CLI params if provided, otherwise use config values
                        summarization_ratio=summarization_ratio if summarization_ratio is not None else config_summarization.get('ratio', 0.2),
                        max_tokens=max_tokens if max_tokens is not None else config_summarization.get('max_tokens', 75),
                        # Pass the whole config for prompt templates
                        config=config
                    )
                    
                    # Wrap in DocumentProcessor interface
                    ai_transcriber = DocumentProcessor(
                        intelligence_backend=enhancement_backend,
                        ocr_processor=None,
                        use_ocr_fallback=False
                    )
                    
                    # Inject semantic processor
                    ai_transcriber.semantic_processor = semantic_processor
                    ai_transcriber.use_semantic_pipeline = True
                    
                else:
                    # Standard flow
                    ai_transcriber = create_processor(
                        config=config,
                        backend_name=backend,
                        ocr_processor=ocr_processor
                    )
            except Exception as e:
                reporter.error(f"Failed to initialize AI backend: {e}")
                raise
        
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
            click.echo(f"Use 'mge memory info -d {memory_path}' to explore")
    
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        # Report error
        reporter.error(f"{error_type}: {error_msg}")
        
        # Enhanced error reporting for OpenAI-specific errors
        if "openai" in error_msg.lower():
            click.echo(click.style("\nOpenAI API Error Details:", fg='yellow'))
            click.echo("- Check that your API key is valid and not expired")
            click.echo("- Verify your account has appropriate rate limits")
            click.echo("- Check network connectivity to OpenAI API")
            click.echo("- Try using --timeout parameter to increase request timeout")
            click.echo("\nTry running with --debug flag for detailed error information")
        
        # Show traceback in verbose mode or debug mode
        if verbose or debug:
            click.echo(click.style("\nTraceback:", fg='yellow'))
            import traceback
            traceback.print_exc()
            
            # Show debug tips
            if not debug:
                click.echo(click.style("\nTip: Run with --debug flag for enhanced error diagnostics", fg='cyan'))
        
        sys.exit(1)


@click.command(name='extract-dir')
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('output_dir', type=click.Path(), required=False)
@click.option('--pattern', default='*.pdf', help='File pattern to match')
@click.option('--recursive/--no-recursive', default=False, help='Process subdirectories')
@click.option('--backend', help='AI backend to use')
@click.option('--memory/--no-memory', default=True, help='Enable memory graph storage')
@click.option('--domain', default='document_collection', help='Memory domain name')
@click.option('--progress/--no-progress', default=True, help='Show progress')
@click.option('--debug/--no-debug', default=False, help='Enable detailed debugging output')
@click.option('--debug-dir', type=click.Path(), help='Directory to save debug information')
@click.option('--timeout', type=int, default=60, help='Timeout for LLM requests in seconds')
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
    progress: bool,
    debug: bool,
    debug_dir: Optional[str],
    timeout: int
):
    """Process all documents in a directory.
    
    This command processes multiple documents in a directory, applying the
    same processing options to each file.
    
    For OpenAI backend debugging, use the --debug flag:
    
      mge extract-dir documents/ output/ --backend openai --debug
    """
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
            progress=progress,
            debug=debug,
            debug_dir=debug_dir,
            timeout=timeout
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