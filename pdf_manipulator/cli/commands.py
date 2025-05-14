"""Command-line interface for document AI toolkit."""
import os
from pathlib import Path
from typing import Optional, List

import click
from tqdm import tqdm

from pdf_manipulator.core.document import PDFDocument
from pdf_manipulator.renderers.image_renderer import ImageRenderer
from pdf_manipulator.extractors.ocr import OCRProcessor, DocumentAnalyzer
from pdf_manipulator.extractors.ai_transcription import OllamaTranscriber, LlamaTranscriber, DocumentTranscriber
from pdf_manipulator.core.pipeline import DocumentProcessor


@click.group()
def cli():
    """Document AI Toolkit: Process and analyze documents with AI."""
    pass


@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
@click.option('--dpi', type=int, default=300, help='Resolution in DPI')
@click.option('--alpha/--no-alpha', default=False, help='Include alpha channel')
@click.option('--zoom', type=float, default=1.0, help='Additional zoom factor')
@click.option('--page', type=int, help='Specific page to render (0-based)')
@click.option('--prefix', type=str, default='page_', help='Filename prefix for output images')
def render(
    pdf_path: str, 
    output_dir: str, 
    dpi: int,
    alpha: bool,
    zoom: float,
    page: Optional[int],
    prefix: str,
):
    """Render PDF pages to PNG images."""
    output_dir = Path(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
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
def info(pdf_path: str, show_toc: bool):
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
@click.option('--lang', type=str, default='eng', help='OCR language')
@click.option('--tessdata-dir', type=click.Path(exists=True), help='Tesseract data directory')
@click.option('--tesseract-cmd', type=click.Path(exists=True), help='Path to tesseract executable')
@click.option('--output', type=click.Path(), help='Output file (default: print to console)')
def ocr(image_path: str, lang: str, tessdata_dir: Optional[str], tesseract_cmd: Optional[str], output: Optional[str]):
    """Extract text from an image using OCR."""
    # Initialize OCR processor with provided configuration
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
@click.argument('output_dir', type=click.Path())
@click.option('--use-ai/--no-ai', default=True, help='Use AI for transcription')
@click.option('--model', type=str, default='llava:latest', help='AI model name (for Ollama)')
@click.option('--dpi', type=int, default=300, help='Rendering DPI')
@click.option('--lang', type=str, default='eng', help='OCR language')
@click.option('--tessdata-dir', type=click.Path(exists=True), help='Tesseract data directory')
@click.option('--tesseract-cmd', type=click.Path(exists=True), help='Path to tesseract executable')
@click.option('--pages', type=str, help='Pages to process (comma-separated, 0-based)')
def process(
    pdf_path: str,
    output_dir: str,
    use_ai: bool,
    model: str,
    dpi: int,
    lang: str,
    tessdata_dir: Optional[str],
    tesseract_cmd: Optional[str],
    pages: Optional[str],
):
    """Process a PDF document through the complete pipeline."""
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

    # Initialize processors
    ocr_processor = OCRProcessor(
        language=lang,
        tesseract_cmd=tesseract_cmd,
        tessdata_dir=tessdata_dir,
    )
    
    # Initialize AI transcriber if requested
    ai_transcriber = None
    if use_ai:
        try:
            # Check if Ollama is available
            transcriber = OllamaTranscriber(model_name=model)
            
            # Create document transcriber with OCR fallback
            ai_transcriber = DocumentTranscriber(
                transcriber=transcriber,
                use_ocr_fallback=True,
                ocr_fallback=ocr_processor.extract_text,
            )
            
            click.echo(f"Using Ollama with model: {model}")
        
        except Exception as e:
            click.echo(f"Warning: Could not initialize AI transcriber: {e}")
            click.echo("Falling back to OCR only")
            use_ai = False
    
    # Set up renderer options
    renderer_kwargs = {
        "dpi": dpi,
        "alpha": False,
        "zoom": 1.0,
    }
    
    # Create document processor
    processor = DocumentProcessor(
        output_dir=output_dir,
        renderer_kwargs=renderer_kwargs,
        ocr_processor=ocr_processor,
        ai_transcriber=ai_transcriber,
    )
    
    try:
        click.echo(f"Processing document: {pdf_path}")
        toc = processor.process_pdf(
            pdf_path=pdf_path,
            use_ai=use_ai,
            page_range=page_range,
        )
        
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
@click.option('--model', type=str, default='llava:latest', help='AI model name')
@click.option('--output', type=click.Path(), help='Output file (default: print to console)')
@click.option('--prompt', type=str, help='Custom prompt for transcription')
def transcribe(image_path: str, model: str, output: Optional[str], prompt: Optional[str]):
    """Transcribe an image using AI."""
    try:
        transcriber = OllamaTranscriber(model_name=model)
        default_prompt = "Transcribe all text in this document image to markdown format. Preserve layout and formatting as best as possible."
        
        click.echo(f"Transcribing image with model: {model}")
        text = transcriber.transcribe_image(image_path, prompt or default_prompt)
        
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


if __name__ == '__main__':
    cli()