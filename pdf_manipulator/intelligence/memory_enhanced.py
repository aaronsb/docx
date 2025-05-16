"""Memory-enhanced intelligence backend that queries knowledge graph for context."""
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from .base import IntelligenceBackend
from ..memory.memory_adapter import MemoryAdapter, MemoryConfig


class MemoryEnhancedBackend(IntelligenceBackend):
    """Intelligence backend that uses memory graph for enhanced context."""
    
    def __init__(
        self,
        base_backend: IntelligenceBackend,
        memory_config: MemoryConfig,
        max_context_memories: int = 5,
        enable_memory_queries: bool = True
    ):
        """Initialize memory-enhanced backend.
        
        Args:
            base_backend: The underlying intelligence backend to enhance
            memory_config: Configuration for memory adapter
            max_context_memories: Maximum number of memories to include in context
            enable_memory_queries: Whether to query memory graph for context
        """
        self.base_backend = base_backend
        self.memory_adapter = MemoryAdapter(memory_config)
        self.max_context_memories = max_context_memories
        self.enable_memory_queries = enable_memory_queries
        self.connected = False
    
    def initialize(self) -> None:
        """Initialize both the base backend and memory connection."""
        self.base_backend.initialize()
        self.memory_adapter.connect()
        self.connected = True
    
    def transcribe_image(
        self,
        image_path: str,
        prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Transcribe an image with enhanced context from memory graph.
        
        Args:
            image_path: Path to the image
            prompt: Optional custom prompt
            context: Optional context dictionary
            
        Returns:
            Transcribed text
        """
        if not self.connected:
            self.initialize()
        
        # Enhance prompt with memory context if enabled
        enhanced_prompt = prompt
        if self.enable_memory_queries and prompt:
            memory_context = self._get_memory_context(prompt, context)
            if memory_context:
                enhanced_prompt = self._enhance_prompt_with_memory(prompt, memory_context)
        
        # Use the base backend with enhanced prompt
        return self.base_backend.transcribe_image(
            image_path=image_path,
            prompt=enhanced_prompt,
            context=context
        )
    
    def process_text(
        self,
        text: str,
        instruction: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process text with enhanced context from memory graph.
        
        Args:
            text: Input text
            instruction: Processing instruction
            context: Optional context dictionary
            
        Returns:
            Processed text
        """
        if not self.connected:
            self.initialize()
        
        # Query memory for relevant context
        memory_context = []
        if self.enable_memory_queries:
            # Search memories for relevant content
            query = f"{instruction} {text[:200]}"  # Use instruction and text excerpt
            memory_context = self._get_memory_context(query, context)
        
        # Enhance instruction with memory context
        enhanced_instruction = instruction
        if memory_context:
            enhanced_instruction = self._enhance_prompt_with_memory(instruction, memory_context)
        
        # Process with base backend
        return self.base_backend.process_text(
            text=text,
            instruction=enhanced_instruction,
            context=context
        )
    
    def _get_memory_context(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get relevant memories for context.
        
        Args:
            query: Search query
            context: Optional context with hints
            
        Returns:
            List of relevant memories
        """
        memories = []
        
        # Search for relevant memories
        search_results = self.memory_adapter.search_memories(
            query=query,
            limit=self.max_context_memories
        )
        
        # If context has document ID, get related memories
        if context and 'document_id' in context:
            doc_memories = self._get_document_memories(
                context['document_id'],
                limit=self.max_context_memories // 2
            )
            memories.extend(doc_memories)
        
        # If context has tags, search by tags
        if context and 'tags' in context:
            for tag in context['tags'][:3]:  # Limit tag searches
                tag_memories = self._get_memories_by_tag(
                    tag,
                    limit=self.max_context_memories // 3
                )
                memories.extend(tag_memories)
        
        # Combine and deduplicate
        seen_ids = set()
        unique_memories = []
        for memory in search_results + memories:
            if memory['id'] not in seen_ids:
                seen_ids.add(memory['id'])
                unique_memories.append(memory)
        
        # Sort by relevance/timestamp and limit
        unique_memories.sort(key=lambda m: m.get('timestamp', ''), reverse=True)
        return unique_memories[:self.max_context_memories]
    
    def _enhance_prompt_with_memory(
        self,
        original_prompt: str,
        memories: List[Dict[str, Any]]
    ) -> str:
        """Enhance a prompt with memory context.
        
        Args:
            original_prompt: The original prompt
            memories: List of relevant memories
            
        Returns:
            Enhanced prompt with memory context
        """
        if not memories:
            return original_prompt
        
        # Build context section
        context_lines = ["### Relevant Context from Knowledge Graph:"]
        
        for i, memory in enumerate(memories):
            # Extract key information
            content = memory.get('content', '')
            summary = memory.get('content_summary', '')
            tags = memory.get('tags', [])
            path = memory.get('path', '')
            
            # Clean content for context
            if summary:
                content_text = summary
            else:
                content_text = content[:200] + "..." if len(content) > 200 else content
            
            # Format memory context
            context_lines.append(f"\n**Context {i+1}** ({path}):")
            if tags:
                context_lines.append(f"Tags: {', '.join(tags)}")
            context_lines.append(content_text)
        
        # Combine with original prompt
        enhanced_prompt = f"""{original_prompt}

{chr(10).join(context_lines)}

### Task:
Based on the above context, {original_prompt}"""
        
        return enhanced_prompt
    
    def _get_document_memories(
        self,
        document_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get memories related to a specific document."""
        if not self.memory_adapter.conn:
            return []
        
        cursor = self.memory_adapter.conn.execute(
            """SELECT m.*, GROUP_CONCAT(mt.tag) as tags
               FROM MEMORY_NODES m
               LEFT JOIN MEMORY_TAGS mt ON m.id = mt.nodeId
               JOIN MEMORY_EDGES e ON (e.source = ? OR e.target = ?)
               WHERE (e.source = m.id OR e.target = m.id)
               GROUP BY m.id
               ORDER BY m.timestamp DESC
               LIMIT ?""",
            (document_id, document_id, limit)
        )
        
        memories = []
        for row in cursor:
            memory = {
                'id': row[0],
                'content': row[2],
                'timestamp': row[3],
                'path': row[4],
                'content_summary': row[5],
                'tags': row[7].split(',') if row[7] else []
            }
            memories.append(memory)
        
        return memories
    
    def _get_memories_by_tag(
        self,
        tag: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get memories with a specific tag."""
        if not self.memory_adapter.conn:
            return []
        
        cursor = self.memory_adapter.conn.execute(
            """SELECT m.*, GROUP_CONCAT(mt.tag) as tags
               FROM MEMORY_NODES m
               JOIN MEMORY_TAGS t ON t.nodeId = m.id
               LEFT JOIN MEMORY_TAGS mt ON m.id = mt.nodeId
               WHERE t.tag = ?
               GROUP BY m.id
               ORDER BY m.timestamp DESC
               LIMIT ?""",
            (tag, limit)
        )
        
        memories = []
        for row in cursor:
            memory = {
                'id': row[0],
                'content': row[2],
                'timestamp': row[3],
                'path': row[4],
                'content_summary': row[5],
                'tags': row[7].split(',') if row[7] else []
            }
            memories.append(memory)
        
        return memories
    
    def store_result_as_memory(
        self,
        content: str,
        prompt: str,
        result: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store an AI processing result as a memory for future reference.
        
        Args:
            content: Original content that was processed
            prompt: The prompt that was used
            result: The AI-generated result
            metadata: Optional metadata
            
        Returns:
            Memory ID of the stored result
        """
        if not self.connected:
            self.initialize()
        
        # Create memory content
        memory_content = f"""AI Processing Result:

Original Content:
{content[:500]}{'...' if len(content) > 500 else ''}

Prompt:
{prompt}

Result:
{result}"""
        
        # Prepare metadata
        full_metadata = {
            'type': 'ai_result',
            'prompt': prompt,
            'content_length': len(content),
            'result_length': len(result),
            **(metadata or {})
        }
        
        # Store as memory
        return self.memory_adapter.store_memory(
            content=memory_content,
            path="/ai_results",
            tags=['ai_result', 'processed'],
            summary=result[:200] if len(result) > 200 else result,
            metadata=full_metadata
        )
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.connected:
            self.memory_adapter.disconnect()
            self.connected = False
        self.base_backend.cleanup()
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()