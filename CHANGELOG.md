# Changelog

All notable changes to Memory Graph Extract (formerly DocX) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-05-19

### Changed
- Renamed project from "DocX" to "Memory Graph Extract (MGE)"
- Enhanced semantic orchestration with clearer component boundaries
- Improved intelligence backend interface for multimodal support
- Standardized memory graph format for compatibility with memory-graph-mcp

### Added
- Advanced knowledge graph construction with ontological tagging
- Edge scoring with confidence and recency factors
- Environmental variable support via .env files
- Comprehensive semantic pipeline configuration
- Semantic processor with multi-step analysis flow

### Fixed
- Graph relationship detection algorithm
- Memory domain handling for cross-document connections
- Multimodal model error handling and fallbacks
- Configuration loading with environment variable substitution

### Documentation
- Added semantic pipeline documentation suite
- Created implementation guide for memory graph integration
- Updated architecture diagrams for semantic orchestration
- Added quickstart guide for semantic pipeline

## [0.2.0] - 2025-05-10

### Changed
- **Major Refactoring**: Restructured entire codebase to focus on semantic knowledge graph extraction
- Renamed project from "PDF Extractor" to "DocX - Semantic Graph PDF Extractor"
- Broke up monolithic `cli/commands.py` (929 lines) into modular command files
- Clarified processor hierarchy with semantic naming:
  - `SemanticOrchestrator` (was DocumentProcessor in pipeline)
  - `ContentExtractor` (was DocumentProcessor in intelligence)
  - `GraphBuilder` (was MemoryProcessor)
  - `StructureAnalyzer` (was TOCProcessor)

### Added
- Comprehensive documentation focusing on semantic understanding
- Base processor classes establishing clear hierarchy
- Modular CLI structure with separate command files
- Semantic aliases for better code clarity
- Memory graph as central feature (not optional)

### Removed
- Legacy `extractors/ai_transcription.py` file
- Outdated scripts (`docaitool_wrapper.sh`, `setup_config.sh`)
- Large test output directories
- Redundant code and unused imports

### Fixed
- CLI argument passing for document processing
- Memory graph creation in processing pipeline
- Import structure for modular CLI

### Documentation
- Updated README.md to emphasize semantic graph extraction
- Revised architecture.md to show memory graph as central component
- Updated CLAUDE.md with semantic-focused development guidelines
- Created REFACTORING_PLAN.md and REFACTORING_PROGRESS.md

## [0.1.0] - 2024-12-01

### Added
- Initial release with basic PDF processing capabilities
- Multiple AI backend support (markitdown, Ollama, llama.cpp)
- OCR fallback functionality
- Basic memory storage features