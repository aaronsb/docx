"""Configuration management commands."""
import os
import sys
import subprocess
from pathlib import Path

import click

from pdf_manipulator.utils.config import (
    load_config, create_default_config, get_all_config_paths,
    USER_CONFIG_DIR, PROJECT_CONFIG_DIR
)
from .base import ProgressReporter


@click.command(name='config')
@click.option('--user', is_flag=True, help='Create/edit user configuration')
@click.option('--project', is_flag=True, help='Create/edit project configuration')
@click.option('--list', 'list_configs', is_flag=True, help='List available configuration files')
@click.option('--editor', is_flag=True, help='Open configuration in default editor')
@click.pass_context
def manage_config(ctx, user: bool, project: bool, list_configs: bool, editor: bool):
    """Manage configuration files."""
    verbose = ctx.obj.get('verbose', False)
    reporter = ProgressReporter(verbose)
    
    if list_configs:
        # List available configuration files
        config_paths = get_all_config_paths()
        click.echo("Available configuration files:")
        click.echo(f"  System: {config_paths.system_config}")
        click.echo(f"  User:   {config_paths.user_config}" + 
                  (" (active)" if config_paths.user_config.exists() else " (not found)"))
        click.echo(f"  Project: {config_paths.project_config}" + 
                  (" (active)" if config_paths.project_config.exists() else " (not found)"))
        return
    
    if user:
        # Create or update user configuration
        config_path = Path(USER_CONFIG_DIR) / "config.yaml"
        if not config_path.exists():
            create_default_config(config_path)
            click.echo(f"Created user configuration at: {config_path}")
        else:
            click.echo(f"User configuration exists at: {config_path}")
        
        if editor:
            _open_in_editor(config_path)
    
    elif project:
        # Create or update project configuration
        config_path = Path(PROJECT_CONFIG_DIR) / "config.yaml"
        if not config_path.exists():
            create_default_config(config_path)
            click.echo(f"Created project configuration at: {config_path}")
        else:
            click.echo(f"Project configuration exists at: {config_path}")
        
        if editor:
            _open_in_editor(config_path)
    
    elif editor:
        # Open current config in editor
        config_path = ctx.obj.get('config_path')
        if config_path:
            _open_in_editor(Path(config_path))
        else:
            click.echo("No configuration file found", err=True)
    
    else:
        # Show current configuration
        config_path = ctx.obj.get('config_path')
        config = ctx.obj.get('config')
        
        if config_path:
            click.echo(f"Current configuration: {config_path}")
            if verbose:
                import yaml
                click.echo("\nConfiguration contents:")
                click.echo(yaml.dump(config, default_flow_style=False))
        else:
            click.echo("No configuration file loaded")


@click.command(name='config-init')
@click.option('--user', is_flag=True, help='Initialize user configuration')
@click.option('--project', is_flag=True, help='Initialize project configuration')
@click.option('--force', is_flag=True, help='Overwrite existing configuration')
@click.pass_context
def init_config(ctx, user: bool, project: bool, force: bool):
    """Initialize configuration with semantic defaults."""
    verbose = ctx.obj.get('verbose', False)
    reporter = ProgressReporter(verbose)
    
    if not user and not project:
        user = True  # Default to user config
    
    if user:
        config_path = Path(USER_CONFIG_DIR) / "config.yaml"
        config_type = "user"
    else:
        config_path = Path(PROJECT_CONFIG_DIR) / "config.yaml"
        config_type = "project"
    
    if config_path.exists() and not force:
        click.echo(f"{config_type.capitalize()} configuration already exists at: {config_path}")
        click.echo("Use --force to overwrite")
        return
    
    try:
        reporter.start(f"Creating {config_type} configuration")
        
        # Create semantic-focused default config
        import yaml
        semantic_config = {
            'memory': {
                'enabled': True,
                'database_name': 'memory_graph.db',
                'domain': {
                    'name': 'pdf_processing',
                    'description': 'Document knowledge base'
                },
                'extraction': {
                    'min_content_length': 50,
                    'detect_relationships': True,
                    'generate_summaries': True,
                    'tags_prefix': 'pdf:'
                },
                'graph': {
                    'max_depth': 3,
                    'similarity_threshold': 0.7
                }
            },
            'intelligence': {
                'default_backend': 'markitdown',
                'use_context': True,
                'backends': {
                    'markitdown': {},
                    'ollama': {
                        'model': 'llava:latest',
                        'base_url': 'http://localhost:11434',
                        'timeout': 120
                    }
                }
            },
            'processing': {
                'use_ocr_fallback': True,
                'default_prompt': 'Extract all text and structure from this document, preserving semantic meaning.',
                'batch_size': 5,
                'concurrent_pages': 3
            }
        }
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(semantic_config, f, default_flow_style=False)
        
        reporter.complete(f"Created semantic configuration at: {config_path}")
        
    except Exception as e:
        reporter.error(str(e))
        raise click.ClickException(str(e))


def _open_in_editor(file_path: Path):
    """Open a file in the default editor."""
    # Try common editor environment variables
    editor = os.environ.get('EDITOR') or os.environ.get('VISUAL')
    
    if not editor:
        # Try common editors
        for cmd in ['code', 'vim', 'nano', 'notepad']:
            if _command_exists(cmd):
                editor = cmd
                break
    
    if not editor:
        click.echo("No editor found. Set EDITOR environment variable.", err=True)
        return
    
    try:
        subprocess.run([editor, str(file_path)])
    except Exception as e:
        click.echo(f"Failed to open editor: {e}", err=True)


def _command_exists(command: str) -> bool:
    """Check if a command exists in PATH."""
    try:
        subprocess.run(['which', command], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False