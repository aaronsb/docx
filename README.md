# PDF Manipulator

A modular Python toolkit for PDF manipulation with capabilities including:

- Rendering PDF pages to PNG images
- Extracting text and metadata
- More features to be added...

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pdf_manipulator.git
cd pdf_manipulator

# Install the package
pip install -e .
```

## Usage

### Command Line Interface

Render PDF pages to PNG images:

```bash
# Render all pages of a PDF
pdf-manipulator render document.pdf output_directory/ --dpi 300

# Render a specific page (0-based index)
pdf-manipulator render document.pdf output_directory/ --page 0 --dpi 300
```

Display PDF information:

```bash
pdf-manipulator info document.pdf
```

### Python API

```python
from pdf_manipulator.core.document import PDFDocument
from pdf_manipulator.renderers.image_renderer import ImageRenderer

# Open a PDF document
with PDFDocument("document.pdf") as doc:
    # Get document info
    print(f"Pages: {doc.page_count}")
    print(f"Metadata: {doc.metadata}")
    
    # Create a renderer
    renderer = ImageRenderer(doc)
    
    # Render a specific page to PNG
    renderer.render_page_to_png(
        page_number=0,  # 0-based index
        output_path="page0.png",
        dpi=300,
        alpha=False,
    )
    
    # Render all pages
    renderer.render_document_to_pngs(
        output_dir="output_directory/",
        file_prefix="page_",
        dpi=300,
    )
```

## Project Structure

```
pdf_manipulator/
├── core/               # Core document handling
├── renderers/          # PDF to image rendering
├── extractors/         # Text/data extraction modules
├── utils/              # Utility functions
└── cli/                # Command line interface
```

## Dependencies

- PyMuPDF (fitz): Fast PDF rendering and manipulation
- Pillow: Image processing
- PyPDF: Pure Python PDF toolkit
- Click: Command line interface
- Pandas: Data manipulation (for future features)

## License

MIT