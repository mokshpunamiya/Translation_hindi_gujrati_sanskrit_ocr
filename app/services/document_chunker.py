import hashlib
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class ContentType(Enum):
    TITLE = "title"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    LIST = "list"
    IMAGE_CAPTION = "caption"
    FOOTER = "footer"
    HEADER = "header"

@dataclass
class DocumentChunk:
    """Represents a processed chunk of document"""
    chunk_id: str
    page_numbers: List[int]
    content_type: ContentType
    text: str
    summary: Optional[str] = None
    importance_score: float = 0.0
    embedding: Optional[List[float]] = None
    metadata: Dict = None

class IntelligentDocumentChunker:
    """Smart chunking with context preservation"""
    
    def __init__(self, max_tokens_per_chunk=2000, overlap_tokens=200):
        self.max_tokens_per_chunk = max_tokens_per_chunk
        self.overlap_tokens = overlap_tokens
    
    def chunk_document(self, pages: List[Dict]) -> List[DocumentChunk]:
        """Chunk document intelligently. Accepts list of dicts with 'page_num' and 'text'."""
        chunks = []
        
        # Extract purely texts for structure detection
        page_texts = [p['text'] for p in pages]
        
        # Phase 1: Structure detection
        structure = self._detect_document_structure(page_texts)
        
        # Phase 2: Semantic segmentation
        semantic_units = self._semantic_segmentation(pages, structure)
        
        # Phase 3: Build hierarchical chunks
        for unit in semantic_units:
            chunks.extend(self._create_chunks_with_context(unit))
        
        # Phase 4: Score importance
        chunks = self._score_chunk_importance(chunks)
        
        return chunks
    
    def _detect_document_structure(self, pages: List[str]) -> Dict:
        """Detect headings, tables, lists, etc."""
        structure = {
            'headings': [],
            'tables': [],
            'paragraphs': []
        }
        
        for page_num, page_text in enumerate(pages):
            lines = page_text.split('\n')
            for line_num, line in enumerate(lines):
                if len(line) < 100 and not line.endswith(('.', '!', '?')) and len(line.strip()) > 0:
                    if line.isupper() or line[0].isupper():
                        structure['headings'].append({
                            'page': page_num,
                            'line': line_num,
                            'text': line,
                            'level': 1
                        })
                
                if '|' in line or (line.count('  ') > 3):
                    structure['tables'].append({
                        'page': page_num,
                        'line': line_num,
                        'text': line
                    })
        
        return structure
    
    def _semantic_segmentation(self, pages: List[Dict], structure: Dict) -> List[Dict]:
        """Segment document into semantic units (chapters/sections)"""
        segments = []
        
        # If no pages, return empty
        if not pages:
            return segments
            
        current_segment = {
            'start_page': pages[0]['page_num'],
            'heading': 'Introduction',
            'content': [],
            'type': 'section'
        }
        
        for idx, page_data in enumerate(pages):
            page_text = page_data['text']
            page_num_actual = page_data['page_num']
            
            # structure uses relative page index relative to the batch
            page_headings = [h for h in structure['headings'] if h['page'] == idx]
            
            if page_headings and len(current_segment['content']) > 0:
                segments.append(current_segment)
                current_segment = {
                    'start_page': page_num_actual,
                    'heading': page_headings[0]['text'],
                    'content': [page_text],
                    'type': 'section'
                }
            else:
                current_segment['content'].append(page_text)
        
        if current_segment['content']:
            segments.append(current_segment)
        
        return segments
    
    def _create_chunks_with_context(self, semantic_unit: Dict) -> List[DocumentChunk]:
        """Create chunks with overlapping context"""
        full_text = '\n'.join(semantic_unit['content'])
        words = full_text.split()
        
        chunks = []
        for i in range(0, len(words), max(1, self.max_tokens_per_chunk - self.overlap_tokens)):
            chunk_words = words[i:i + self.max_tokens_per_chunk]
            chunk_text = ' '.join(chunk_words)
            
            if i > 0:
                context_start = max(0, i - self.overlap_tokens)
                context_words = words[context_start:i]
                chunk_text = '[CONTEXT FROM PREVIOUS] ' + ' '.join(context_words[-100:]) + '\n' + chunk_text
            
            if i + self.max_tokens_per_chunk < len(words):
                next_words = words[i + self.max_tokens_per_chunk: i + self.max_tokens_per_chunk + self.overlap_tokens]
                chunk_text = chunk_text + '\n[CONTEXT FOR NEXT] ' + ' '.join(next_words)
            
            chunk = DocumentChunk(
                chunk_id=hashlib.md5(f"{semantic_unit['heading']}_{i}_{semantic_unit['start_page']}".encode()).hexdigest(),
                page_numbers=[semantic_unit['start_page']], 
                content_type=ContentType.PARAGRAPH,
                text=chunk_text,
                metadata={'heading': semantic_unit['heading'], 'position': i}
            )
            chunks.append(chunk)
        
        return chunks
    
    def _score_chunk_importance(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Score chunks by importance for priority processing"""
        for chunk in chunks:
            score = 0.0
            score += min(len(chunk.text) / 1000, 1.0) * 0.3
            
            if chunk.metadata and chunk.metadata.get('heading'):
                score += 0.2
            
            important_keywords = ['important', 'critical', 'must', 'required', 'conclusion', 'summary', 'result']
            for keyword in important_keywords:
                if keyword in chunk.text.lower():
                    score += 0.1
            
            if chunk.page_numbers[0] < 5:
                score += 0.2
            
            chunk.importance_score = min(score, 1.0)
        
        return sorted(chunks, key=lambda x: x.importance_score, reverse=True)
