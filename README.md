# PDFX - PDF Extractor

A modular Python toolkit for PDF document processing and analysis with AI capabilities.

## Summary

PDFX transforms PDF documents into structured, searchable content using a combination of rendering, OCR, and AI-powered transcription. Key features include:

- Rendering PDF pages to PNG images
- OCR text extraction from document images
- AI-powered document transcription using local models with multiple backends
- Table of contents generation with structured metadata
- Markdown conversion for easy content reuse
- Flexible configuration system with YAML format
- Command-line interface with configuration management
- **Memory graph storage**: Store extracted content in SQLite database following memory-graph schema
- **Context-aware processing**: Use existing memories to enhance new document processing

## Use Cases

### Document Processing
- **Batch PDF to Markdown conversion**: Convert entire PDF documents or directories into markdown files
- **Intelligent content extraction**: Use AI to understand complex layouts, tables, and figures
- **OCR fallback**: Automatically fall back to OCR when AI transcription fails

### Knowledge Management
- **Document memory storage**: Build a searchable knowledge base from processed documents
- **Cross-document relationships**: Create connections between related content across multiple PDFs
- **Context-aware processing**: Use previously extracted knowledge to improve future processing

### Examples

```bash
# Convert a PDF to searchable markdown with AI
pdfx process document.pdf output/ --model llava:latest

# Process with memory storage to build knowledge base
pdfx process document.pdf output/ --memory

# Render specific pages as images
pdfx render document.pdf images/ --pages 0,1,2 --dpi 300

# Extract text from scanned images
pdfx ocr scan.png --output text.txt
```

## Usage

### Command Line Interface

The tool uses a simple, intuitive command structure:

```bash
# Simple command format: verb input [output] [options]
pdfx render document.pdf images/        # Convert PDF to images
pdfx ocr image.png                      # Extract text with OCR
pdfx transcribe image.png               # Transcribe image with AI
pdfx process document.pdf output/       # Full intelligent processing
pdfx info document.pdf                  # Show document information
```

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

# Process with memory storage enabled
pdfx process document.pdf output_directory/ --memory

# Process with memory and specific AI backend
pdfx process document.pdf output_directory/ --memory --backend ollama --model llava:latest
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
```

**Transcribe an image with AI:**

```bash
# Transcribe an image using Ollama (default)
pdfx transcribe image.png --model llava:latest --output transcription.md

# Transcribe with custom prompt
pdfx transcribe image.png --prompt "Extract tables from this image as markdown"
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
config = load_config()

# Basic PDF rendering
with PDFDocument("document.pdf") as doc:
    renderer = ImageRenderer(doc)
    renderer.render_page_to_png(
        page_number=0,
        output_path="page0.png",
        dpi=config.get('rendering', {}).get('dpi', 300),
    )

# OCR processing
ocr = OCRProcessor(
    language=config.get('ocr', {}).get('language', 'eng'),
    tessdata_dir=config.get('ocr', {}).get('tessdata_dir'),
)
text = ocr.extract_text("page0.png")

# AI transcription with Ollama
processor = create_processor(
    config=config,
    ocr_processor=ocr,
    backend_name="ollama",
)
text = processor.process_image(
    "page0.png",
    custom_prompt="Transcribe this document page to markdown format."
)

# Complete document processing pipeline
document_processor = DocumentProcessor(
    output_dir=config.get('general', {}).get('output_dir', 'output'),
    renderer_kwargs={"dpi": 300, "alpha": False, "zoom": 1.0},
    ocr_processor=ocr,
    ai_transcriber=processor,
)
toc = document_processor.process_pdf("document.pdf", use_ai=True)
```

### Output Structure

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
    ├── memory_graph.db       # Memory storage database (if enabled)
    └── document_name_contents.json  # Table of contents metadata
```

The contents.json file includes document structure, TOC, and metadata.

### Memory Graph Usage

When memory storage is enabled (`--memory` flag or configured in settings), the toolkit creates a SQLite database following the memory-graph schema:

```python
# Using memory storage in Python
from pdf_manipulator.memory.memory_adapter import MemoryConfig
from pdf_manipulator.memory.memory_processor import MemoryProcessor

# Configure memory storage
memory_config = MemoryConfig(
    database_path="output/memory_graph.db",
    domain_name="pdf_documents",
    enable_relationships=True,
    enable_summaries=True,
)

# Process document with memory storage
document_processor = DocumentProcessor(
    output_dir="output/",
    memory_config=memory_config,
    # ... other options
)

result = document_processor.process_pdf(
    "document.pdf",
    store_in_memory=True,
)

# Query stored memories
with MemoryProcessor(memory_config) as processor:
    # Find related documents
    similar_docs = processor.find_similar_documents("search query")
    
    # Get document knowledge graph
    graph = processor.get_document_graph(document_id, max_depth=2)
```

Example memory configuration in config.yaml:

```yaml
memory:
  enabled: true
  database_name: "memory_graph.db"
  domain:
    name: "pdf_processing"
    description: "PDF document knowledge base"
  creation:
    enable_relationships: true
    enable_summaries: true
    tags_prefix: "pdf:"
    min_content_length: 50
```

## Architecture Overview

PDFX follows a layered architecture with modular components:

### Processing Pipeline

The document processing pipeline follows this sequence:

1. PDF document → rendering → PNG images
2. Images → OCR/AI transcription → text 
3. Text → structure extraction → structured content
4. (Optional) Advanced processing → semantic understanding

### AI Intelligence Backends

Multiple backend options provide flexibility:

- **Ollama API** (easiest to use)
- **llama.cpp** direct integration (via Python bindings)
- **llama.cpp HTTP** server (for custom optimized builds)

### Memory Graph Integration

The toolkit supports storing extracted content in a memory-graph compatible SQLite database:

- Store document pages, sections, and metadata as interconnected memory nodes
- Create relationships between related content (pages, sections, documents)
- Query previous memories to enhance future document processing
- Generate AI summaries for better searchability
- Compatible with memory-graph ecosystem for knowledge management

### Configuration System

The toolkit uses a hierarchical YAML-based configuration:

1. Default built-in configuration
2. User configuration (~/.config/pdf_manipulator/config.yaml)
3. Project configuration (./.pdf_manipulator/config.yaml) 
4. Command-line options (override all others)

## Installation and Setup

### Installation

```bash
# Clone the repository
git clone https://github.com/aaronsb/docx.git
cd docx

# Standard installation
pip install -e .

# If you want to use llama.cpp (optional)
pip install -e '.[llama]'
```

### Dependencies

- **Required**: Python 3.8+
- **Core Dependencies**: PyMuPDF, pytesseract, etc. (installed automatically)
- **Optional**: `llama-cpp-python` (for direct llama.cpp integration)

If you encounter build errors with `llama-cpp-python`, you can still use the toolkit with Ollama.

### Configuration Management

```bash
# Run first-time setup (optional - runs automatically if needed)
pdfx-setup

# List available configuration files
pdfx config --list

# Create/update user configuration
pdfx config --user

# Create/update project-specific configuration
pdfx config --project

# Open configuration in default editor
pdfx config --editor
```

## Component Setup

### Tesseract OCR Setup

Required for OCR capabilities:

- **Arch Linux**: `sudo pacman -S tesseract tesseract-data-eng` (or other language packs)
- **Ubuntu/Debian**: `sudo apt-get install -y tesseract-ocr tesseract-ocr-eng`
- **macOS**: `brew install tesseract tesseract-lang`
- **Windows**: 
  1. Download installer from https://github.com/UB-Mannheim/tesseract/wiki
  2. Install and add to PATH
  3. Set TESSDATA_PREFIX environment variable to tessdata directory

If you encounter Tesseract errors, they may be due to:

1. **Missing language data** - Ensure the language pack (e.g., 'eng') is installed
2. **Incorrect Tesseract data path** - Set through one of these methods:
   - Use the `--tessdata-dir` CLI option
   - Set the `TESSDATA_PREFIX` environment variable: `export TESSDATA_PREFIX=/usr/share/tessdata`
   - In Python code: `OCRProcessor(tessdata_dir="/usr/share/tessdata")`

### AI Backend Setup

#### Ollama Setup (Recommended)

For native installation:
- Follow installation instructions at https://ollama.ai/
- Pull a multimodal model: `ollama pull llava:latest`
- Server runs on http://localhost:11434 by default

#### Docker Setup for Ollama

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

#### llama.cpp Direct Integration

- Requires the llama-cpp-python package: `pip install -e '.[llama]'`
- Requires downloading model files manually
- More configuration options, but can have build issues on some platforms

#### llama.cpp HTTP Server (for custom optimized builds)

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
│   ├── llama_cpp_http.py # HTTP client for llama.cpp
│   └── memory_enhanced.py # Memory-enhanced backend
├── memory/             # Memory graph integration
│   ├── memory_adapter.py  # SQLite database adapter
│   └── memory_processor.py # Document memory processing
├── utils/              # Utility functions
├── cli/                # Command line interface
│   └── commands.py     # CLI commands
└── examples/           # Example scripts
    ├── memory_processing_example.py      # Basic memory storage example
    ├── memory_enhanced_processing.py     # Advanced memory-enhanced processing
    └── cli_memory_example.sh            # CLI usage examples
```

## License

MIT