"""Adapter for integrating memory-graph storage with PDF processing."""
import sqlite3
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import uuid
from datetime import datetime


@dataclass
class MemoryConfig:
    """Configuration for memory adapter."""
    database_path: Path
    domain_name: str = "pdf_processing"
    domain_description: str = "Domain for PDF document processing and extraction"
    enable_relationships: bool = True  # Create relationships between related pages/sections
    enable_summaries: bool = True      # Generate summaries for memories
    tags_prefix: str = "pdf:"         # Prefix for tags (e.g., "pdf:page", "pdf:section")
    min_content_length: int = 50      # Minimum content length to create a memory


class MemoryAdapter:
    """Adapter for storing PDF content in memory-graph SQLite database."""
    
    def __init__(self, config: MemoryConfig):
        """Initialize the memory adapter with configuration."""
        self.config = config
        self.conn: Optional[sqlite3.Connection] = None
        self.domain_id: Optional[str] = None
        
    def connect(self) -> None:
        """Connect to the database and initialize domain."""
        self.conn = sqlite3.connect(str(self.config.database_path))
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Create schema if it doesn't exist
        self._create_schema()
        
        # Check if domain exists, create if not
        cursor = self.conn.execute(
            "SELECT id FROM DOMAINS WHERE name = ?", 
            (self.config.domain_name,)
        )
        result = cursor.fetchone()
        
        if result:
            self.domain_id = result[0]
            # Update last access
            self.conn.execute(
                "UPDATE DOMAINS SET lastAccess = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), self.domain_id)
            )
        else:
            # Create new domain
            self.domain_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            self.conn.execute(
                "INSERT INTO DOMAINS (id, name, description, created, lastAccess) VALUES (?, ?, ?, ?, ?)",
                (self.domain_id, self.config.domain_name, self.config.domain_description, now, now)
            )
            
            # Set as current domain (no REPLACE since we have CHECK constraint)
            cursor = self.conn.execute("SELECT id FROM PERSISTENCE WHERE id = 1")
            if cursor.fetchone():
                self.conn.execute(
                    "UPDATE PERSISTENCE SET currentDomain = ?, lastAccess = ? WHERE id = 1",
                    (self.domain_id, now)
                )
            else:
                self.conn.execute(
                    "INSERT INTO PERSISTENCE (id, currentDomain, lastAccess) VALUES (1, ?, ?)",
                    (self.domain_id, now)
                )
        
        self.conn.commit()
        
    def disconnect(self) -> None:
        """Disconnect from the database."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def _create_schema(self) -> None:
        """Create the database schema if it doesn't exist."""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS DOMAINS (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created TEXT NOT NULL,
            lastAccess TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS PERSISTENCE (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            currentDomain TEXT NOT NULL,
            lastAccess TEXT NOT NULL,
            lastMemoryId TEXT,
            FOREIGN KEY (currentDomain) REFERENCES DOMAINS(id)
        );

        CREATE TABLE IF NOT EXISTS MEMORY_NODES (
            id TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            path TEXT DEFAULT '/',
            content_summary TEXT,
            summary_timestamp TEXT,
            FOREIGN KEY (domain) REFERENCES DOMAINS(id)
        );

        CREATE TABLE IF NOT EXISTS MEMORY_TAGS (
            nodeId TEXT NOT NULL,
            tag TEXT NOT NULL,
            PRIMARY KEY (nodeId, tag),
            FOREIGN KEY (nodeId) REFERENCES MEMORY_NODES(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS MEMORY_EDGES (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            type TEXT NOT NULL,
            strength REAL NOT NULL CHECK (strength >= 0 AND strength <= 1),
            timestamp TEXT NOT NULL,
            domain TEXT NOT NULL,
            FOREIGN KEY (source) REFERENCES MEMORY_NODES(id) ON DELETE CASCADE,
            FOREIGN KEY (target) REFERENCES MEMORY_NODES(id) ON DELETE CASCADE,
            FOREIGN KEY (domain) REFERENCES DOMAINS(id)
        );

        CREATE TABLE IF NOT EXISTS DOMAIN_REFS (
            nodeId TEXT NOT NULL,
            domain TEXT NOT NULL,
            targetDomain TEXT NOT NULL,
            targetNodeId TEXT NOT NULL,
            description TEXT,
            bidirectional INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (nodeId, targetDomain, targetNodeId),
            FOREIGN KEY (nodeId) REFERENCES MEMORY_NODES(id) ON DELETE CASCADE,
            FOREIGN KEY (domain) REFERENCES DOMAINS(id),
            FOREIGN KEY (targetDomain) REFERENCES DOMAINS(id)
        );

        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_memory_nodes_domain ON MEMORY_NODES(domain);
        CREATE INDEX IF NOT EXISTS idx_memory_tags_tag ON MEMORY_TAGS(tag);
        CREATE INDEX IF NOT EXISTS idx_memory_edges_source ON MEMORY_EDGES(source, domain);
        CREATE INDEX IF NOT EXISTS idx_memory_edges_target ON MEMORY_EDGES(target, domain);
        CREATE INDEX IF NOT EXISTS idx_domain_refs_target ON DOMAIN_REFS(targetDomain, targetNodeId);

        -- Full text search table with proper structure
        CREATE VIRTUAL TABLE IF NOT EXISTS memory_content_fts USING fts5(
            id,              -- Memory ID
            content,         -- Memory content
            content_summary, -- Memory summary
            path,            -- Organization path
            tags,            -- Concatenated tags for searching
            domain,          -- Domain ID
            tokenize="porter unicode61"  -- Use Porter stemming algorithm
        );

        -- Triggers to maintain FTS synchronization
        CREATE TRIGGER IF NOT EXISTS memory_nodes_ai AFTER INSERT ON MEMORY_NODES BEGIN
            INSERT INTO memory_content_fts(id, content, content_summary, path, domain)
            VALUES (new.id, new.content, new.content_summary, new.path, new.domain);
        END;

        CREATE TRIGGER IF NOT EXISTS memory_nodes_ad AFTER DELETE ON MEMORY_NODES BEGIN
            DELETE FROM memory_content_fts WHERE id = old.id;
        END;

        CREATE TRIGGER IF NOT EXISTS memory_nodes_au AFTER UPDATE ON MEMORY_NODES BEGIN
            DELETE FROM memory_content_fts WHERE id = old.id;
            INSERT INTO memory_content_fts(id, content, content_summary, path, domain)
            VALUES (new.id, new.content, new.content_summary, new.path, new.domain);
        END;

        CREATE TRIGGER IF NOT EXISTS memory_tags_ai AFTER INSERT ON MEMORY_TAGS BEGIN
            UPDATE memory_content_fts 
            SET tags = (SELECT group_concat(tag, ' ') FROM MEMORY_TAGS WHERE nodeId = new.nodeId)
            WHERE id = new.nodeId;
        END;

        CREATE TRIGGER IF NOT EXISTS memory_tags_ad AFTER DELETE ON MEMORY_TAGS BEGIN
            UPDATE memory_content_fts 
            SET tags = (SELECT group_concat(tag, ' ') FROM MEMORY_TAGS WHERE nodeId = old.nodeId)
            WHERE id = old.nodeId;
        END;
        """
        
        # Execute schema creation
        self.conn.executescript(schema_sql)
        self.conn.commit()
            
    def store_memory(
        self,
        content: str,
        path: str = "/",
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        relationships: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a memory node in the graph.
        
        Args:
            content: The content of the memory
            path: The path/category for the memory
            tags: List of tags for the memory
            summary: Optional summary of the content
            relationships: Dictionary of relationship types to target memories
            metadata: Optional metadata (stored in content as JSON prefix)
            
        Returns:
            The ID of the created memory node
        """
        if not self.conn:
            raise RuntimeError("Not connected to database")
            
        # Skip if content too short
        if len(content.strip()) < self.config.min_content_length:
            return None
            
        # Generate ID
        memory_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # If metadata provided, prepend to content as JSON
        if metadata:
            content = f"METADATA:{json.dumps(metadata)}\n\n{content}"
        
        # Insert memory node
        self.conn.execute(
            """INSERT INTO MEMORY_NODES 
               (id, domain, content, timestamp, path, content_summary, summary_timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (memory_id, self.domain_id, content, now, path, summary, now if summary else None)
        )
        
        # Add tags
        if tags:
            for tag in tags:
                # Add prefix if configured
                if self.config.tags_prefix and not tag.startswith(self.config.tags_prefix):
                    tag = f"{self.config.tags_prefix}{tag}"
                    
                self.conn.execute(
                    "INSERT INTO MEMORY_TAGS (nodeId, tag) VALUES (?, ?)",
                    (memory_id, tag)
                )
        
        # Add relationships
        if relationships and self.config.enable_relationships:
            for rel_type, targets in relationships.items():
                for target in targets:
                    edge_id = f"{memory_id}-{target['targetId']}-{rel_type}"
                    strength = target.get('strength', 0.8)
                    
                    self.conn.execute(
                        """INSERT INTO MEMORY_EDGES 
                           (id, source, target, type, strength, timestamp, domain)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (edge_id, memory_id, target['targetId'], rel_type, strength, now, self.domain_id)
                    )
        
        self.conn.commit()
        return memory_id
    
    def update_memory_summary(self, memory_id: str, summary: str) -> None:
        """Update the summary of an existing memory."""
        if not self.conn:
            raise RuntimeError("Not connected to database")
            
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            "UPDATE MEMORY_NODES SET content_summary = ?, summary_timestamp = ? WHERE id = ?",
            (summary, now, memory_id)
        )
        self.conn.commit()
    
    def create_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str = "relates_to",
        strength: float = 0.8
    ) -> None:
        """Create a relationship between two memory nodes."""
        if not self.conn:
            raise RuntimeError("Not connected to database")
            
        edge_id = f"{source_id}-{target_id}-{rel_type}"
        now = datetime.utcnow().isoformat()
        
        self.conn.execute(
            """INSERT OR REPLACE INTO MEMORY_EDGES 
               (id, source, target, type, strength, timestamp, domain)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (edge_id, source_id, target_id, rel_type, strength, now, self.domain_id)
        )
        self.conn.commit()
    
    def search_memories(
        self,
        query: str,
        limit: int = 10,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for memories using full-text search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            domain: Optional domain filter (defaults to current domain)
            
        Returns:
            List of memory nodes matching the search
        """
        if not self.conn:
            raise RuntimeError("Not connected to database")
            
        domain = domain or self.domain_id
        
        # Use MATCH for FTS5
        cursor = self.conn.execute(
            """SELECT m.*, 
                      GROUP_CONCAT(mt.tag) as tags
               FROM MEMORY_NODES m
               JOIN memory_content_fts fts ON m.id = fts.id
               LEFT JOIN MEMORY_TAGS mt ON m.id = mt.nodeId
               WHERE memory_content_fts MATCH ? AND m.domain = ?
               GROUP BY m.id
               ORDER BY rank
               LIMIT ?""",
            (query, domain, limit)
        )
        
        results = []
        for row in cursor:
            memory = {
                'id': row[0],
                'domain': row[1],
                'content': row[2],
                'timestamp': row[3],
                'path': row[4],
                'content_summary': row[5],
                'summary_timestamp': row[6],
                'tags': row[7].split(',') if row[7] else []
            }
            results.append(memory)
            
        return results
    
    def get_recent_memories(
        self,
        limit: int = 10,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent memories from the graph.
        
        Args:
            limit: Maximum number of results
            domain: Optional domain filter (defaults to current domain)
            
        Returns:
            List of recent memory nodes
        """
        if not self.conn:
            raise RuntimeError("Not connected to database")
            
        domain = domain or self.domain_id
        
        cursor = self.conn.execute(
            """SELECT m.*, 
                      GROUP_CONCAT(mt.tag) as tags
               FROM MEMORY_NODES m
               LEFT JOIN MEMORY_TAGS mt ON m.id = mt.nodeId
               WHERE m.domain = ?
               GROUP BY m.id
               ORDER BY m.timestamp DESC
               LIMIT ?""",
            (domain, limit)
        )
        
        results = []
        for row in cursor:
            memory = {
                'id': row[0],
                'domain': row[1],
                'content': row[2],
                'timestamp': row[3],
                'path': row[4],
                'content_summary': row[5],
                'summary_timestamp': row[6],
                'tags': row[7].split(',') if row[7] else []
            }
            results.append(memory)
            
        return results