import os
import sys
import asyncio
import logging

# Set up logging to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Adjust python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Config
from app.services.production_pipeline import LargeDocumentPipeline

async def main():
    # Load API key and initialize pipeline
    api_key = Config.GEMINI_API_KEY
    if not api_key:
        print("Set GEMINI_API_KEY in .env first.")
        return

    # Use a small chunk size for testing so we can see multiple chunks easily
    pipeline = LargeDocumentPipeline(api_key=api_key, lang='hin') 
    
    # Override settings for a faster, smaller test
    pipeline.chunker.max_tokens_per_chunk = 200
    pipeline.chunker.overlap_tokens = 20
    
    pdf_path = os.path.join("raw_files", "jain_lagna_sanskar_020392_hr3.pdf")
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return
        
    print(f"Testing pipeline with: {pdf_path}")
    
    # We will only run on the first 2 pages to be quick
    # Monkey patch _stream_ocr_pages to limit to 2 pages
    original_stream = pipeline._stream_ocr_pages
    def limited_stream(pdf_path, start_page):
        gen = original_stream(pdf_path, start_page)
        count = 0
        for item in gen:
            yield item
            count += 1
            if count >= 2:  # Stop after 2 pages
                break
    pipeline._stream_ocr_pages = limited_stream

    result = await pipeline.process_large_document(pdf_path, "jain_lagna_sanskar_test")
    
    print("\n--- PIPELINE RESULT ---")
    print(f"Total Chunks: {result.get('total_chunks')}")
    print(f"Successful: {result.get('successful_chunks')}")
    print(f"Failed: {result.get('failed_chunks')}")
    print("\nSnippet of final document:")
    print(result.get('document')[:500] + "..." if result.get('document') else "None")

if __name__ == "__main__":
    asyncio.run(main())
