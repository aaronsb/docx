#!/bin/bash
# Example: Using memory integration with the CLI

# Process a PDF with memory storage enabled
echo "=== Processing PDF with Memory Storage ==="
pdfx process document.pdf output/ --memory --backend ollama --model llava:latest

# The above command will:
# 1. Render PDF pages to images
# 2. Transcribe using AI (Ollama with llava model)
# 3. Store content in a memory graph SQLite database
# 4. Create relationships between pages and sections

# You can also enable memory in your configuration file:
echo "
# Enable memory storage by default
memory:
  enabled: true
  database_name: 'memory_graph.db'
  domain:
    name: 'my_documents'
    description: 'My document knowledge base'
" >> ~/.config/pdf_manipulator/config.yaml

# Process multiple PDFs into the same memory domain
echo "=== Building Document Knowledge Base ==="
for pdf in *.pdf; do
    echo "Processing: $pdf"
    pdfx process "$pdf" output/ --memory
done

# The memory database will be created at:
# output/<document_name>/memory_graph.db

# You can then query these databases using the Python API
# or integrate them with other memory-graph compatible tools

echo "=== Memory Storage Complete ==="
echo "Memory databases created in output directory"
echo "Use the Python examples to query and visualize the stored memories"