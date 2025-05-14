"""Command-line interface for PDF manipulator."""
import os
from pathlib import Path
from typing import Optional

import click
from tqdm import tqdm

from pdf_manipulator.core.document import PDFDocument
from pdf_manipulator.renderers.image_renderer import ImageRenderer


@click.group()
def cli():
    """PDF Manipulator: a toolkit for PDF operations."""
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
def info(pdf_path: str):
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


if __name__ == '__main__':
    cli()