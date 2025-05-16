-- Memory graph database schema
CREATE TABLE IF NOT EXISTS DOMAINS (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created TEXT NOT NULL,
    lastAccess TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS MEMORY_NODES (
    id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    path TEXT,
    content_summary TEXT,
    summary_timestamp TEXT,
    FOREIGN KEY (domain) REFERENCES DOMAINS(id)
);

CREATE TABLE IF NOT EXISTS MEMORY_EDGES (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    type TEXT NOT NULL,
    strength REAL NOT NULL,
    timestamp TEXT NOT NULL,
    domain TEXT NOT NULL,
    FOREIGN KEY (source) REFERENCES MEMORY_NODES(id),
    FOREIGN KEY (target) REFERENCES MEMORY_NODES(id),
    FOREIGN KEY (domain) REFERENCES DOMAINS(id)
);

CREATE TABLE IF NOT EXISTS MEMORY_TAGS (
    nodeId TEXT NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (nodeId, tag),
    FOREIGN KEY (nodeId) REFERENCES MEMORY_NODES(id)
);

CREATE TABLE IF NOT EXISTS PERSISTENCE (
    id INTEGER PRIMARY KEY,
    currentDomain TEXT,
    lastAccess TEXT,
    FOREIGN KEY (currentDomain) REFERENCES DOMAINS(id)
);

-- Create FTS table for content search
CREATE VIRTUAL TABLE IF NOT EXISTS memory_content_fts USING fts5(
    id UNINDEXED,
    content,
    content=MEMORY_NODES,
    content_rowid=rowid
);

-- Create triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS memory_fts_insert AFTER INSERT ON MEMORY_NODES
BEGIN
    INSERT INTO memory_content_fts(id, content) VALUES (new.id, new.content);
END;

CREATE TRIGGER IF NOT EXISTS memory_fts_update AFTER UPDATE ON MEMORY_NODES
BEGIN
    UPDATE memory_content_fts SET content = new.content WHERE id = new.id;
END;

CREATE TRIGGER IF NOT EXISTS memory_fts_delete AFTER DELETE ON MEMORY_NODES
BEGIN
    DELETE FROM memory_content_fts WHERE id = old.id;
END;