class LargeDocumentConfig:
    # Chunking
    CHUNK_SIZE = 2000  # tokens per chunk
    OVERLAP_SIZE = 200  # overlap between chunks
    
    # Processing
    BATCH_SIZE = 10  # pages per batch
    MAX_WORKERS = 3  # parallel workers
    
    # Rate Limiting (free tier safe)
    INITIAL_RATE = 5  # 5 requests per second
    MAX_RATE = 15     # max 15 requests per second
    BURST_CAPACITY = 20
    
    # Context Management
    MAX_CONTEXT_TOKENS = 8000
    COMPRESSION_RATIO = 0.3  # Compress to 30%
    
    # Fault Tolerance
    MAX_RETRIES = 3
    CHECKPOINT_INTERVAL = 10  # Save checkpoint every 10 pages
    JOB_TIMEOUT = 300  # 5 minutes per job
    
    # Quality
    MIN_CONTENT_LENGTH = 50  # Skip very short pages
    IMPORTANCE_THRESHOLD = 0.3  # Minimum importance to process
