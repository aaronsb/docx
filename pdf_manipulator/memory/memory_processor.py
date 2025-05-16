"""Memory processor for storing PDF content in knowledge graph."""
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import json
import hashlib

from ..core.document import PDFDocument
from ..intelligence.processor import DocumentProcessor as IntelligenceProcessor
from .memory_adapter import MemoryAdapter, MemoryConfig


class MemoryProcessor:
    """Process PDF documents and store extracted content as memories."""
    
    def __init__(
        self,
        memory_config: MemoryConfig,
        intelligence_processor: Optional[IntelligenceProcessor] = None
    ):
        """Initialize the memory processor.
        
        Args:
            memory_config: Configuration for memory storage
            intelligence_processor: Optional AI processor for generating summaries
        """
        self.memory_config = memory_config
        self.intelligence = intelligence_processor
        self.adapter = MemoryAdapter(memory_config)
        self.document_memories: Dict[str, str] = {}  # Track memory IDs for relationships
        
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
        document_metadata: Optional[Dict[str, Any]] = None
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
            'metadata': document_metadata or {}
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
        
        # Create document-level memory
        doc_content = self._create_document_summary(page_content, doc_metadata)
        doc_memory_id = self.adapter.store_memory(
            content=doc_content,
            path=f"/documents/{Path(pdf_document.filename).stem}",
            tags=['document', 'root', pdf_document.filename],
            summary=self._generate_summary(doc_content) if self.intelligence else None,
            metadata=doc_metadata
        )
        results['document_id'] = doc_memory_id
        
        # Process each page
        for page_num, content in page_content.items():
            if not content.strip():
                continue
                
            # Store page memory
            page_path = f"/documents/{Path(pdf_document.filename).stem}/pages/{page_num}"
            page_tags = ['page', f'page:{page_num}', pdf_document.filename]
            
            page_memory_id = self.adapter.store_memory(
                content=content,
                path=page_path,
                tags=page_tags,
                summary=self._generate_summary(content) if self.intelligence else None,
                metadata={'page_number': page_num, 'document': pdf_document.filename}
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
        sections = self._extract_sections(page_content)
        for section in sections:
            section_content = section['content']
            section_path = f"/documents/{Path(pdf_document.filename).stem}/sections/{section['id']}"
            section_tags = ['section', f"section:{section['level']}", section['title']]
            
            section_memory_id = self.adapter.store_memory(
                content=section_content,
                path=section_path,
                tags=section_tags,
                summary=self._generate_summary(section_content) if self.intelligence else None,
                metadata={
                    'title': section['title'],
                    'level': section['level'],
                    'pages': section['pages']
                }
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