"""Memory graph command-line interface."""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from pdf_manipulator.memory.memory_adapter import MemoryAdapter, MemoryConfig
from pdf_manipulator.memory.memory_processor import MemoryProcessor
from .base import ProgressReporter


@click.group(name='memory')
@click.pass_context
def memory_group(ctx):
    """Manage memory graph databases."""
    pass


@memory_group.command(name='create')
@click.argument('name')
@click.option('--database', '-d', type=click.Path(), help='Database file path')
@click.option('--description', '-desc', help='Domain description')
@click.pass_context
def create_memory(ctx, name: str, database: Optional[str], description: Optional[str]):
    """Create a new memory domain."""
    reporter = ProgressReporter(ctx.obj.get('verbose', False))
    
    if not database:
        database = f"{name}_memory.db"
    
    if not description:
        description = f"Memory domain for {name}"
    
    try:
        reporter.start(f"Creating memory domain '{name}' in {database}")
        
        config = MemoryConfig(
            database_path=Path(database),
            domain_name=name,
            domain_description=description
        )
        
        adapter = MemoryAdapter(config)
        adapter.connect()
        adapter.disconnect()
        
        reporter.complete(f"Created memory domain '{name}'")
        
    except Exception as e:
        reporter.error(str(e))
        raise click.ClickException(str(e))


@memory_group.command(name='search')
@click.argument('query')
@click.option('--database', '-d', type=click.Path(exists=True), required=True, 
              help='Path to memory database')
@click.option('--limit', type=int, default=10, help='Maximum results to return')
@click.option('--domain', help='Specific domain to search')
@click.pass_context
def search_memory(ctx, query: str, database: str, limit: int, domain: Optional[str]):
    """Search memories in the knowledge graph."""
    reporter = ProgressReporter(ctx.obj.get('verbose', False))
    
    try:
        reporter.start(f"Searching for '{query}' in {database}")
        
        memory_config = MemoryConfig(database_path=Path(database))
        adapter = MemoryAdapter(memory_config)
        adapter.connect()
        
        # Search memories
        results = adapter.search_memories(query, limit=limit, domain=domain)
        
        click.echo(f"\nFound {len(results)} memories matching '{query}':")
        for i, memory in enumerate(results):
            click.echo(f"\n{i+1}. {memory['path']}")
            click.echo(f"   ID: {memory['id'][:8]}...")
            click.echo(f"   Tags: {', '.join(memory['tags'])}")
            
            content_preview = memory['content'][:200] + "..." if len(memory['content']) > 200 else memory['content']
            click.echo(f"   Content: {content_preview}")
            
            if memory.get('content_summary'):
                click.echo(f"   Summary: {memory['content_summary']}")
        
        adapter.disconnect()
        
    except Exception as e:
        reporter.error(str(e))
        raise click.ClickException(str(e))


@memory_group.command(name='info')
@click.option('--database', '-d', type=click.Path(exists=True), required=True,
              help='Path to memory database')
@click.pass_context
def memory_info(ctx, database: str):
    """Display information about a memory database."""
    reporter = ProgressReporter(ctx.obj.get('verbose', False))
    
    try:
        reporter.start(f"Analyzing {database}")
        
        memory_config = MemoryConfig(database_path=Path(database))
        adapter = MemoryAdapter(memory_config)
        adapter.connect()
        
        # Get database statistics
        cursor = adapter.conn.execute("SELECT COUNT(*) FROM MEMORY_NODES")
        node_count = cursor.fetchone()[0]
        
        cursor = adapter.conn.execute("SELECT COUNT(*) FROM MEMORY_EDGES")
        edge_count = cursor.fetchone()[0]
        
        cursor = adapter.conn.execute("SELECT COUNT(DISTINCT domain) FROM MEMORY_NODES")
        domain_count = cursor.fetchone()[0]
        
        cursor = adapter.conn.execute("SELECT id, name, description FROM DOMAINS")
        domains = cursor.fetchall()
        
        click.echo(f"\nMemory database: {database}")
        click.echo(f"Total memories: {node_count}")
        click.echo(f"Total relationships: {edge_count}")
        click.echo(f"Domains: {domain_count}")
        
        if domains:
            click.echo("\nAvailable domains:")
            for domain_id, domain_name, domain_desc in domains:
                cursor = adapter.conn.execute(
                    "SELECT COUNT(*) FROM MEMORY_NODES WHERE domain = ?",
                    (domain_id,)
                )
                count = cursor.fetchone()[0]
                click.echo(f"  - {domain_name}: {count} memories")
                if domain_desc:
                    click.echo(f"    {domain_desc}")
        
        # Recent memories
        recent = adapter.get_recent_memories(limit=5)
        if recent:
            click.echo("\nRecent memories:")
            for i, memory in enumerate(recent):
                click.echo(f"  {i+1}. {memory['path']} ({memory['timestamp']})")
        
        adapter.disconnect()
        
    except Exception as e:
        reporter.error(str(e))
        raise click.ClickException(str(e))


@memory_group.command(name='export')
@click.option('--database', '-d', type=click.Path(exists=True), required=True,
              help='Path to memory database')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--format', type=click.Choice(['json', 'csv']), default='json',
              help='Export format')
@click.pass_context
def export_memory(ctx, database: str, output: Optional[str], format: str):
    """Export memory database contents."""
    reporter = ProgressReporter(ctx.obj.get('verbose', False))
    
    if not output:
        output = database.replace('.db', f'_export.{format}')
    
    try:
        reporter.start(f"Exporting {database} to {output}")
        
        memory_config = MemoryConfig(database_path=Path(database))
        
        with MemoryProcessor(memory_config) as processor:
            # Get all memories
            adapter = processor.adapter
            cursor = adapter.conn.execute(
                """SELECT m.*, GROUP_CONCAT(mt.tag) as tags
                   FROM MEMORY_NODES m
                   LEFT JOIN MEMORY_TAGS mt ON m.id = mt.nodeId
                   GROUP BY m.id"""
            )
            
            memories = []
            for row in cursor:
                memory = {
                    'id': row[0],
                    'domain': row[1],
                    'content': row[2],
                    'timestamp': row[3],
                    'path': row[4],
                    'content_summary': row[5],
                    'tags': row[7].split(',') if row[7] else []
                }
                memories.append(memory)
            
            # Get relationships
            cursor = adapter.conn.execute("SELECT * FROM MEMORY_EDGES")
            edges = []
            for row in cursor:
                edge = {
                    'id': row[0],
                    'source': row[1],
                    'target': row[2],
                    'type': row[3],
                    'strength': row[4],
                    'timestamp': row[5],
                    'domain': row[6]
                }
                edges.append(edge)
            
            # Export data
            if format == 'json':
                export_data = {
                    'memories': memories,
                    'relationships': edges,
                    'metadata': {
                        'exported_at': datetime.now().isoformat(),
                        'total_memories': len(memories),
                        'total_relationships': len(edges),
                        'database': database
                    }
                }
                
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2)
            
            else:  # CSV format
                # Export memories
                import csv
                memory_file = output.replace('.csv', '_memories.csv')
                with open(memory_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['id', 'domain', 'path', 'content', 'summary', 'tags', 'timestamp'])
                    writer.writeheader()
                    for mem in memories:
                        mem['tags'] = ';'.join(mem['tags'])
                        mem['summary'] = mem.get('content_summary', '')
                        writer.writerow(mem)
                
                # Export relationships
                edge_file = output.replace('.csv', '_relationships.csv')
                with open(edge_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['id', 'source', 'target', 'type', 'strength', 'domain', 'timestamp'])
                    writer.writeheader()
                    writer.writerows(edges)
                
                click.echo(f"Exported memories to {memory_file}")
                click.echo(f"Exported relationships to {edge_file}")
            
            reporter.complete(f"Exported {len(memories)} memories and {len(edges)} relationships")
    
    except Exception as e:
        reporter.error(str(e))
        raise click.ClickException(str(e))


@memory_group.command(name='connect')
@click.argument('database1', type=click.Path(exists=True))
@click.argument('database2', type=click.Path(exists=True))
@click.option('--relationship', '-r', default='related_to', 
              help='Relationship type between documents')
@click.option('--strength', '-s', type=float, default=0.7,
              help='Relationship strength (0-1)')
@click.pass_context
def connect_memories(ctx, database1: str, database2: str, relationship: str, strength: float):
    """Connect two memory databases through cross-references."""
    reporter = ProgressReporter(ctx.obj.get('verbose', False))
    
    try:
        reporter.start(f"Connecting {database1} and {database2}")
        
        # TODO: Implement cross-database connections
        # This would involve creating domain references between databases
        
        click.echo("Cross-database connections not yet implemented")
        
    except Exception as e:
        reporter.error(str(e))
        raise click.ClickException(str(e))