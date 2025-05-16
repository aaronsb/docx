# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Document AI Toolkit (docx) is a Python framework for intelligent PDF document processing. It transforms PDFs into structured content using rendering, OCR, and AI transcription. The system has a modular architecture with a pipeline-based approach.

## Commands and Tools

### Development Setup

```bash
# Install in development mode (standard)
pip install -e .

# Install with llama.cpp support (optional)
pip install -e '.[llama]'
```

### Running the CLI

The toolkit provides two equivalent command-line interfaces:

```bash
# Primary command
pdfx [command] [options]

# Alternative command (same functionality)
docaitool [command] [options]
```

### Core Commands

```bash
# Process a complete PDF document (full pipeline)
pdfx process document.pdf output/ --backend ollama --model llava:latest

# Render PDF pages to images
pdfx render document.pdf images/ --dpi 300

# Extract text from an image with OCR
pdfx ocr image.png --output text.txt

# Transcribe an image with AI
pdfx transcribe image.png --model llava:latest --output text.md

# Show PDF document information
pdfx info document.pdf

# Manage configuration
pdfx config --list
pdfx config --user --editor
pdfx config --project
```

## Architecture Overview

The project follows a layered architecture:

1. **Core Layer** - Basic document handling and pipeline orchestration
   - `PDFDocument`: PDF file operations
   - `DocumentProcessor`: High-level processing orchestration
   - `PerformanceTimer`: Processing metrics tracking

2. **Rendering Layer** - PDF to image conversion
   - `ImageRenderer`: Converts PDF pages to PNG images with configurable parameters

3. **Extraction Layer** - Text extraction from images
   - `OCRProcessor`: Tesseract OCR integration
   - `DocumentAnalyzer`: Basic document structure analysis

4. **Intelligence Layer** - AI-powered text extraction and processing
   - `IntelligenceBackend` (abstract base class)
   - Concrete implementations:
     - `OllamaBackend`: Integration with Ollama API
     - `LlamaCppBackend`: Direct llama.cpp integration
     - `LlamaCppHttpBackend`: HTTP client for llama.cpp server

5. **CLI Layer** - Command-line interface
   - Command structure following `verb input [output] [options]` pattern

## Processing Pipeline

The document processing pipeline follows this sequence:

1. PDF document → rendering → PNG images
2. Images → OCR/AI transcription → text
3. Text → structure extraction → structured content
4. (Optional) Advanced processing → semantic understanding

## Configuration System

The toolkit uses a hierarchical YAML-based configuration system:

1. Default built-in configuration
2. User configuration (~/.config/pdf_manipulator/config.yaml)
3. Project configuration (./.pdf_manipulator/config.yaml)
4. Command-line options (override all others)

Main configuration sections:
- `general`: Output directory and logging settings
- `rendering`: DPI, alpha channel, zoom settings
- `ocr`: Tesseract language and paths
- `intelligence`: AI backend configuration (ollama, llama_cpp, llama_cpp_http)
- `processing`: Default prompts and fallback settings

## Important Development Notes

1. When adding new features, maintain the modular architecture with clear separation of concerns

2. For implementing new intelligence backends:
   - Inherit from `IntelligenceBackend` in intelligence/base.py
   - Implement required methods (especially `transcribe_image`)
   - Add configuration handling in intelligence/processor.py

3. Error handling pattern:
   - Use specific exceptions from core/exceptions.py
   - Implement OCR fallback for AI transcription failures
   - Track and report performance metrics

4. Testing considerations:
   - Test each pipeline component individually
   - Test configuration loading with different hierarchies
   - Ensure graceful handling of missing dependencies (especially optional ones)

5. Performance optimization:
   - Use the PerformanceTimer to track processing time
   - Consider caching for repeated operations
   - Monitor memory usage when processing large documents