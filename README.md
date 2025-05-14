# Document AI Toolkit

A modular Python toolkit for document processing and analysis with AI capabilities including:

- Rendering PDF pages to PNG images
- OCR text extraction from document images
- AI-powered document transcription using local models (Ollama, llama.cpp)
- Table of contents generation with structured metadata
- Markdown conversion for easy content reuse

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/doc_ai_toolkit.git
cd doc_ai_toolkit

# Standard installation
pip install -e .

# If you want to use llama.cpp (optional)
pip install -e '.[llama]'
```

## Prerequisites

### Required

- Python 3.8+

### Optional but Recommended

#### Tesseract OCR

Required for OCR capabilities:

- **Arch Linux**: `sudo pacman -S tesseract tesseract-data-eng` (or other language packs)
- **Ubuntu/Debian**: `sudo apt-get install -y tesseract-ocr tesseract-ocr-eng`
- **macOS**: `brew install tesseract tesseract-lang`
- **Windows**: 
  1. Download installer from https://github.com/UB-Mannheim/tesseract/wiki
  2. Install and add to PATH
  3. Set TESSDATA_PREFIX environment variable to tessdata directory

#### Ollama

Required for AI transcription:

- Follow installation instructions at https://ollama.ai/
- Pull a multimodal model: `ollama pull llava:latest`

## Dependencies

The toolkit has several dependency options:

- **Core Dependencies**: Always installed (PyMuPDF, pytesseract, etc.)
- **Optional Dependencies**:
  - `llama-cpp-python`: For using llama.cpp models directly (install with `pip install -e '.[llama]'`)

If you encounter build errors with `llama-cpp-python`, you can still use the toolkit with Ollama without installing this dependency.

## Usage

### Command Line Interface

**Process a complete document:**

```bash
# Process a PDF with AI transcription (using Ollama)
docaitool process document.pdf output_directory/ --model llava:latest

# Process specific pages only
docaitool process document.pdf output_directory/ --pages 0,1,2

# Process with OCR only (no AI)
docaitool process document.pdf output_directory/ --no-ai

# Specify Tesseract data directory if needed
docaitool process document.pdf output_directory/ --tessdata-dir /usr/share/tessdata
```

**Render PDF pages to PNG images:**

```bash
# Render all pages of a PDF
docaitool render document.pdf output_directory/ --dpi 300

# Render a specific page (0-based index)
docaitool render document.pdf output_directory/ --page 0 --dpi 300
```

**OCR an image:**

```bash
# Extract text from an image using OCR
docaitool ocr image.png --output text.txt

# Specify Tesseract data directory if needed
docaitool ocr image.png --tessdata-dir /usr/share/tessdata
```

**Transcribe an image with AI:**

```bash
# Transcribe an image using Ollama
docaitool transcribe image.png --model llava:latest --output transcription.md
```

**Display PDF information:**

```bash
# Show PDF info including the table of contents
docaitool info document.pdf

# Show PDF info but hide the table of contents
docaitool info document.pdf --no-show-toc
```

### Python API

```python
from pdf_manipulator.core.document import PDFDocument
from pdf_manipulator.renderers.image_renderer import ImageRenderer
from pdf_manipulator.extractors.ocr import OCRProcessor
from pdf_manipulator.extractors.ai_transcription import OllamaTranscriber, DocumentTranscriber
from pdf_manipulator.core.pipeline import DocumentProcessor

# Basic PDF rendering
with PDFDocument("document.pdf") as doc:
    renderer = ImageRenderer(doc)
    renderer.render_page_to_png(
        page_number=0,
        output_path="page0.png",
        dpi=300,
    )

# OCR processing with custom Tesseract path
ocr = OCRProcessor(
    language="eng",
    tessdata_dir="/usr/share/tessdata",  # Specify if needed
    tesseract_cmd="/usr/bin/tesseract",  # Specify if needed
)
text = ocr.extract_text("page0.png")

# AI transcription with Ollama
transcriber = OllamaTranscriber(model_name="llava:latest")
text = transcriber.transcribe_image(
    "page0.png",
    prompt="Transcribe this document page to markdown format."
)

# Complete document processing pipeline
processor = DocumentProcessor(
    output_dir="output/",
    renderer_kwargs={"dpi": 300},
    ocr_processor=ocr,
    ai_transcriber=DocumentTranscriber(
        transcriber=transcriber,
        use_ocr_fallback=True,
        ocr_fallback=ocr.extract_text,
    ),
)

toc = processor.process_pdf("document.pdf", use_ai=True)
```

## Tesseract Configuration

If you encounter Tesseract errors, they may be due to:

1. **Missing language data** - Ensure the language pack (e.g., 'eng') is installed
2. **Incorrect Tesseract data path** - Set through one of these methods:
   - Use the `--tessdata-dir` CLI option
   - Set the `TESSDATA_PREFIX` environment variable: `export TESSDATA_PREFIX=/usr/share/tessdata`
   - In Python code: `OCRProcessor(tessdata_dir="/usr/share/tessdata")`

## Output Structure

When processing a document, the toolkit creates the following structure:

```
output_directory/
└── document_name/
    ├── images/               # Rendered page images
    │   ├── page_0000.png
    │   ├── page_0001.png
    │   └── ...
    ├── markdown/             # Transcribed content
    │   ├── page_0000.md
    │   ├── page_0001.md
    │   └── ...
    └── document_name_contents.json  # Table of contents metadata
```

The contents.json file follows this structure:

```json
{
  "document_name": "example",
  "total_pages": 3,
  "pages": [
    {
      "page_number": 1,
      "image_file": "page_0000.png",
      "markdown_file": "page_0000.md",
      "first_line": "Chapter 1: Introduction",
      "word_count": 245
    },
    ...
  ],
  "has_native_toc": true,
  "native_toc": [
    {
      "level": 1,
      "title": "Chapter 1: Introduction",
      "page": 1,
      "page_index": 0
    },
    {
      "level": 2,
      "title": "1.1 Background",
      "page": 2,
      "page_index": 1
    },
    ...
  ],
  "metadata": {
    "title": "Example Document",
    "author": "Document AI Toolkit",
    "subject": "PDF Processing",
    "creator": "PyMuPDF"
  }
}
```

## Project Structure

```
doc_ai_toolkit/
├── core/               # Core document handling
│   ├── document.py     # PDF document operations
│   ├── exceptions.py   # Error handling
│   └── pipeline.py     # Processing pipeline
├── renderers/          # PDF to image rendering
│   └── image_renderer.py
├── extractors/         # Text extraction modules
│   ├── ocr.py          # OCR functionality
│   └── ai_transcription.py # AI-based transcription
├── utils/              # Utility functions
└── cli/                # Command line interface
    └── commands.py     # CLI commands
```

## License

MIT