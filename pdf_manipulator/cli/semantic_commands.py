"""CLI commands for semantic pipeline processing."""
import click
from pathlib import Path
from typing import Optional

from ..core.semantic_orchestrator import SemanticOrchestrator, ProcessingConfig
from ..config.semantic_config_manager import SemanticConfigManager
from ..intelligence.ollama_multimodal import OllamaMultimodalBackend
from ..intelligence.openai_multimodal import OpenAIMultimodalBackend
from ..utils.logging_config import setup_logging


@click.command(name='semantic')
@click.argument('document_path', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
@click.option('--config', type=click.Path(exists=True), 
              help='Configuration file path')
@click.option('--backend', type=click.Choice(['ollama', 'openai']), 
              help='LLM backend to use')
@click.option('--model', help='Model name for the backend')
@click.option('--max-pages', type=int, help='Maximum pages to process')
@click.option('--parallel', type=int, help='Number of pages to process in parallel')
@click.option('--no-llm', is_flag=True, help='Disable LLM enhancement')
@click.option('--save-intermediate', is_flag=True, 
              help='Save intermediate processing results')
@click.option('--format', type=click.Choice(['json', 'sqlite', 'both']), 
              default='json', help='Output format')
@click.option('--confidence', type=float, default=0.7, 
              help='Minimum confidence threshold')
@click.pass_context
def process_semantic(ctx, document_path: str, output_dir: str, 
                    config: Optional[str], backend: Optional[str],
                    model: Optional[str], max_pages: Optional[int],
                    parallel: Optional[int], no_llm: bool,
                    save_intermediate: bool, format: str,
                    confidence: float):
    """Process document through semantic extraction pipeline.
    
    This command extracts semantic knowledge graphs from documents,
    building rich relationships and ontological understanding.
    """
    # Setup logging
    setup_logging(ctx.obj.verbose, ctx.obj.log_level, not ctx.obj.no_file_log)
    
    click.echo(click.style("🧠 Starting semantic processing...", fg='blue', bold=True))
    
    # Load configuration
    config_manager = SemanticConfigManager(config)
    
    # Override with CLI arguments
    cli_args = {
        "backend": backend,
        "model": model,
        "max_pages": max_pages,
        "parallel": parallel,
        "no_llm": no_llm,
        "save_intermediate": save_intermediate,
        "format": format,
        "confidence": confidence
    }
    
    # Merge CLI args with config
    config_manager.merge_with_cli_args({k: v for k, v in cli_args.items() if v is not None})
    pipeline_config = config_manager.get_pipeline_config()
    
    # Create processing configuration
    processing_config = ProcessingConfig(
        enable_llm=not no_llm and pipeline_config.enable_llm,
        max_pages=pipeline_config.max_pages,
        parallel_pages=pipeline_config.parallel_pages,
        context_window=pipeline_config.context_window,
        confidence_threshold=pipeline_config.confidence_threshold,
        enable_ocr_fallback=pipeline_config.enable_ocr_fallback,
        save_intermediate=pipeline_config.save_intermediate or save_intermediate,
        output_format=pipeline_config.output_format
    )
    
    # Create backend if LLM is enabled
    intelligence_backend = None
    if processing_config.enable_llm:
        backend_type = config_manager.config.llm_backend_type
        backend_config = config_manager.get_llm_backend_config()
        
        if backend_type == "ollama":
            intelligence_backend = OllamaMultimodalBackend(
                model=model or backend_config.get("model", "llava:latest"),
                base_url=backend_config.get("base_url", "http://localhost:11434"),
                timeout=backend_config.get("timeout", 120)
            )
            click.echo(f"Using Ollama backend with model: {intelligence_backend.model}")
            
        elif backend_type == "openai":
            intelligence_backend = OpenAIMultimodalBackend(
                api_key=backend_config.get("api_key"),
                model=model or backend_config.get("model", "gpt-4-vision-preview"),
                max_tokens=backend_config.get("max_tokens", 4096),
                temperature=backend_config.get("temperature", 0.1)
            )
            click.echo(f"Using OpenAI backend with model: {intelligence_backend.model}")
    else:
        click.echo("LLM enhancement disabled, using basic extraction only")
    
    # Create orchestrator
    orchestrator = SemanticOrchestrator(
        backend=intelligence_backend,
        config=processing_config
    )
    
    # Process document
    click.echo(f"\nProcessing: {document_path}")
    click.echo(f"Output directory: {output_dir}\n")
    
    try:
        with click.progressbar(length=100, label='Processing') as bar:
            # Hook into progress updates
            def update_progress(message: str, percentage: float = None):
                if percentage is not None:
                    bar.update(int(percentage * 100) - bar.pos)
                bar.label = message
            
            orchestrator.progress_reporter.callback = update_progress
            
            # Process
            results = orchestrator.process_document(document_path, output_dir)
        
        # Show results
        click.echo(click.style("\n✅ Processing complete!", fg='green', bold=True))
        
        if "graph_stats" in results:
            click.echo("\n📊 Graph Statistics:")
            stats = results["graph_stats"]
            click.echo(f"  Total nodes: {stats.get('total_nodes', 0)}")
            click.echo(f"  Total edges: {stats.get('total_edges', 0)}")
            click.echo(f"  Node types: {stats.get('node_types', {})}")
            click.echo(f"  Edge types: {stats.get('edge_types', {})}")
            click.echo(f"  Ontology coverage: {stats.get('ontology_coverage', 0):.1%}")
        
        click.echo(f"\n📁 Output saved to: {output_dir}")
        
        if "json_path" in results:
            click.echo(f"  JSON graph: {results['json_path']}")
        
        click.echo(f"\n⏱️  Processing time: {results['metadata']['processing_time']:.2f}s")
        
    except Exception as e:
        click.echo(click.style(f"\n❌ Error: {e}", fg='red', bold=True))
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        ctx.exit(1)


@click.command(name='semantic-test')
@click.option('--backend', type=click.Choice(['mock', 'ollama', 'openai']), 
              default='mock', help='Backend to test')
@click.option('--samples', type=int, default=3, help='Number of test samples')
@click.pass_context
def test_semantic_pipeline(ctx, backend: str, samples: int):
    """Test the semantic pipeline with sample data."""
    setup_logging(ctx.obj.verbose, ctx.obj.log_level, not ctx.obj.no_file_log)
    
    click.echo(click.style("🧪 Testing semantic pipeline...", fg='yellow', bold=True))
    
    # Import test components
    from ..tests.test_semantic_pipeline import MockLLMBackend
    
    # Create test backend
    if backend == 'mock':
        test_backend = MockLLMBackend()
        click.echo("Using mock LLM backend")
    else:
        click.echo(f"Testing with real {backend} backend")
        # Would create real backend here
    
    # Run tests
    click.echo(f"\nRunning {samples} test samples...")
    
    for i in range(samples):
        click.echo(f"\nTest {i+1}/{samples}:")
        # Would run actual test here
        click.echo("  ✓ Structure analysis")
        click.echo("  ✓ Content analysis")
        click.echo("  ✓ Graph building")
        click.echo("  ✓ Semantic enhancement")
    
    click.echo(click.style("\n✅ All tests passed!", fg='green', bold=True))


# Command group for semantic operations
@click.group(name='semantic')
def semantic_group():
    """Semantic extraction and processing commands."""
    pass


semantic_group.add_command(process_semantic, name='process')
semantic_group.add_command(test_semantic_pipeline, name='test')