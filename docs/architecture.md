# PDF Extractor Architecture

This document outlines the architectural vision for the PDF Extractor tool (pdfx), with a focus on the hierarchical processing workflow and the integration of multiple AI backends.

## Command Structure

The tool follows a consistent and intuitive command pattern:

```
pdfx [verb] [input] [output] [options]
```

Where each verb represents a specific processing chain, building on simpler operations to create more complex workflows.

## Processing Hierarchy

The processing verbs form a natural hierarchy, with each level building on the previous:

```
PDF → render → images → OCR/AI → text → structure → sections → insights
```

### Core Verbs and Processing Chains

1. **`render`** - Convert PDF pages to images
   - **Input**: PDF document
   - **Output**: PNG images
   - **Components**: PDFDocument, ImageRenderer
   - **Example**: `pdfx render document.pdf images/`

2. **`ocr`** - Extract text from images using OCR
   - **Input**: Image
   - **Output**: Raw text
   - **Components**: OCRProcessor
   - **Example**: `pdfx ocr image.png text.txt`
   - **Chain**: Operates directly on an image

3. **`transcribe`** - Use AI to extract text from images
   - **Input**: Image
   - **Output**: Enhanced text (formatted markdown)
   - **Components**: IntelligenceBackend (Ollama, LlamaCpp, LlamaCppHttp)
   - **Example**: `pdfx transcribe image.png markdown.md`
   - **Chain**: Operates directly on an image

4. **`extract`** - Extract structured content from a PDF
   - **Input**: PDF document
   - **Output**: Structured content (TOC, text, metadata)
   - **Components**: PDFDocument, ImageRenderer, OCRProcessor/IntelligenceBackend, DocumentAnalyzer
   - **Example**: `pdfx extract document.pdf output/`
   - **Chain**: render → ocr/transcribe → basic structure extraction

5. **`process`** - Complete document processing with advanced AI
   - **Input**: PDF document
   - **Output**: Comprehensive markdown conversion with intelligent structure
   - **Components**: DocumentProcessor + Advanced AI (Claude/OpenAI)
   - **Example**: `pdfx process document.pdf output/`
   - **Chain**: render → ocr/transcribe → extract → section identification → advanced AI transformation

## Intelligence Backend Architecture

The system uses a flexible intelligence backend architecture that supports multiple AI models:

1. **Local Processing**
   - Ollama API (easy setup, multimodal)
   - LlamaCpp direct integration (via Python bindings)
   - LlamaCpp HTTP server (custom optimized builds)

2. **Advanced API Processing** (future)
   - Claude API (for sophisticated document understanding)
   - OpenAI API (for multimodal GPT-4 processing)

Each backend implements a common interface (BaseTranscriber) ensuring consistency across the system.

## Process Verb Vision

The `process` verb represents the most sophisticated operation, designed to:

1. Render the PDF to high-quality images
2. Extract text using the best available method (OCR or AI transcription)
3. Identify logical document sections and structure
4. Pass these sections to a sophisticated AI model (Claude/GPT-4)
5. Use specially crafted prompts to transform each section into well-structured markdown
6. Maintain the document's logical flow and relationships
7. Preserve tables, lists, and other complex elements
8. Combine the processed sections into a cohesive markdown document

This approach leverages both the strengths of specialized document processing tools and the natural language understanding capabilities of large language models.

## Configuration System

The system uses a flexible YAML-based configuration that allows users to:

1. Configure rendering parameters (DPI, zoom, etc.)
2. Set up OCR preferences (language, Tesseract path)
3. Choose and configure AI backends
4. Define processing parameters and prompts

The configuration can be managed through:
- Manual editing of YAML files
- Interactive setup script (`pdfx-setup`)
- Command-line options that override config settings

## Future Directions

1. **Section Intelligence**: Enhanced ability to identify logical document sections
2. **Custom Backends**: Support for user-defined AI backends
3. **Specialized Prompts**: Domain-specific prompts for different document types
4. **Pipeline Extensions**: Allow users to add custom processing steps
5. **Document Understanding**: Deep semantic understanding of document content
6. **Incremental Processing**: Process documents in chunks to handle very large documents