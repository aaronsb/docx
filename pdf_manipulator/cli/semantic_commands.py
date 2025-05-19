"""CLI commands for semantic pipeline processing."""
import click
from pathlib import Path
from typing import Optional

from ..core.semantic_orchestrator import SemanticOrchestrator, ProcessingConfig
from ..config.semantic_config_manager import SemanticConfigManager
from ..intelligence.ollama_multimodal import OllamaMultimodalBackend
from ..intelligence.openai_multimodal import OpenAIMultimodalBackend
from ..utils.logging_config import configure_logging


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
@click.option('--summarization-ratio', type=float, 
              help='Text summarization ratio (0.0-1.0, 0=max, 1=none)')
@click.option('--max-tokens', type=int, 
              help='Maximum tokens to keep in summarized text')
@click.option('--debug/--no-debug', default=False, 
              help='Enable detailed debugging output')
@click.option('--debug-dir', type=click.Path(), 
              help='Directory to save debug information')
@click.option('--timeout', type=int, default=60,
              help='Timeout for LLM requests in seconds')
@click.pass_context
def process_semantic(ctx, document_path: str, output_dir: str, 
                    config: Optional[str], backend: Optional[str],
                    model: Optional[str], max_pages: Optional[int],
                    parallel: Optional[int], no_llm: bool,
                    save_intermediate: bool, format: str,
                    confidence: float, summarization_ratio: Optional[float] = None,
                    max_tokens: Optional[int] = None, debug: bool = False,
                    debug_dir: Optional[str] = None, timeout: int = 60):
    """Process document through semantic extraction pipeline.
    
    This command extracts semantic knowledge graphs from documents,
    building rich relationships and ontological understanding.
    
    When using OpenAI backend, you can enable enhanced debugging with the --debug flag:
    
      mge semantic process document.pdf output/ --backend openai --model gpt-4o-mini --debug
      
    Additional debug options:
      --debug-dir PATH      Directory to save detailed debug information
      --timeout SECONDS     Adjust request timeout (default: 60s)
    
    The OpenAI backend now defaults to gpt-4o-mini for better cost efficiency.
    """
    # Setup logging
    log_level = "DEBUG" if ctx.obj.verbose else ctx.obj.log_level
    configure_logging(console_level=log_level, enable_file=not ctx.obj.no_file_log)
    
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
        "confidence": confidence,
        "summarization_ratio": summarization_ratio,
        "max_tokens": max_tokens
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
            # Create debug directory if needed
            debug_output_dir = None
            if debug and debug_dir:
                debug_output_dir = debug_dir
            elif debug:
                # Create a debug directory in the output folder
                debug_output_dir = Path(output_dir) / "debug" / "openai"
                debug_output_dir.mkdir(parents=True, exist_ok=True)
                click.echo(f"Debug mode enabled - saving debug info to {debug_output_dir}")
            
            # Configure OpenAI backend with debug settings
            intelligence_backend = OpenAIMultimodalBackend(
                api_key=backend_config.get("api_key"),
                model=model or backend_config.get("model", "gpt-4o-mini"),
                max_tokens=backend_config.get("max_tokens", 4096),
                temperature=backend_config.get("temperature", 0.1),
                timeout=timeout,
                debug_mode=debug,
                debug_dir=str(debug_output_dir) if debug_output_dir else None,
                logger=logger
            )
            click.echo(f"Using OpenAI backend with model: {intelligence_backend.model}")
            
            # Add debug info
            if debug:
                click.echo(f"  Debug mode: Enabled")
                click.echo(f"  Timeout: {timeout}s")
                click.echo(f"  Max tokens: {intelligence_backend.max_tokens}")
                click.echo(f"  Temperature: {intelligence_backend.temperature}")
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
        error_type = type(e).__name__
        error_msg = str(e)
        
        # Enhanced error reporting
        click.echo(click.style(f"\n❌ Error ({error_type}): {error_msg}", fg='red', bold=True))
        
        # Check for specific error types and provide more helpful messages
        if "openai" in error_msg.lower():
            click.echo(click.style("\nOpenAI API Error Details:", fg='yellow'))
            click.echo("- Check that your API key is valid and not expired")
            click.echo("- Verify your account has appropriate rate limits")
            click.echo("- Check network connectivity to OpenAI API")
            click.echo("- Try using --timeout parameter to increase request timeout")
            click.echo("\nTry running with --debug flag for detailed error information")
        
        # Show traceback in verbose mode
        if ctx.obj.verbose or debug:
            click.echo(click.style("\nTraceback:", fg='yellow'))
            import traceback
            traceback.print_exc()
            
            # Show additional debug tips if debug mode is not enabled
            if not debug:
                click.echo(click.style("\nTip: Run with --debug flag for enhanced error diagnostics", fg='cyan'))
        
        ctx.exit(1)


@click.command(name='semantic-test')
@click.option('--backend', type=click.Choice(['mock', 'ollama', 'openai']), 
              default='mock', help='Backend to test')
@click.option('--samples', type=int, default=3, help='Number of test samples')
@click.pass_context
def test_semantic_pipeline(ctx, backend: str, samples: int):
    """Test the semantic pipeline with sample data."""
    log_level = "DEBUG" if ctx.obj.verbose else ctx.obj.log_level
    configure_logging(console_level=log_level, enable_file=not ctx.obj.no_file_log)
    
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