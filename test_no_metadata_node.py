#!/usr/bin/env python3
"""Test that metadata is not prepended to memory content."""
import sqlite3
import json
from pathlib import Path


def check_database_for_metadata_nodes(db_path: str):
    """Check if the database contains metadata-prepended nodes."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query all memory nodes
    cursor.execute("SELECT id, content FROM MEMORY_NODES")
    nodes = cursor.fetchall()
    
    metadata_nodes = []
    
    for node_id, content in nodes:
        if content.startswith("METADATA:"):
            metadata_nodes.append({
                'id': node_id,
                'content_preview': content[:200]
            })
    
    conn.close()
    
    return metadata_nodes


def main():
    """Main test function."""
    # Example database path
    db_path = "/home/aaron/Projects/ai/pdf_sources/zeroshot/2505.03335v2/memory_graph.db"
    
    if Path(db_path).exists():
        print(f"Checking database: {db_path}")
        metadata_nodes = check_database_for_metadata_nodes(db_path)
        
        if metadata_nodes:
            print(f"\nFound {len(metadata_nodes)} nodes with METADATA prefix:")
            for node in metadata_nodes:
                print(f"\nNode ID: {node['id']}")
                print(f"Content preview: {node['content_preview']}...")
        else:
            print("\n✓ No nodes with METADATA prefix found!")
    else:
        print(f"Database not found at: {db_path}")
        print("\nTo test, process a document and then run:")
        print(f"  python {__file__} /path/to/memory_graph.db")


if __name__ == "__main__":
    main()