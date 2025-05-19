"""Example script demonstrating the complete semantic pipeline."""
import sys
from pathlib import Path
import logging
from typing import Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from pdf_manipulator.core.semantic_orchestrator import SemanticOrchestrator, ProcessingConfig
from pdf_manipulator.config.semantic_config_manager import SemanticConfigManager
from pdf_manipulator.intelligence.ollama_multimodal import OllamaMultimodalBackend
from pdf_manipulator.intelligence.openai_multimodal import OpenAIMultimodalBackend


def setup_logging(level: str = "INFO"):
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_backend(backend_type: str, config_manager: SemanticConfigManager):
    """Create the appropriate intelligence backend."""
    backend_config = config_manager.get_llm_backend_config()
    
    if backend_type == "ollama":
        return OllamaMultimodalBackend(
            model=backend_config.get("model", "llava:latest"),
            base_url=backend_config.get("base_url", "http://localhost:11434"),
            timeout=backend_config.get("timeout", 120)
        )
    elif backend_type == "openai":
        return OpenAIMultimodalBackend(
            api_key=backend_config.get("api_key"),
            model=backend_config.get("model", "gpt-4-vision-preview"),
            max_tokens=backend_config.get("max_tokens", 4096),
            temperature=backend_config.get("temperature", 0.1)
        )
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")


def process_document(
    document_path: str,
    output_dir: str,
    config_path: Optional[str] = None,
    backend_type: Optional[str] = None,
    max_pages: Optional[int] = None
):
    """Process a document through the semantic pipeline."""
    # Load configuration
    config_manager = SemanticConfigManager(config_path)
    pipeline_config = config_manager.get_pipeline_config()
    
    # Override with command line arguments
    if backend_type:
        config_manager.set("llm_backend.type", backend_type)
    if max_pages:
        config_manager.set("pipeline.max_pages", max_pages)
    
    # Create processing configuration
    processing_config = ProcessingConfig(
        enable_llm=pipeline_config.enable_llm,
        max_pages=pipeline_config.max_pages,
        parallel_pages=pipeline_config.parallel_pages,
        context_window=pipeline_config.context_window,
        confidence_threshold=pipeline_config.confidence_threshold,
        enable_ocr_fallback=pipeline_config.enable_ocr_fallback,
        save_intermediate=pipeline_config.save_intermediate,
        output_format=pipeline_config.output_format
    )
    
    # Create backend if LLM is enabled
    backend = None
    if processing_config.enable_llm:
        backend = create_backend(
            config_manager.config.llm_backend_type,
            config_manager
        )
        print(f"Using {backend.get_model_info()['provider']} backend")
    
    # Create orchestrator
    orchestrator = SemanticOrchestrator(
        backend=backend,
        config=processing_config
    )
    
    # Process document
    print(f"Processing {document_path}...")
    results = orchestrator.process_document(document_path, output_dir)
    
    # Print results
    print("\nProcessing Complete!")
    print(f"Output saved to: {output_dir}")
    print("\nGraph Statistics:")
    stats = results.get("graph_stats", {})
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return results


def main():
    """Main example function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process document through semantic pipeline")
    parser.add_argument("document", help="Path to document")
    parser.add_argument("output", help="Output directory")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--backend", choices=["ollama", "openai"], help="LLM backend")
    parser.add_argument("--max-pages", type=int, help="Maximum pages to process")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM enhancement")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Process document
    process_document(
        document_path=args.document,
        output_dir=args.output,
        config_path=args.config,
        backend_type=args.backend,
        max_pages=args.max_pages
    )


if __name__ == "__main__":
    main()


# Example usage:
"""
# Process with default configuration
python semantic_pipeline_example.py document.pdf output/

# Process with custom config
python semantic_pipeline_example.py document.pdf output/ --config my_config.yaml

# Process with OpenAI backend
python semantic_pipeline_example.py document.pdf output/ --backend openai

# Process only first 10 pages
python semantic_pipeline_example.py document.pdf output/ --max-pages 10

# Process without LLM (basic extraction only)
python semantic_pipeline_example.py document.pdf output/ --no-llm

# Process with debug logging
python semantic_pipeline_example.py document.pdf output/ --log-level DEBUG
"""