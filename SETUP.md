# Quick Setup Guide

## One-Line Setup

```bash
./scripts/mge-setup
```

This will:
1. ✅ Check Python version (requires >=3.8)
2. ✅ Create a virtual environment
3. ✅ Install all dependencies
4. ✅ Check for external tools (Tesseract, Ollama)
5. ✅ Create configuration file
6. ✅ Generate activation script

## Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

## After Setup

1. **Activate the environment:**
   ```bash
   source activate.sh
   ```

2. **Start extracting:**
   ```bash
   mge extract document.pdf output/ --memory
   ```

## Troubleshooting

### Python not found
- Install Python 3.8 or later from [python.org](https://python.org)

### Tesseract warnings
- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
- macOS: `brew install tesseract`
- Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Ollama not detected
- Install from [ollama.ai](https://ollama.ai)
- Start with: `ollama serve`
- Pull a model: `ollama pull llava:latest`

### Permission denied
```bash
chmod +x scripts/mge-setup
```

## Next Steps

- Read the [Quick Start Guide](docs/quickstart.md)
- Configure AI backends in `~/.config/pdf_manipulator/config.yaml`
- Explore memory graph features with `mge memory --help`