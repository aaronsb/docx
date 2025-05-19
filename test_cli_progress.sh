#!/bin/bash
cd /home/aaron/Projects/ai/docx
source venv/bin/activate

# Test with just 3 pages for quick demo
echo "Testing rendering and transcription progress..."
pdfx process /home/aaron/Projects/ai/pdf_sources/AGA-State-of-the-States-2023.pdf \
    output_v2/test_cli_progress/ \
    --pages 0,1,2 \
    --backend markitdown \
    --render \
    --progress