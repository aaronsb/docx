"""Enhanced semantic orchestrator for full pipeline coordination."""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import concurrent.futures
from datetime import datetime

from ..processors.structure_analyzer import StructureAnalyzer, TOCStructure
from ..processors.content_analyzer import ContentAnalyzer
from ..processors.semantic_enhancer import SemanticEnhancer
from ..memory.graph_builder import GraphBuilder, NodeType, EdgeType
from ..intelligence.base import IntelligenceBackend
from ..core.document import Document
from ..core.exceptions import ProcessingError
from ..utils.progress import ProgressReporter


@dataclass
class ProcessingConfig:
    """Configuration for semantic processing pipeline."""
    enable_llm: bool = True
    max_pages: Optional[int] = None
    parallel_pages: int = 4
    context_window: int = 4096
    confidence_threshold: float = 0.7
    enable_ocr_fallback: bool = True
    save_intermediate: bool = False
    output_format: str = "json"  # json, sqlite, both


@dataclass
class PageData:
    """Data for a single page."""
    number: int
    text: str
    image_path: Optional[str] = None
    metadata: Dict[str, Any] = None


class SemanticOrchestrator:
    """Enhanced orchestrator for the semantic extraction pipeline."""
    
    def __init__(self, 
                 backend: Optional[IntelligenceBackend] = None,
                 config: Optional[ProcessingConfig] = None,
                 logger: Optional[logging.Logger] = None):
        """Initialize the semantic orchestrator.
        
        Args:
            backend: Intelligence backend for LLM processing
            config: Processing configuration
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.config = config or ProcessingConfig()
        self.backend = backend
        
        # Initialize components
        self.structure_analyzer = StructureAnalyzer(logger=self.logger)
        self.content_analyzer = ContentAnalyzer(logger=self.logger)
        self.graph_builder = GraphBuilder(logger=self.logger)
        
        # Initialize semantic enhancer if LLM is enabled
        self.semantic_enhancer = None
        if self.config.enable_llm and self.backend:
            self.semantic_enhancer = SemanticEnhancer(
                backend=self.backend,
                logger=self.logger
            )
        
        # Progress tracking
        self.progress_reporter = ProgressReporter()
        
    def process_document(self, 
                        document_path: Union[str, Path],
                        output_dir: Union[str, Path]) -> Dict[str, Any]:
        """Process a complete document through the semantic pipeline.
        
        Args:
            document_path: Path to the document
            output_dir: Directory for output files
            
        Returns:
            Processing results including graph data
        """
        start_time = datetime.now()
        document_path = Path(document_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            self.logger.info(f"Starting semantic processing of {document_path}")
            
            # Phase 1: Structure Discovery
            self.progress_reporter.update("Analyzing document structure...")
            toc = self.structure_analyzer.extract_or_construct_toc(str(document_path))
            
            # Phase 2: Extract pages
            self.progress_reporter.update("Extracting page content...")
            pages = self._extract_pages(document_path)
            
            # Phase 3: Initial Analysis
            self.progress_reporter.update("Performing initial content analysis...")
            initial_analysis = self._perform_initial_analysis(pages, toc)
            
            # Phase 4: Semantic Enhancement (if enabled)
            if self.config.enable_llm and self.semantic_enhancer:
                self.progress_reporter.update("Enhancing with semantic understanding...")
                self._perform_semantic_enhancement(pages, toc)
            
            # Phase 5: Generate output
            self.progress_reporter.update("Generating final output...")
            results = self._generate_output(output_dir, document_path.stem)
            
            # Add processing metadata
            end_time = datetime.now()
            results["metadata"] = {
                "processing_time": (end_time - start_time).total_seconds(),
                "document": str(document_path),
                "pages_processed": len(pages),
                "llm_enabled": self.config.enable_llm,
                "backend": self.backend.get_model_info() if self.backend else None
            }
            
            self.logger.info(f"Processing complete in {results['metadata']['processing_time']:.2f}s")
            return results
            
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            raise ProcessingError(f"Failed to process document: {e}")
    
    def _extract_pages(self, document_path: Path) -> List[PageData]:
        """Extract pages from document."""
        pages = []
        
        with Document(str(document_path)) as doc:
            total_pages = len(doc)
            max_pages = self.config.max_pages or total_pages
            
            for i in range(min(max_pages, total_pages)):
                self.progress_reporter.update(f"Extracting page {i+1}/{total_pages}")
                
                # Get page text
                page = doc[i]
                text = page.get_text()
                
                # Render page image if needed for LLM
                image_path = None
                if self.config.enable_llm and self.semantic_enhancer:
                    image_path = self._render_page_image(doc, i)
                
                pages.append(PageData(
                    number=i,
                    text=text,
                    image_path=image_path,
                    metadata={"page_number": i + 1}
                ))
        
        return pages
    
    def _perform_initial_analysis(self, pages: List[PageData], 
                                 toc: TOCStructure) -> Dict[str, Any]:
        """Perform initial lexical analysis."""
        all_stems = []
        all_relationships = []
        document_freq = {}
        
        for page in pages:
            # Analyze content
            analysis = self.content_analyzer.analyze_content(
                page.text,
                toc_context={"toc": toc, "document_freq": document_freq}
            )
            
            # Collect results
            all_stems.extend(analysis["word_stems"])
            all_relationships.extend(analysis["relationships"])
            
            # Update document frequency
            for stem in analysis["word_stems"]:
                document_freq[stem.stem] = document_freq.get(stem.stem, 0) + 1
            
            # Create initial nodes
            self._create_initial_nodes(page, analysis)
        
        document_freq["_total_docs"] = len(pages)
        
        return {
            "total_stems": len(all_stems),
            "unique_stems": len(set(s.stem for s in all_stems)),
            "relationships": len(all_relationships),
            "document_frequency": document_freq
        }
    
    def _create_initial_nodes(self, page: PageData, analysis: Dict[str, Any]):
        """Create initial graph nodes from analysis."""
        # Create page node
        page_node = self.graph_builder.create_node(
            content={
                "text": page.text,
                "page_number": page.number,
                "key_terms": [t.text for t in analysis.get("key_terms", [])]
            },
            node_type=NodeType.PAGE,
            confidence=0.8  # Initial confidence
        )
        
        # Create nodes for key concepts
        for term in analysis.get("key_terms", []):
            concept_node = self.graph_builder.create_node(
                content={"text": term.text, "significance": term.significance},
                node_type=NodeType.CONCEPT,
                ontology_tags=[term.stem],
                confidence=term.significance
            )
            
            # Link to page
            self.graph_builder.create_edge(
                source=page_node,
                target=concept_node,
                edge_type=EdgeType.CONTAINS,
                confidence=term.significance
            )
        
        # Create relationships
        for rel in analysis.get("relationships", []):
            # Create or find nodes
            source_node = self._find_or_create_concept_node(rel.source)
            target_node = self._find_or_create_concept_node(rel.target)
            
            # Create edge
            edge_type = self._map_relationship_type(rel.type)
            self.graph_builder.create_edge(
                source=source_node,
                target=target_node,
                edge_type=edge_type,
                confidence=rel.strength,
                evidence=rel.evidence
            )
    
    def _perform_semantic_enhancement(self, pages: List[PageData], 
                                     toc: TOCStructure):
        """Perform LLM-based semantic enhancement."""
        # Process pages in batches for efficiency
        batch_size = self.config.parallel_pages
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = []
            
            for i in range(0, len(pages), batch_size):
                batch = pages[i:i + batch_size]
                
                # Submit batch for processing
                for page in batch:
                    future = executor.submit(
                        self._enhance_single_page,
                        page, toc, i
                    )
                    futures.append(future)
                
                # Wait for batch to complete
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        self.logger.debug(f"Enhanced page {result['page_number']}")
                    except Exception as e:
                        self.logger.error(f"Enhancement failed: {e}")
    
    def _enhance_single_page(self, page: PageData, toc: TOCStructure, 
                           context_index: int) -> Dict[str, Any]:
        """Enhance a single page with semantic understanding."""
        # Get context from nearby pages
        previous_summaries = self._get_previous_summaries(context_index)
        
        # Prepare context
        context = self.semantic_enhancer.prepare_context(
            toc=toc,
            page_content=page.text,
            page_image_path=page.image_path,
            page_number=page.number,
            total_pages=len(self.graph_builder.nodes),
            previous_summaries=previous_summaries
        )
        
        # Generate semantic summary
        summary = self.semantic_enhancer.enhance_with_llm(context)
        
        # Find page node
        page_node = None
        for node in self.graph_builder.nodes.values():
            if (node.type == NodeType.PAGE and 
                node.content.get("page_number") == page.number):
                page_node = node
                break
        
        if page_node:
            # Update graph with semantic understanding
            self.semantic_enhancer.update_graph(
                self.graph_builder,
                summary,
                page_node,
                confidence=summary.confidence
            )
        
        return {
            "page_number": page.number,
            "summary": summary.to_dict()
        }
    
    def _generate_output(self, output_dir: Path, doc_name: str) -> Dict[str, Any]:
        """Generate final output files."""
        results = {}
        
        # Export graph as JSON
        if self.config.output_format in ["json", "both"]:
            graph_data = self.graph_builder.export_graph()
            json_path = output_dir / f"{doc_name}_graph.json"
            
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(graph_data, f, indent=2, ensure_ascii=False)
            
            results["json_path"] = str(json_path)
            results["graph_stats"] = graph_data["metadata"]
        
        # Export to SQLite (memory-graph format)
        if self.config.output_format in ["sqlite", "both"]:
            # TODO: Implement SQLite export compatible with memory-graph
            pass
        
        # Save intermediate results if enabled
        if self.config.save_intermediate:
            intermediate_dir = output_dir / "intermediate"
            intermediate_dir.mkdir(exist_ok=True)
            
            # Save TOC
            # Save initial analysis
            # Save summaries
        
        return results
    
    def _render_page_image(self, doc: Document, page_index: int) -> str:
        """Render page as image for multimodal processing."""
        # TODO: Implement page rendering
        # For now, return None
        return None
    
    def _find_or_create_concept_node(self, concept: str) -> 'Node':
        """Find existing concept node or create new one."""
        # Search existing nodes
        for node in self.graph_builder.nodes.values():
            if (node.type == NodeType.CONCEPT and 
                concept.lower() in node.content.get("text", "").lower()):
                return node
        
        # Create new node
        return self.graph_builder.create_node(
            content={"text": concept},
            node_type=NodeType.CONCEPT,
            confidence=0.7
        )
    
    def _map_relationship_type(self, rel_type: str) -> EdgeType:
        """Map text relationship to edge type."""
        mapping = {
            "type_of": EdgeType.PART_OF,
            "contains": EdgeType.CONTAINS,
            "part_of": EdgeType.PART_OF,
            "relates_to": EdgeType.RELATES_TO,
            "similar_to": EdgeType.SIMILAR_TO,
            "example_of": EdgeType.EXAMPLE_OF,
            "definition": EdgeType.DEFINES,
            "references": EdgeType.REFERENCES,
            "co_occurrence": EdgeType.RELATES_TO
        }
        
        return mapping.get(rel_type, EdgeType.RELATES_TO)
    
    def _get_previous_summaries(self, current_index: int) -> List[str]:
        """Get summaries from previous pages for context."""
        summaries = []
        
        # Get up to 3 previous summaries
        for i in range(max(0, current_index - 3), current_index):
            # Find page node
            for node in self.graph_builder.nodes.values():
                if (node.type == NodeType.PAGE and 
                    node.content.get("page_number") == i):
                    summary = node.content.get("semantic_summary")
                    if summary:
                        summaries.append(summary)
                    break
        
        return summaries