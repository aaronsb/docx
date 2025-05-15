# PDFX - PDF Extractor

A modular Python toolkit for PDF document processing and analysis with AI capabilities including:

- Rendering PDF pages to PNG images
- OCR text extraction from document images
- AI-powered document transcription using local models with multiple backends:
  - Ollama API (easy to use)
  - llama.cpp direct integration (via Python bindings)
  - llama.cpp HTTP server (custom builds/optimizations)
- Table of contents generation with structured metadata
- Markdown conversion for easy content reuse
- Flexible configuration system with YAML format
- Command-line interface with configuration management

## Installation

```bash
# Clone the repository
git clone https://github.com/aaronsb/docx.git
cd docx

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

#### AI Backends

For AI transcription, you can use one of the following backends:

##### Ollama (Recommended for ease of use)

- Follow installation instructions at https://ollama.ai/
- Pull a multimodal model: `ollama pull llava:latest`
- Server runs on http://localhost:11434 by default

###### Docker Setup for Ollama

For a containerized Ollama setup with GPU acceleration:

1. Create a `docker-compose.yml` file:

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    environment:
      - OLLAMA_ORIGINS=chrome-extension://*
      - OLLAMA_HOST=0.0.0.0
      - OLLAMA_KEEP_ALIVE=1h
    ports:
      - "11434:11434"
    volumes:
      - ./ollama_data:/root/.ollama
      - /dev/shm:/dev/shm
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

2. Start the Ollama container:

```bash
docker compose up -d
```

3. Pull and run models:

```bash
# Pull a multimodal model
docker exec -it ollama ollama pull llava:latest

# List available models
docker exec -it ollama ollama list

# Test a model
docker exec -it ollama ollama run llava:latest
```

4. For Intel GPU acceleration, add the following to your `docker-compose.yml`:

```yaml
    environment:
      # Add these lines for Intel GPU acceleration
      - OLLAMA_USE_OPENVINO=1
      - OLLAMA_CPU_THREADS=16  # Adjust based on your CPU cores
    volumes:
      # Add these lines for GPU access
      - /dev/dri:/dev/dri
    devices:
      # Expose Intel GPU devices
      - /dev/dri/renderD128:/dev/dri/renderD128
      - /dev/dri/card0:/dev/dri/card0
    group_add:
      - video
```

You may need to install Intel drivers first:

```bash
sudo apt-get install -y intel-opencl-icd intel-level-zero-gpu level-zero intel-media-va-driver-non-free
sudo usermod -a -G video $USER  # Log out and back in after this
```

For more details on the Docker setup for Ollama, see: [ollama-docker](https://github.com/aaronsb/ollama-docker)

##### llama.cpp Direct Integration

- Requires the llama-cpp-python package: `pip install -e '.[llama]'`
- Requires downloading model files manually
- More configuration options, but can have build issues on some platforms

##### llama.cpp HTTP Server (for custom optimized builds)

- Build and run your own optimized llama.cpp server:
  ```bash
  git clone https://github.com/ggerganov/llama.cpp.git
  cd llama.cpp
  # Build with your custom optimization flags
  make LLAMA_CUBLAS=1  # For NVIDIA GPU support
  # or
  make LLAMA_METAL=1  # For Apple Silicon
  # Run the server with multimodal support
  ./server -m path/to/model.gguf --multimodal-path /path/to/clip/model
  ```
- Server typically runs on http://localhost:8080
- No need to install llama-cpp-python

## Dependencies

The toolkit has several dependency options:

- **Core Dependencies**: Always installed (PyMuPDF, pytesseract, etc.)
- **Optional Dependencies**:
  - `llama-cpp-python`: For using llama.cpp models directly (install with `pip install -e '.[llama]'`)

If you encounter build errors with `llama-cpp-python`, you can still use the toolkit with Ollama without installing this dependency.

## Configuration

The toolkit uses a flexible configuration system with YAML files. Configuration files can be created at:
- Project-specific: `./.pdf_manipulator/config.yaml`
- User-specific: `~/.config/pdf_manipulator/config.yaml`

You can manage configuration files using:

```bash
# List available configuration files
pdfx config --list

# Create/update user configuration
pdfx config --user

# Create/update project-specific configuration
pdfx config --project

# Open configuration in default editor
pdfx config --editor
```

For detailed configuration documentation, see [Configuration Guide](docs/configuration.md).

## Usage

### Quick Start

The tool uses a simple, intuitive command structure:

```bash
# Run first-time setup (optional - runs automatically if needed)
pdfx-setup

# Simple command format: verb input [output] [options]
pdfx render document.pdf images/        # Convert PDF to images
pdfx ocr image.png                      # Extract text with OCR
pdfx transcribe image.png               # Transcribe image with AI
pdfx extract document.pdf output/       # Extract structured content
pdfx process document.pdf output/       # Full intelligent processing
pdfx info document.pdf                  # Show document information
```

### Command Line Interface

**Process a complete document:**

```bash
# Process a PDF with Ollama (default)
pdfx process document.pdf output_directory/ --model llava:latest

# Process with llama.cpp HTTP server backend
pdfx process document.pdf output_directory/ \
  --backend llama_cpp_http \
  --model llava

# Process with direct llama.cpp integration
pdfx process document.pdf output_directory/ \
  --backend llama_cpp \
  --model-path /path/to/model.gguf

# Process specific pages only
pdfx process document.pdf output_directory/ --pages 0,1,2

# Process with OCR only (no AI)
pdfx process document.pdf output_directory/ --no-ai

# Specify Tesseract data directory if needed
pdfx process document.pdf output_directory/ --tessdata-dir /usr/share/tessdata
```

**Render PDF pages to PNG images:**

```bash
# Render all pages of a PDF
pdfx render document.pdf output_directory/ --dpi 300

# Render a specific page (0-based index)
pdfx render document.pdf output_directory/ --page 0 --dpi 300
```

**OCR an image:**

```bash
# Extract text from an image using OCR
pdfx ocr image.png --output text.txt

# Specify Tesseract data directory if needed
pdfx ocr image.png --tessdata-dir /usr/share/tessdata
```

**Transcribe an image with AI:**

```bash
# Transcribe an image using Ollama (default)
pdfx transcribe image.png --model llava:latest --output transcription.md

# Transcribe using llama.cpp HTTP server
pdfx transcribe image.png \
  --backend llama_cpp_http \
  --output transcription.md

# Transcribe with custom prompt
pdfx transcribe image.png --prompt "Extract tables from this image as markdown"
```

**Display PDF information:**

```bash
# Show PDF info including the table of contents
pdfx info document.pdf

# Show PDF info but hide the table of contents
pdfx info document.pdf --no-show-toc
```

**List AI intelligence backends:**

```bash
# List available and configured intelligence backends
pdfx intelligence --list
```

### Python API

```python
from pdf_manipulator.core.document import PDFDocument
from pdf_manipulator.renderers.image_renderer import ImageRenderer
from pdf_manipulator.extractors.ocr import OCRProcessor
from pdf_manipulator.utils.config import load_config
from pdf_manipulator.intelligence.processor import create_processor
from pdf_manipulator.core.pipeline import DocumentProcessor

# Load configuration
config = load_config()  # Loads from default locations

# Basic PDF rendering
with PDFDocument("document.pdf") as doc:
    renderer = ImageRenderer(doc)
    renderer.render_page_to_png(
        page_number=0,
        output_path="page0.png",
        dpi=config.get('rendering', {}).get('dpi', 300),
    )

# OCR processing with configuration
ocr = OCRProcessor(
    language=config.get('ocr', {}).get('language', 'eng'),
    tessdata_dir=config.get('ocr', {}).get('tessdata_dir'),
    tesseract_cmd=config.get('ocr', {}).get('tesseract_cmd'),
)
text = ocr.extract_text("page0.png")

# AI transcription using intelligence backends
# Create a processor with the configured backend (or specific backend)
processor = create_processor(
    config=config,
    ocr_processor=ocr,
    backend_name="ollama",  # Optional - uses default from config if not specified
)

# Process an image with AI
text = processor.process_image(
    "page0.png",
    custom_prompt="Transcribe this document page to markdown format."
)

# Process text with AI
cleaned_text = processor.process_text(
    ocr_text,
    custom_prompt_template="Clean this OCR text: {text}"
)

# Alternative: Access direct backend API for more control
# You can still use the direct API if needed
from pdf_manipulator.intelligence.ollama import OllamaBackend
from pdf_manipulator.intelligence.llama_cpp import LlamaCppBackend
from pdf_manipulator.intelligence.llama_cpp_http import LlamaCppHttpBackend

# Create backend from config section
ollama_config = config.get('intelligence', {}).get('backends', {}).get('ollama', {})
ollama = OllamaBackend(ollama_config)
text = ollama.transcribe_image("page0.png")

# Complete document processing pipeline
document_processor = DocumentProcessor(
    output_dir=config.get('general', {}).get('output_dir', 'output'),
    renderer_kwargs={
        "dpi": config.get('rendering', {}).get('dpi', 300),
        "alpha": config.get('rendering', {}).get('alpha', False),
        "zoom": config.get('rendering', {}).get('zoom', 1.0),
    },
    ocr_processor=ocr,
    ai_transcriber=processor,
)

toc = document_processor.process_pdf("document.pdf", use_ai=True)
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
    "author": "PDFX",
    "subject": "PDF Processing",
    "creator": "PyMuPDF"
  }
}
```

## Project Structure

```
pdf_manipulator/
├── core/               # Core document handling
│   ├── document.py     # PDF document operations
│   ├── exceptions.py   # Error handling
│   └── pipeline.py     # Processing pipeline
├── renderers/          # PDF to image rendering
│   └── image_renderer.py
├── extractors/         # Text extraction modules
│   ├── ocr.py          # OCR functionality
│   └── ai_transcription.py # AI-based transcription
├── intelligence/       # AI backends
│   ├── base.py         # Base class for backends
│   ├── ollama.py       # Ollama API integration
│   ├── llama_cpp.py    # Direct llama.cpp integration
│   └── llama_cpp_http.py # HTTP client for llama.cpp
├── utils/              # Utility functions
└── cli/                # Command line interface
    └── commands.py     # CLI commands
```

## License

MIT