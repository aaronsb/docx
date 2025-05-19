# PDFX - PDF Extractor

A modular Python toolkit for PDF document processing and analysis with AI capabilities.

## Summary

PDFX transforms PDF documents into structured, searchable content using direct document conversion or a combination of rendering, OCR, and AI-powered transcription. Key features include:

- **Direct document conversion** with markitdown (default) - no rendering required
- Multiple document format support (PDF, Word, PowerPoint, Excel, and more)
- Rendering PDF pages to PNG images (when needed)
- OCR text extraction from document images
- AI-powered document transcription using local models with multiple backends
- Table of contents generation with structured metadata
- Markdown conversion for easy content reuse
- Progress tracking with visual status updates
- Flexible configuration system with YAML format
- Command-line interface with configuration management
- **Memory graph storage**: Store extracted content in SQLite database directly compatible with [memory-graph-mcp](https://github.com/aaronsb/memory-graph)
- **Context-aware processing**: Use existing memories to enhance new document processing

## Use Cases

### Document Processing
- **Direct document conversion**: Fast conversion without rendering using markitdown (default)
- **Batch PDF to Markdown conversion**: Convert entire PDF documents or directories into markdown files
- **Intelligent content extraction**: Use AI to understand complex layouts, tables, and figures
- **OCR fallback**: Automatically fall back to OCR when AI transcription fails

### Knowledge Management
- **Document memory storage**: Build a searchable knowledge base from processed documents
- **MCP-compatible memory graph**: Generated databases work directly with [memory-graph-mcp](https://github.com/aaronsb/memory-graph) for Claude Desktop
- **Cross-document relationships**: Create connections between related content across multiple PDFs
- **Context-aware processing**: Use previously extracted knowledge to improve future processing

### Examples

```bash
# Direct conversion with markitdown (default, fastest)
pdfx process document.pdf output/

# Traditional rendering pipeline with AI
pdfx process document.pdf output/ --backend ollama --render

# Process with memory storage to build knowledge base
pdfx process document.pdf output/ --memory

# Render specific pages as images
pdfx render document.pdf images/ --pages 0,1,2 --dpi 300

# Extract text from scanned images
pdfx ocr scan.png --output text.txt

# Process with custom backend
pdfx process document.pdf output/ --backend llama_cpp --model llama-7b.gguf
```

## Usage

### Command Line Interface

The CLI provides several commands for different operations:

**Process a complete document:**

```bash
# Process with default markitdown backend (fastest, no rendering)
pdfx process document.pdf output_directory/

# Process with direct conversion explicitly
pdfx process document.pdf output_directory/ --backend markitdown --direct

# Process with AI backend (renders pages first)
pdfx process document.pdf output_directory/ --backend ollama --model llava:latest

# Process with OCR only (no AI)
pdfx process document.pdf output_directory/ --no-ai

# Process specific pages
pdfx process document.pdf output_directory/ --pages 0,5,10

# Process with memory storage enabled
pdfx process document.pdf output_directory/ --memory

# Process without progress display
pdfx process document.pdf output_directory/ --no-progress
```

**Render PDF pages:**

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
# Transcribe with markitdown (default)
pdfx transcribe image.png --output transcription.md

# Transcribe with Ollama
pdfx transcribe image.png --backend ollama --model llava:latest --output transcription.md

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

# Direct document conversion with markitdown
from pdf_manipulator.intelligence.markitdown import MarkitdownBackend
markitdown = MarkitdownBackend()
toc = markitdown.process_direct_document(
    document_path="document.pdf",
    output_dir="output/",
    base_filename="document"
)

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

# AI transcription
processor = create_processor(
    config=config,
    ocr_processor=ocr,
    backend_name="markitdown",  # or "ollama", "llama_cpp", etc.
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
toc = document_processor.process_pdf(
    "document.pdf", 
    use_ai=True,
    show_progress=True  # Show progress status updates
)
```

### Output Structure

When processing a document, the toolkit creates the following structure:

```
output_directory/
└── document_name/
    ├── images/               # Rendered page images (if rendering used)
    │   ├── page_0000.png
    │   ├── page_0001.png
    │   └── ...
    ├── markdown/             # Transcribed content
    │   ├── document_name.md  # Single file for direct conversion
    │   ├── page_0000.md      # Individual pages for rendered pipeline
    │   ├── page_0001.md
    │   └── ...
    ├── memory_graph.db       # Memory storage database (if enabled)
    └── document_name_contents.json  # Table of contents metadata
```

The contents.json file includes document structure, TOC, and metadata.

### Memory Graph Usage

When memory storage is enabled (`--memory` flag or configured in settings), the toolkit creates a SQLite database that is directly compatible with the [memory-graph-mcp server](https://github.com/aaronsb/memory-graph). These database files can be used with Claude Desktop and other AI tools:

```python
from pdf_manipulator.memory.memory_adapter import MemoryConfig
from pdf_manipulator.memory.memory_processor import MemoryProcessor

# Configure memory storage
memory_config = MemoryConfig(
    database_path="output/memory_graph.db",
    domain_name="pdf_processing",
    domain_description="PDF document processing knowledge base",
    enable_relationships=True,
    enable_summaries=True,
)

# Initialize memory processor with AI support
with MemoryProcessor(memory_config, intelligence_processor) as mem_processor:
    # Process document with memory storage
    results = mem_processor.process_document(
        pdf_document=doc,
        page_content=page_content_dict,
        document_metadata={
            'filename': 'document.pdf',
            'transcription_method': 'ai',
        }
    )
```

## Architecture

The document processing pipeline follows this sequence:

### Direct Conversion (markitdown - default)
1. Document → markitdown → Markdown
2. Markdown → structure extraction → structured content
3. (Optional) Memory storage → knowledge graph

### Traditional Pipeline (AI/OCR backends)
1. PDF document → rendering → PNG images
2. Images → OCR/AI transcription → text 
3. Text → structure extraction → structured content
4. (Optional) Advanced processing → semantic understanding
5. (Optional) Memory storage → knowledge graph

### AI Intelligence Backends

Multiple backend options provide flexibility:

- **markitdown** (default) - Direct document conversion, no GPU required
- **Ollama API** - Easy to use with local models
- **llama.cpp** - Direct integration via Python bindings
- **llama.cpp HTTP** - Server for custom optimized builds

### Memory Graph Integration

The toolkit generates SQLite databases that are directly compatible with the [memory-graph-mcp server](https://github.com/aaronsb/memory-graph), enabling seamless integration with other AI tools and Claude Desktop:

- Store document pages, sections, and metadata as interconnected memory nodes
- Create relationships between related content (pages, sections, documents)
- Query previous memories to enhance future document processing
- Generate AI summaries for better searchability
- Database files can be opened directly by memory-graph-mcp for use with Claude Desktop and other AI applications
- Compatible with the entire memory-graph ecosystem for knowledge management

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
- **Core Dependencies**: PyMuPDF, pytesseract, markitdown, etc. (installed automatically)
- **Optional**: `llama-cpp-python` (for direct llama.cpp integration)

If you encounter build errors with `llama-cpp-python`, you can still use the toolkit with markitdown or Ollama.

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

### markitdown Setup (Default Backend)

markitdown is installed automatically and requires no additional setup. It handles:
- PDF files
- Microsoft Office documents (Word, PowerPoint, Excel)
- Images with text
- HTML and text files
- Many other formats

### Tesseract OCR Setup

Required for OCR capabilities and fallback:

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

#### Ollama Setup (Recommended for AI Processing)

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

### Advanced Configuration

For fine-tuning performance and behavior, modify your `config.yaml`:

```yaml
intelligence:
  default_backend: "markitdown"  # Default backend
  backends:
    markitdown:
      # No configuration needed - works out of the box
    ollama:
      model: "llava:latest"
      base_url: "http://localhost:11434"
      timeout: 120

rendering:
  dpi: 300  # Higher for better quality
  alpha: false  # Include transparency
  zoom: 1.0  # Scaling factor

processing:
  use_ocr_fallback: true  # Fallback to OCR if AI fails
  default_prompt: "Transcribe all text in this document image to markdown format."

memory:
  enabled: false  # Enable memory storage by default
  database_name: "memory_graph.db"
  domain:
    name: "pdf_processing"
    description: "PDF document processing knowledge base"
  creation:
    enable_relationships: true
    enable_summaries: true
    tags_prefix: "pdf:"
    min_content_length: 50
```

## Troubleshooting

### markitdown Issues

- If document conversion fails, check the file format is supported
- For PDF-specific features, may need to install additional dependencies: `pip install "markitdown[pdf]"`

### Tesseract Issues

- Verify installation: `tesseract --version`
- Check language data: `tesseract --list-langs`
- Ensure TESSDATA_PREFIX is set correctly

### AI Backend Issues

- For Ollama: Check server is running: `curl http://localhost:11434/api/tags`
- Verify model is downloaded: `ollama list`
- For llama.cpp: Check model file path and format

### Memory Issues

- For large documents, consider processing in chunks with `--pages`
- Adjust rendering DPI if running out of memory
- Use markitdown for direct conversion without rendering

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests if available
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PyMuPDF for PDF rendering
- Tesseract for OCR capabilities
- Ollama for easy AI model deployment
- llama.cpp for efficient model inference
- markitdown for direct document conversion
- memory-graph project for knowledge management inspiration