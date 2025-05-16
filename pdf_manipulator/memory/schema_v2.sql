-- Memory graph database schema v2 - matching memory-graph-mcp
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