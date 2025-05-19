# Semantic Pipeline Quick Start Guide

Get up and running with semantic document extraction in minutes.

## Prerequisites

1. **Python 3.8+**
2. **PDF documents** to process
3. **LLM Backend** (optional):
   - Ollama with LLaVA model (local)
   - OpenAI API key (cloud)

## Installation

```bash
# Clone the repository
git clone https://github.com/aaronsb/memory-graph-extract.git
cd memory-graph-extract

# Install with semantic pipeline support
pip install -e .

# Optional: Install with llama.cpp support
pip install -e ".[llama]"
```

## Basic Usage

### 1. Simple Document Processing

Extract semantic knowledge from a PDF:

```bash
# Process with default settings (uses Ollama if available)
mge semantic process document.pdf output/

# Process without LLM (basic extraction only)
mge semantic process document.pdf output/ --no-llm
```

### 2. Configure LLM Backend

#### Using Ollama (Recommended for Local Processing)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the LLaVA model
ollama pull llava:latest

# Process with Ollama backend
mge semantic process document.pdf output/ --backend ollama
```

#### Using OpenAI

```bash
# Set your API key
export OPENAI_API_KEY="your-api-key"

# Process with OpenAI GPT-4V
mge semantic process document.pdf output/ --backend openai --model gpt-4-vision-preview
```

### 3. Check Results

The pipeline creates a knowledge graph in the output directory:

```bash
# View the generated files
ls output/document/

# Contents:
# - document_graph.json    # Semantic knowledge graph
# - markdown/             # Extracted content
# - metadata.json        # Processing metadata
```

## Configuration

### Quick Configuration

Create a simple config file (`my_config.yaml`):

```yaml
llm_backend:
  type: "ollama"
  backends:
    ollama:
      model: "llava:latest"
      base_url: "http://localhost:11434"

pipeline:
  enable_llm: true
  max_pages: 50
  parallel_pages: 4
  output_format: "json"
```

Use it:

```bash
mge semantic process document.pdf output/ --config my_config.yaml
```

### Environment Variables

Set commonly used values:

```bash
# OpenAI configuration
export OPENAI_API_KEY="your-key"

# Custom Ollama endpoint
export OLLAMA_HOST="http://your-server:11434"

# Output preferences
export MGE_OUTPUT_FORMAT="both"  # json and sqlite
```

## Common Use Cases

### 1. Process Multiple Documents

```bash
# Process a directory
for pdf in documents/*.pdf; do
    mge semantic process "$pdf" "output/$(basename "$pdf" .pdf)/"
done
```

### 2. Limited Processing (First N Pages)

```bash
# Process only first 10 pages
mge semantic process large_document.pdf output/ --max-pages 10
```

### 3. Parallel Processing

```bash
# Use 8 parallel workers for faster processing
mge semantic process document.pdf output/ --parallel 8
```

### 4. Save Intermediate Results

```bash
# Keep intermediate processing data for debugging
mge semantic process document.pdf output/ --save-intermediate
```

## Understanding the Output

### Graph Structure

The JSON output contains:

```json
{
  "nodes": {
    "node_id": {
      "type": "page|section|concept",
      "content": {
        "text": "Content text",
        "semantic_summary": "AI-generated understanding"
      },
      "ontology_tags": ["category1", "category2"],
      "confidence": 0.95
    }
  },
  "edges": {
    "edge_id": {
      "source_id": "node1",
      "target_id": "node2",
      "type": "contains|references|relates_to",
      "weight": 0.85
    }
  }
}
```

### Node Types
- **document**: Root document node
- **section**: Document sections from TOC
- **page**: Individual pages
- **concept**: Extracted concepts and entities

### Edge Types
- **contains**: Hierarchical containment
- **references**: Direct references
- **relates_to**: Semantic relationships
- **supports**: Supporting evidence
- **contradicts**: Conflicting information

## Viewing Results

### 1. Command Line

```bash
# Quick summary of the graph
mge memory info output/document/memory_graph.db

# Search the graph
mge memory search "machine learning" --database output/document/memory_graph.db
```

### 2. Python API

```python
import json

# Load the graph
with open('output/document/document_graph.json') as f:
    graph = json.load(f)

# Explore nodes
for node_id, node in graph['nodes'].items():
    if node['type'] == 'concept':
        print(f"Concept: {node['content']['text']}")
        print(f"Tags: {node['ontology_tags']}")
```

### 3. Web Interface

Use memory-graph-interface for visual exploration:

```bash
# Install the interface
npm install -g memory-graph-interface

# View your graph
memory-graph-interface --database output/document/memory_graph.db
```

## Troubleshooting

### LLM Backend Issues

```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# List available models
ollama list

# Test OpenAI key
mge semantic test --backend openai
```

### Memory Issues

For large documents:

```bash
# Limit processing scope
mge semantic process large.pdf output/ --max-pages 100

# Reduce parallel workers
mge semantic process large.pdf output/ --parallel 2
```

### Slow Processing

```bash
# Disable LLM for faster basic extraction
mge semantic process document.pdf output/ --no-llm

# Use config for performance tuning
# Adjust in config.yaml:
# parallel_pages: 8
# cache.enabled: true
```

## Next Steps

1. **Explore Advanced Configuration**: See `docs/configuration.md`
2. **Integrate with Memory Graph**: Connect to the ecosystem
3. **Build Custom Pipelines**: Extend components for your needs
4. **Contribute**: Submit issues and PRs on GitHub

## Getting Help

- **Documentation**: `/docs` directory
- **Examples**: `/examples` directory  
- **Issues**: https://github.com/aaronsb/memory-graph-extract/issues
- **Discussions**: GitHub Discussions