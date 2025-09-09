"""
ADK Chunk Handler - Proper handling of ADK streaming chunks with partial flag

Based on ADK documentation:
- partial=True: Current output is incomplete, more coming for THIS chunk
- partial=False/None: Current chunk is complete (conversation may continue)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time


@dataclass
class ChunkData:
    """Data structure for tracking chunks"""
    index: int
    text: str
    is_partial: Optional[bool]
    timestamp: float
    chunk_id: Optional[str] = None


class ADKChunkHandler:
    """
    Handles ADK streaming chunks properly according to documentation.
    
    The partial flag indicates whether the CURRENT chunk is complete,
    not whether chunks should be appended or replaced.
    """
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset handler for new stream"""
        self.chunks: List[ChunkData] = []
        self.current_partial_buffer = ""
        self.completed_texts: List[str] = []
        self.chunk_index = 0
        
    async def process_stream(self, async_generator):
        """
        Process ADK async generator stream with proper partial flag handling
        
        Returns:
            str: The complete assembled text from all chunks
        """
        self.reset()
        
        async for chunk in async_generator:
            self.chunk_index += 1
            
            # Extract chunk data
            chunk_data = self._extract_chunk_data(chunk)
            
            if chunk_data:
                self._process_chunk(chunk_data)
                
                # Emit progress event if websocket is available
                self._emit_chunk_event(chunk_data)
        
        # Finalize any remaining partial buffer
        if self.current_partial_buffer:
            self.completed_texts.append(self.current_partial_buffer)
            self.current_partial_buffer = ""
        
        # Return all completed texts joined
        final_text = "".join(self.completed_texts)
        print(f"[ADK Handler] Final text assembled: {len(final_text)} chars from {len(self.completed_texts)} complete chunks")
        
        return final_text
    
    def _extract_chunk_data(self, chunk) -> Optional[ChunkData]:
        """Extract text and metadata from ADK chunk"""
        
        if not hasattr(chunk, 'content') or not hasattr(chunk.content, 'parts'):
            return None
        
        # Get partial flag from chunk
        is_partial = getattr(chunk, 'partial', None)
        
        # Extract text from parts
        for part in chunk.content.parts:
            if hasattr(part, 'text') and part.text is not None:
                import time as time_module
                return ChunkData(
                    index=self.chunk_index,
                    text=part.text,
                    is_partial=is_partial,
                    timestamp=time_module.time(),
                    chunk_id=getattr(chunk, 'id', None)
                )
        
        return None
    
    def _process_chunk(self, chunk_data: ChunkData):
        """
        Process a single chunk based on its partial flag
        
        According to ADK docs:
        - partial=True: This text is incomplete, more coming for THIS specific output
        - partial=False/None: This text chunk is complete
        """
        
        self.chunks.append(chunk_data)
        
        if chunk_data.is_partial is True:
            # This chunk is incomplete - accumulate in buffer
            self.current_partial_buffer += chunk_data.text
            print(f"[ADK Handler] Chunk {chunk_data.index}: Partial text received ({len(chunk_data.text)} chars), "
                  f"buffer now {len(self.current_partial_buffer)} chars")
            
        else:  # partial is False or None - chunk is complete
            if self.current_partial_buffer:
                # We were accumulating a partial chunk, now it's complete
                complete_text = self.current_partial_buffer + chunk_data.text
                self.completed_texts.append(complete_text)
                self.current_partial_buffer = ""
                print(f"[ADK Handler] Chunk {chunk_data.index}: Completed partial sequence "
                      f"({len(complete_text)} chars total)")
            else:
                # This is a standalone complete chunk
                self.completed_texts.append(chunk_data.text)
                print(f"[ADK Handler] Chunk {chunk_data.index}: Complete standalone text "
                      f"({len(chunk_data.text)} chars)")
    
    def _emit_chunk_event(self, chunk_data: ChunkData):
        """Emit websocket event for chunk progress"""
        try:
            from agents.nj_voter_chat_adk.agent import _emit_reasoning_event
            
            _emit_reasoning_event("adk_chunk_processed", {
                "index": chunk_data.index,
                "text_length": len(chunk_data.text),
                "is_partial": chunk_data.is_partial,
                "buffer_size": len(self.current_partial_buffer),
                "completed_chunks": len(self.completed_texts)
            })
        except:
            pass  # Silent fail if websocket not available
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics about chunk processing"""
        return {
            "total_chunks": len(self.chunks),
            "partial_chunks": sum(1 for c in self.chunks if c.is_partial is True),
            "complete_chunks": sum(1 for c in self.chunks if c.is_partial is not True),
            "completed_texts": len(self.completed_texts),
            "buffer_size": len(self.current_partial_buffer),
            "total_chars": sum(len(t) for t in self.completed_texts) + len(self.current_partial_buffer)
        }


# Backward compatibility function for existing code
async def consume_adk_stream(async_generator) -> str:
    """
    Consume an ADK async generator and return the complete text.
    
    This is a convenience function that maintains backward compatibility
    with the existing codebase while using the improved chunk handler.
    """
    handler = ADKChunkHandler()
    return await handler.process_stream(async_generator)