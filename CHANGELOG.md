# Changelog

All notable changes to DocX will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-05-19

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