# DocX Refactoring Plan

This document outlines the plan to refactor monolithic code structures and clarify the processor hierarchy.

## 1. CLI Module Refactoring

### Current State
- `cli/commands.py`: 929 lines containing all CLI commands

### Proposed Structure
```
cli/
├── __init__.py
├── base.py              # Shared CLI utilities and decorators
├── process_commands.py  # Document processing commands
├── memory_commands.py   # Memory graph operations
├── config_commands.py   # Configuration management
├── utility_commands.py  # Render, OCR, info commands
└── main.py             # Entry point with command registration
```

### Implementation Steps
1. Create `base.py` with shared utilities
2. Extract process-related commands to `process_commands.py`
3. Extract memory commands to `memory_commands.py`
4. Extract config commands to `config_commands.py`
5. Move utility commands to `utility_commands.py`
6. Create `main.py` to register all command groups

## 2. Processor Hierarchy Clarification

### Current Confusion
Multiple "Processor" classes with unclear boundaries:
- `DocumentProcessor` (in `intelligence/processor.py`)
- `DocumentProcessor` (in `core/pipeline.py`) 
- `MemoryProcessor`
- `TOCProcessor`
- `OCRProcessor`

### Proposed Architecture
```
processors/
├── base.py              # Abstract base processor
├── semantic.py          # Main semantic orchestrator (was DocumentProcessor)
├── content.py           # Text extraction processor
├── memory.py            # Graph building processor (was MemoryProcessor)
├── structure.py         # Document structure analyzer (was TOCProcessor)
└── ocr.py              # OCR processor (moved from extractors)
```

### Class Renaming
- `core.pipeline.DocumentProcessor` → `SemanticOrchestrator`
- `intelligence.processor.DocumentProcessor` → `ContentExtractor`
- `MemoryProcessor` → `GraphBuilder`
- `TOCProcessor` → `StructureAnalyzer`
- Keep `OCRProcessor` as is

## 3. Intelligence Backend Cleanup

### Current State
- Multiple backends with similar patterns
- Unclear hierarchy between backends

### Proposed Changes
1. Create clear base classes:
   - `BaseIntelligenceBackend` (abstract)
   - `DirectExtractionBackend` (for markitdown)
   - `AIEnhancedBackend` (for Ollama, LlamaCpp)
   - `ContextAwareBackend` (for memory-enhanced)

2. Standardize methods:
   - `extract_semantic_content()`
   - `enhance_with_context()`
   - `generate_relationships()`

## 4. Memory/Graph Module Organization

### Current State
- Memory functionality mixed with processing logic
- Adapter pattern not fully utilized

### Proposed Structure
```
memory/
├── __init__.py
├── adapter.py          # Database operations
├── builder.py          # Graph construction logic
├── query.py            # Search and traversal
├── relationships.py    # Relationship detection
└── schema.sql          # Database schema
```

## 5. Configuration Simplification

### Current Issues
- Complex configuration hierarchy
- Memory settings scattered

### Proposed Changes
1. Create `SemanticConfig` class for graph-related settings
2. Simplify backend configuration
3. Make memory/graph primary, not optional

## 6. Testing Reorganization

### Current State
- Many test files at root level
- No clear test structure

### Proposed Structure
```
tests/
├── unit/
│   ├── test_processors/
│   ├── test_memory/
│   └── test_backends/
├── integration/
│   ├── test_pipeline/
│   └── test_cli/
└── fixtures/
    ├── sample_pdfs/
    └── test_graphs/
```

## Implementation Priority

1. **Phase 1: Documentation** (Completed)
   - Update README.md ✓
   - Update architecture.md ✓
   - Update CLAUDE.md ✓

2. **Phase 2: Cleanup** (Completed)
   - Remove test outputs ✓
   - Remove legacy code ✓

3. **Phase 3: CLI Refactoring** (Next)
   - Break up commands.py
   - Create modular command structure

4. **Phase 4: Processor Clarification**
   - Rename and reorganize processors
   - Create clear hierarchy

5. **Phase 5: Backend Consolidation**
   - Standardize intelligence backends
   - Improve inheritance structure

6. **Phase 6: Memory Module**
   - Separate concerns
   - Enhance graph operations

7. **Phase 7: Testing**
   - Reorganize test structure
   - Add semantic-focused tests

## Success Criteria

1. No file exceeds 500 lines
2. Clear separation of concerns
3. Semantic processing is primary focus
4. Memory graph is central, not peripheral
5. Each class has single responsibility
6. Tests validate semantic understanding

## Notes

- Maintain backward compatibility where possible
- Update imports gradually
- Add deprecation warnings for moved code
- Document changes in CHANGELOG.md