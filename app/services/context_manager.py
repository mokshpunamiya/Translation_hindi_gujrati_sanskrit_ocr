from collections import deque
from typing import List, Dict, Optional
from app.services.document_chunker import DocumentChunk

class ContextWindowManager:
    """Manages context window for large documents with summarization"""
    
    def __init__(self, max_tokens=8000, compression_ratio=0.3):
        self.max_tokens = max_tokens
        self.compression_ratio = compression_ratio
        self.context_buffer = deque(maxlen=10)  # Keep last 10 chunks
        self.summarizer = self._init_summarizer()
        
    def _init_summarizer(self):
        """Initialize summarization model (lightweight)"""
        try:
            # Using a small summarization model
            from transformers import pipeline
            return pipeline("summarization", model="facebook/bart-large-cnn", device=-1)  # CPU
        except Exception:
            return None
    
    def add_to_context(self, chunk: DocumentChunk) -> str:
        """Add chunk to context, compress if needed"""
        current_context = self._get_current_context()
        
        # Check if adding this chunk exceeds token limit
        if self._estimate_tokens(current_context + chunk.text) > self.max_tokens:
            # Need to compress context
            compressed = self._compress_context(current_context)
            self.context_buffer.clear()
            self.context_buffer.append(compressed)
        
        self.context_buffer.append(chunk.text)
        return self._get_current_context()
    
    def _compress_context(self, context: str) -> str:
        """Compress context by summarizing oldest parts"""
        if not self.summarizer or len(context) < 1000:
            # Simple compression: take first 500 and last 500 chars
            if len(context) > 1000:
                return context[:500] + "\n...[COMPRESSED]...\n" + context[-500:]
            return context
        
        # Intelligent summarization
        try:
            summary = self.summarizer(context, 
                                     max_length=int(len(context) * self.compression_ratio),
                                     min_length=50,
                                     do_sample=False)
            return summary[0]['summary_text']
        except:
            return context[:500] + "\n...[COMPRESSED]...\n" + context[-500:]
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation"""
        return len(text) // 4  # Approximate: 4 chars per token
    
    def _get_current_context(self) -> str:
        """Get current context as string"""
        return '\n'.join(self.context_buffer)
    
    def get_context_for_page(self, page_num: int, chunks: List[DocumentChunk]) -> str:
        """Get relevant context for a specific page"""
        nearby_chunks = []
        for chunk in chunks:
            if abs(chunk.page_numbers[0] - page_num) < 5:  # Within 5 pages
                nearby_chunks.append(chunk)
        
        context = f"[CONTEXT FOR PAGE {page_num}]\n"
        for chunk in nearby_chunks[:3]:  # Limit to 3 nearby chunks
            metadata_heading = chunk.metadata.get('heading', 'Section') if chunk.metadata else 'Section'
            context += f"--- {metadata_heading} ---\n"
            context += chunk.text[:500] + "...\n\n"
        
        return context
