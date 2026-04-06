import concurrent.futures
from typing import List, Callable, Dict
import multiprocessing as mp
import logging
from app.services.rate_limit_controller import AdaptiveRateLimiter
from app.services.document_chunker import DocumentChunk

logger = logging.getLogger(__name__)

class DistributedDocumentProcessor:
    """Process document chunks in parallel across multiple workers"""
    
    def __init__(self, max_workers=None):
        self.max_workers = max_workers or max(1, mp.cpu_count() - 1)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        self.rate_limiter = AdaptiveRateLimiter()
        
    def process_document_parallel(self, chunks: List[DocumentChunk], 
                                  process_func: Callable) -> List[Dict]:
        """Process chunks in parallel with rate limiting"""
        futures = []
        
        # Submit all chunks for processing
        for chunk in chunks:
            future = self.executor.submit(
                self._process_with_rate_limit,
                process_func,
                chunk
            )
            futures.append(future)
        
        # Collect results as they complete
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result(timeout=300)  # 5 minute timeout
                results.append(result)
            except Exception as e:
                logger.error(f"Chunk processing failed: {e}")
                results.append({'error': str(e)})
        
        return results
    
    def _process_with_rate_limit(self, process_func: Callable, chunk: DocumentChunk):
        """Process with rate limiting"""
        self.rate_limiter.before_request()
        
        try:
            result = process_func(chunk)
            self.rate_limiter.after_request(success=True)
            return result
        except Exception as e:
            self.rate_limiter.after_request(success=False)
            raise e
    
    def process_streaming(self, chunk_generator, process_func: Callable):
        """Process chunks in streaming fashion for memory efficiency"""
        results = []
        
        for chunk in chunk_generator:
            self.rate_limiter.before_request()
            
            try:
                result = process_func(chunk)
                self.rate_limiter.after_request(success=True)
                results.append(result)
                yield result
            except Exception as e:
                self.rate_limiter.after_request(success=False)
                logger.error(f"Streaming processing failed: {e}")
                yield {'error': str(e), 'chunk_id': chunk.chunk_id if hasattr(chunk, 'chunk_id') else ''}
        
        return results
