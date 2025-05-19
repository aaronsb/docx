"""Memory processor for storing PDF content in knowledge graph."""
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import json
import hashlib
import logging

from ..core.document import PDFDocument
from ..intelligence.processor import DocumentProcessor as IntelligenceProcessor
from .memory_adapter import MemoryAdapter, MemoryConfig
from .toc_processor import TOCProcessor, TOCStructure, TOCEntry


class MemoryProcessor:
    """Process PDF documents and store extracted content as memories."""
    
    def __init__(
        self,
        memory_config: MemoryConfig,
        intelligence_processor: Optional[IntelligenceProcessor] = None,
        use_toc_first: bool = True,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the memory processor.
        
        Args:
            memory_config: Configuration for memory storage
            intelligence_processor: Optional AI processor for generating summaries
            use_toc_first: Whether to use TOC as primary structure (default: True)
            logger: Optional logger instance
        """
        self.memory_config = memory_config
        self.intelligence = intelligence_processor
        self.adapter = MemoryAdapter(memory_config)
        self.document_memories: Dict[str, str] = {}  # Track memory IDs for relationships
        self.use_toc_first = use_toc_first
        self.logger = logger or logging.getLogger(__name__)
        self.toc_processor = TOCProcessor(logger=self.logger)
        
    def __enter__(self):
        """Context manager entry."""
        self.adapter.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.adapter.disconnect()
        
    def process_document(
        self,
        pdf_document: PDFDocument,
        page_content: Dict[int, str],
        document_metadata: Optional[Dict[str, Any]] = None,
        semantic_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a PDF document and store content as memories.
        
        Args:
            pdf_document: The PDF document object
            page_content: Dictionary mapping page numbers to extracted text
            document_metadata: Optional metadata about the document
            
        Returns:
            Dictionary with processing results and memory IDs
        """
        results = {
            'document_id': None,
            'page_memories': {},
            'section_memories': {},
            'relationships': [],
            'metadata': document_metadata or {},
            'toc_structure': None,
            'structure_method': 'pattern-based'  # Default
        }
        
        # Extract document metadata
        pdf_info = pdf_document.get_info()
        doc_metadata = {
            'filename': pdf_document.filename,
            'pages': pdf_document.num_pages,
            'title': pdf_info.get('Title', Path(pdf_document.filename).stem),
            'author': pdf_info.get('Author'),
            'subject': pdf_info.get('Subject'),
            'creation_date': pdf_info.get('CreationDate'),
            **(document_metadata or {})
        }
        
        # Try to detect and use TOC structure first
        toc_structure = None
        if self.use_toc_first:
            self.logger.info("Attempting to detect table of contents...")
            toc_result = self.toc_processor.detect_toc(page_content)
            
            if toc_result:
                toc_pages, toc_content = toc_result
                self.logger.info(f"TOC detected on pages: {toc_pages}")
                
                # Parse TOC structure
                toc_structure = self.toc_processor.parse_toc(toc_content, toc_pages)
                if toc_structure:
                    results['toc_structure'] = toc_structure
                    results['structure_method'] = 'toc-based'
                    self.logger.info(f"Successfully parsed TOC with {len(toc_structure.entries)} entries")
        
        # Create document-level memory
        doc_content = self._create_document_summary(page_content, doc_metadata)
        doc_memory_id = self.adapter.store_memory(
            content=doc_content,
            path=f"/documents/{Path(pdf_document.filename).stem}",
            tags=['document', 'root', pdf_document.filename],
            summary=self._generate_summary(doc_content) if self.intelligence else None,
            # Don't pass metadata as it gets prepended to content, contaminating the graph
            metadata=None
        )
        results['document_id'] = doc_memory_id
        
        # Process each page
        for page_num, content in page_content.items():
            if not content.strip():
                continue
                
            # Store page memory
            page_path = f"/documents/{Path(pdf_document.filename).stem}/pages/{page_num}"
            page_tags = ['page', f'page:{page_num}', pdf_document.filename]
            
            # Use semantic analysis if available
            if semantic_analysis and page_num in semantic_analysis:
                semantic_data = semantic_analysis[page_num]
                self.logger.info(f"Using semantic analysis for page {page_num}")
                
                # Extract semantic summary
                semantic_summary = None
                if "semantic_enhancement" in semantic_data:
                    enhancement = semantic_data["semantic_enhancement"]
                    semantic_summary = enhancement.get("semantic_summary", "")
                    self.logger.info(f"Found semantic summary: '{semantic_summary[:100]}...'")
                    
                    # Add key insights to tags
                    key_insights = enhancement.get("key_insights", [])
                    for insight in key_insights[:3]:  # Limit to top 3 insights
                        page_tags.append(f"insight:{insight}")
                    
                    # Add ontology tags if available
                    if "metadata" in enhancement and "ontology_tags" in enhancement["metadata"]:
                        ontology_tags = enhancement["metadata"]["ontology_tags"]
                        if isinstance(ontology_tags, list):
                            for tag in ontology_tags[:5]:  # Limit to top 5 ontology tags
                                page_tags.append(f"ontology:{tag}")
                
                # Create a rich semantic content including both summary and markitdown text
                if semantic_summary:
                    memory_content = f"# Semantic Summary\n\n{semantic_summary}\n\n# Original Content\n\n{content[:2000]}"
                else:
                    memory_content = content
                
                page_memory_id = self.adapter.store_memory(
                    content=memory_content,
                    path=page_path,
                    tags=page_tags,
                    summary=self._generate_summary(memory_content) if self.intelligence else None,
                    # Page metadata is already encoded in tags and path
                    metadata=None
                )
            else:
                page_memory_id = self.adapter.store_memory(
                    content=content,
                    path=page_path,
                    tags=page_tags,
                    summary=self._generate_summary(content) if self.intelligence else None,
                    # Page metadata is already encoded in tags and path
                    metadata=None
                )
            
            if page_memory_id:
                results['page_memories'][page_num] = page_memory_id
                
                # Create relationship to document
                self.adapter.create_relationship(
                    source_id=page_memory_id,
                    target_id=doc_memory_id,
                    rel_type='part_of',
                    strength=1.0
                )
                
                # Create relationship to previous page
                if page_num > 0 and (page_num - 1) in results['page_memories']:
                    prev_page_id = results['page_memories'][page_num - 1]
                    self.adapter.create_relationship(
                        source_id=prev_page_id,
                        target_id=page_memory_id,
                        rel_type='precedes',
                        strength=1.0
                    )
        
        # Extract and process sections
        if toc_structure:
            # Use TOC-based structure
            sections = self._process_toc_sections(toc_structure, page_content)
        else:
            # Fallback to pattern-based extraction
            sections = self._extract_sections(page_content)
            
        for section in sections:
            section_content = section['content']
            section_path = f"/documents/{Path(pdf_document.filename).stem}/sections/{section['id']}"
            section_tags = ['section', f"section:{section['level']}", section['title']]
            
            # Use semantic analysis if available for section pages
            if semantic_analysis:
                # Collect semantic summaries from pages in this section
                semantic_summaries = []
                for page_num in section['pages']:
                    if page_num in semantic_analysis:
                        semantic_data = semantic_analysis[page_num]
                        if "semantic_enhancement" in semantic_data:
                            enhancement = semantic_data["semantic_enhancement"]
                            summary = enhancement.get("semantic_summary", "")
                            if summary:
                                semantic_summaries.append(summary)
                
                # If we have semantic summaries, use them as section content
                if semantic_summaries:
                    section_content = f"## {section['title']}\n\n" + "\n\n".join(semantic_summaries)
            
            section_memory_id = self.adapter.store_memory(
                content=section_content,
                path=section_path,
                tags=section_tags,
                summary=self._generate_summary(section_content) if self.intelligence else None,
                # Section metadata is already encoded in tags and content
                metadata=None
            )
            
            if section_memory_id:
                results['section_memories'][section['id']] = section_memory_id
                
                # Create relationship to document
                self.adapter.create_relationship(
                    source_id=section_memory_id,
                    target_id=doc_memory_id,
                    rel_type='part_of',
                    strength=0.9
                )
                
                # Create relationships to pages
                for page_num in section['pages']:
                    if page_num in results['page_memories']:
                        self.adapter.create_relationship(
                            source_id=section_memory_id,
                            target_id=results['page_memories'][page_num],
                            rel_type='contains',
                            strength=0.8
                        )
        
        return results
    
    def _create_document_summary(
        self,
        page_content: Dict[int, str],
        metadata: Dict[str, Any]
    ) -> str:
        """Create a summary content for the document level memory."""
        summary_parts = []
        
        # Add metadata summary
        summary_parts.append(f"Document: {metadata.get('title', 'Untitled')}")
        if metadata.get('author'):
            summary_parts.append(f"Author: {metadata['author']}")
        if metadata.get('subject'):
            summary_parts.append(f"Subject: {metadata['subject']}")
        summary_parts.append(f"Pages: {metadata['pages']}")
        summary_parts.append("")
        
        # Add first page excerpt
        if 0 in page_content and page_content[0]:
            excerpt = page_content[0][:500].strip()
            summary_parts.append("First page excerpt:")
            summary_parts.append(excerpt)
            if len(page_content[0]) > 500:
                summary_parts.append("...")
        
        return "\n".join(summary_parts)
    
    def _extract_sections(
        self,
        page_content: Dict[int, str]
    ) -> List[Dict[str, Any]]:
        """Extract sections from the document content.
        
        Returns a list of section dictionaries with:
        - id: Unique section ID
        - title: Section title
        - level: Section level (1-6)
        - content: Section content
        - pages: List of pages the section spans
        """
        sections = []
        
        # Common heading patterns
        heading_patterns = [
            (r'^#+\s+(.+)$', 'markdown'),  # Markdown headings
            (r'^(\d+\.)+\s+(.+)$', 'numbered'),  # Numbered sections
            (r'^(?:CHAPTER|Chapter|Section|SECTION)\s+\d+[:.]?\s*(.+)$', 'formal'),
            (r'^[A-Z][A-Z\s]+$', 'allcaps'),  # All caps headings
        ]
        
        current_section = None
        all_content = []
        
        # Combine all pages into one text for section extraction
        for page_num in sorted(page_content.keys()):
            content = page_content[page_num]
            all_content.append((page_num, content))
        
        # Extract sections
        for page_num, content in all_content:
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Check if line is a heading
                is_heading = False
                heading_text = line
                heading_level = 1
                
                for pattern, pattern_type in heading_patterns:
                    match = re.match(pattern, line)
                    if match:
                        is_heading = True
                        if pattern_type == 'markdown':
                            heading_level = line.count('#')
                            heading_text = match.group(1)
                        elif pattern_type == 'numbered':
                            heading_level = match.group(1).count('.')
                            heading_text = match.group(2)
                        else:
                            heading_text = match.group(1) if match.groups() else line
                        break
                
                if is_heading:
                    # Save previous section
                    if current_section and current_section['content']:
                        sections.append(current_section)
                    
                    # Create new section
                    section_id = hashlib.md5(f"{heading_text}-{page_num}".encode()).hexdigest()[:8]
                    current_section = {
                        'id': section_id,
                        'title': heading_text,
                        'level': heading_level,
                        'content': heading_text + '\n',
                        'pages': [page_num]
                    }
                elif current_section:
                    # Add content to current section
                    current_section['content'] += line + '\n'
                    if page_num not in current_section['pages']:
                        current_section['pages'].append(page_num)
        
        # Save last section
        if current_section and current_section['content']:
            sections.append(current_section)
        
        return sections
    
    def _process_toc_sections(
        self, 
        toc_structure: TOCStructure, 
        page_content: Dict[int, str]
    ) -> List[Dict[str, Any]]:
        """Process sections based on TOC structure.
        
        Args:
            toc_structure: Parsed TOC structure
            page_content: Dictionary mapping page numbers to extracted text
            
        Returns:
            List of section dictionaries with TOC-based structure
        """
        sections = []
        flat_entries = toc_structure.get_flat_entries()
        
        # Create blueprint for mapping
        blueprint = self.toc_processor.create_blueprint(toc_structure, page_content)
        
        # Process each TOC entry
        for i, entry in enumerate(flat_entries):
            # Determine content range
            start_page = entry.page
            
            # Find next entry's page to determine end
            end_page = max(page_content.keys())  # Default to last page
            if i + 1 < len(flat_entries):
                end_page = flat_entries[i + 1].page - 1
            
            # Collect content from pages
            section_content = []
            pages_in_section = []
            
            for page_num in range(start_page, end_page + 1):
                if page_num in page_content:
                    content = page_content[page_num]
                    if content.strip():
                        section_content.append(content)
                        pages_in_section.append(page_num)
            
            if section_content:
                # Create section ID using TOC entry number or title
                section_id = entry.number.replace('.', '_') if entry.number else \
                            hashlib.md5(entry.title.encode()).hexdigest()[:8]
                
                sections.append({
                    'id': section_id,
                    'title': entry.title,
                    'level': entry.level,
                    'content': '\n\n'.join(section_content),
                    'pages': pages_in_section,
                    'toc_entry': entry,  # Keep reference to TOC entry
                    'path': entry.get_full_path()
                })
                
                self.logger.debug(f"Processed TOC section: {entry.title} (pages {start_page}-{end_page})")
        
        # Handle orphan pages not in TOC
        orphan_pages = blueprint.get('orphan_pages', [])
        if orphan_pages:
            self.logger.info(f"Found {len(orphan_pages)} orphan pages not in TOC")
            
            # Try pattern-based extraction for orphan pages
            orphan_content = {page: page_content[page] for page in orphan_pages 
                            if page in page_content}
            
            if orphan_content:
                orphan_sections = self._extract_sections(orphan_content)
                sections.extend(orphan_sections)
        
        return sections
    
    def _generate_summary(self, content: str, max_length: int = 500) -> Optional[str]:
        """Generate a summary of the content using AI if available."""
        if not self.intelligence:
            # Simple extractive summary
            sentences = re.split(r'[.!?]\s+', content)
            if sentences:
                return sentences[0][:max_length]
            return content[:max_length]
        
        # Use AI for summarization
        prompt = f"""Summarize this content in 1-2 sentences, capturing the key information:

{content[:2000]}"""
        
        try:
            summary = self.intelligence.process(prompt, max_tokens=100)
            return summary.strip()
        except Exception:
            # Fallback to simple summary
            return content[:max_length]
    
    def link_related_documents(
        self,
        doc1_id: str,
        doc2_id: str,
        relationship_type: str = "related_to",
        strength: float = 0.7
    ) -> None:
        """Create a relationship between two documents."""
        self.adapter.create_relationship(
            source_id=doc1_id,
            target_id=doc2_id,
            rel_type=relationship_type,
            strength=strength
        )
    
    def find_similar_documents(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find documents similar to the query."""
        return self.adapter.search_memories(
            query=query,
            limit=limit
        )
    
    def get_document_graph(
        self,
        document_id: str,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """Get the knowledge graph for a document.
        
        Returns a graph structure with the document and its related memories.
        """
        if not self.adapter.conn:
            raise RuntimeError("Not connected to database")
        
        graph = {
            'nodes': {},
            'edges': []
        }
        
        # Recursive function to traverse the graph
        def traverse(node_id: str, depth: int = 0):
            if depth > max_depth or node_id in graph['nodes']:
                return
            
            # Get node data
            cursor = self.adapter.conn.execute(
                """SELECT m.*, GROUP_CONCAT(mt.tag) as tags
                   FROM MEMORY_NODES m
                   LEFT JOIN MEMORY_TAGS mt ON m.id = mt.nodeId
                   WHERE m.id = ?
                   GROUP BY m.id""",
                (node_id,)
            )
            row = cursor.fetchone()
            
            if row:
                graph['nodes'][node_id] = {
                    'id': row[0],
                    'content': row[2][:200] + '...' if len(row[2]) > 200 else row[2],
                    'path': row[4],
                    'summary': row[5],
                    'tags': row[7].split(',') if row[7] else []
                }
                
                # Get edges
                cursor = self.adapter.conn.execute(
                    """SELECT target, type, strength
                       FROM MEMORY_EDGES
                       WHERE source = ?""",
                    (node_id,)
                )
                
                for edge_row in cursor:
                    target_id, rel_type, strength = edge_row
                    graph['edges'].append({
                        'source': node_id,
                        'target': target_id,
                        'type': rel_type,
                        'strength': strength
                    })
                    
                    # Traverse to connected nodes
                    traverse(target_id, depth + 1)
        
        traverse(document_id)
        return graph