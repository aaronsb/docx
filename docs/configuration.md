# Configuration Guide

Memory Graph Extract uses a flexible configuration system based on YAML files. This guide explains how to configure the tool to suit your specific needs.

## Configuration Files

Memory Graph Extract searches for configuration files in the following order (highest priority first):

1. Custom path specified with `--config` option
2. Project-specific config: `./.mge/config.yaml`
3. User-specific config: `~/.config/mge/config.yaml`
4. System default config (built-in)

If no configuration file is found, a default one will be created in the user's config directory.

## Managing Configuration

You can manage configuration files using the `config` command:

```bash
# List available configuration files
mge config --list

# Create/update user configuration
mge config --user

# Create/update project-specific configuration
mge config --project

# Open configuration in default editor
mge config --editor
```

## Configuration Structure

The configuration file is organized into sections:

### General Settings

```yaml
general:
  # Default output directory for processed files
  output_dir: "output"
  
  # Logging configuration
  logging:
    # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    level: "INFO"
    # Log file path (set to null for console only)
    file: null
```

### Rendering Settings

```yaml
rendering:
  # Resolution in DPI (dots per inch)
  dpi: 300
  
  # Include alpha channel (transparency) in rendered images
  alpha: false
  
  # Additional zoom factor for rendering
  zoom: 1.0
```

### OCR Settings

```yaml
ocr:
  # OCR language(s) to use with Tesseract
  language: "eng"
  
  # Path to tessdata directory containing language data files
  tessdata_dir: null
  
  # Path to tesseract executable
  tesseract_cmd: null
```

### Intelligence Settings

```yaml
intelligence:
  # Default backend to use for AI processing
  default_backend: "ollama"
  
  # Configuration for different intelligence backends
  backends:
    # Ollama API backend
    ollama:
      model: "llava:latest"
      base_url: "http://localhost:11434"
      timeout: 120
    
    # Direct llama.cpp integration via Python bindings
    llama_cpp:
      model_path: null
      n_ctx: 2048
      n_gpu_layers: -1
    
    # llama.cpp HTTP server backend
    llama_cpp_http:
      base_url: "http://localhost:8080"
      model: null
      timeout: 120
      n_predict: 2048
      temperature: 0.1
```

### Processing Settings

```yaml
processing:
  # Default prompt for AI transcription of document images
  default_prompt: "Transcribe all text in this document image to markdown format. Preserve layout including tables, lists, headings, and paragraphs."
  
  # Whether to use OCR as fallback when AI transcription fails
  use_ocr_fallback: true
```

## Command-Line Overrides

Most configuration options can be overridden via command-line arguments. For example:

```bash
# Override output directory and AI backend
docaitool process document.pdf custom_output/ --backend llama_cpp_http
```

The precedence order is:
1. Command-line arguments
2. Project config
3. User config
4. System defaults

## Examples

### Configuring Ollama

```yaml
intelligence:
  default_backend: "ollama"
  backends:
    ollama:
      model: "llava:latest"
      base_url: "http://localhost:11434"
      timeout: 120
```

### Configuring llama.cpp Direct Integration

```yaml
intelligence:
  default_backend: "llama_cpp"
  backends:
    llama_cpp:
      model_path: "/path/to/model.gguf"
      n_ctx: 4096
      n_gpu_layers: 32
```

### Configuring llama.cpp HTTP Server

```yaml
intelligence:
  default_backend: "llama_cpp_http"
  backends:
    llama_cpp_http:
      base_url: "http://localhost:8080"
      model: "llava:13b"
      timeout: 180
      n_predict: 4096
      temperature: 0.2
```

## Managing Multiple Backends

You can configure multiple intelligence backends in your configuration file and switch between them using the `--backend` option:

```bash
# Use Ollama backend
docaitool process document.pdf output/ --backend ollama

# Use llama.cpp HTTP backend
docaitool process document.pdf output/ --backend llama_cpp_http
```

## Viewing Intelligence Backend Information

You can view information about configured intelligence backends using the `intelligence` command:

```bash
# List available intelligence backends
docaitool intelligence --list
```