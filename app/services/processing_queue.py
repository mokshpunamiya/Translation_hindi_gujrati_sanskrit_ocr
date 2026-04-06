import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import threading
from queue import PriorityQueue

@dataclass
class ProcessingJob:
    job_id: str
    document_name: str
    page_range: tuple
    chunk_id: str
    priority: int  # Lower = higher priority
    status: str  # pending, processing, completed, failed
    created_at: datetime
    retry_count: int = 0
    error_message: str = None
    
    # Enable PriorityQueue sorting based on priority
    def __lt__(self, other):
        return self.priority < other.priority

class PersistentProcessingQueue:
    """SQLite-backed priority queue with checkpoint recovery"""
    
    def __init__(self, db_path="processing_queue.db"):
        self.db_path = db_path
        self._init_database()
        self.priority_queue = PriorityQueue()
        self._load_pending_jobs()
        
    def _init_database(self):
        """Initialize SQLite database"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_jobs (
                job_id TEXT PRIMARY KEY,
                document_name TEXT,
                page_start INTEGER,
                page_end INTEGER,
                chunk_id TEXT,
                priority INTEGER,
                status TEXT,
                created_at TIMESTAMP,
                retry_count INTEGER,
                error_message TEXT,
                last_updated TIMESTAMP
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_checkpoints (
                document_name TEXT PRIMARY KEY,
                last_processed_page INTEGER,
                total_pages INTEGER,
                completed_chunks TEXT,
                failed_chunks TEXT,
                last_updated TIMESTAMP
            )
        """)
        
        self.conn.commit()
    
    def _load_pending_jobs(self):
        """Load pending jobs from database on startup"""
        self.cursor.execute("""
            SELECT * FROM processing_jobs 
            WHERE status IN ('pending', 'processing')
            ORDER BY priority ASC, created_at ASC
        """)
        
        for row in self.cursor.fetchall():
            job = ProcessingJob(
                job_id=row[0],
                document_name=row[1],
                page_range=(row[2], row[3]),
                chunk_id=row[4],
                priority=row[5],
                status=row[6],
                created_at=datetime.fromisoformat(row[7]),
                retry_count=row[8],
                error_message=row[9]
            )
            self.priority_queue.put(job)
    
    def add_job(self, job: ProcessingJob):
        """Add job to queue and database"""
        # Store in database
        self.cursor.execute("""
            INSERT OR REPLACE INTO processing_jobs 
            (job_id, document_name, page_start, page_end, chunk_id, 
             priority, status, created_at, retry_count, error_message, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.job_id, job.document_name, job.page_range[0], job.page_range[1],
            job.chunk_id, job.priority, job.status, 
            job.created_at.isoformat(), job.retry_count, job.error_message,
            datetime.now().isoformat()
        ))
        self.conn.commit()
        
        # Add to in-memory queue
        self.priority_queue.put(job)
    
    def get_next_job(self) -> Optional[ProcessingJob]:
        """Get next job from queue"""
        try:
            job = self.priority_queue.get_nowait()
            
            # Update status to processing
            self.cursor.execute("""
                UPDATE processing_jobs 
                SET status = 'processing', last_updated = ?
                WHERE job_id = ?
            """, (datetime.now().isoformat(), job.job_id))
            self.conn.commit()
            
            return job
        except:
            return None
    
    def complete_job(self, job_id: str):
        """Mark job as completed"""
        self.cursor.execute("""
            UPDATE processing_jobs 
            SET status = 'completed', last_updated = ?
            WHERE job_id = ?
        """, (datetime.now().isoformat(), job_id))
        self.conn.commit()
    
    def fail_job(self, job_id: str, error: str, retry: bool = True):
        """Mark job as failed, optionally retry"""
        self.cursor.execute("""
            SELECT retry_count FROM processing_jobs WHERE job_id = ?
        """, (job_id,))
        row = self.cursor.fetchone()
        retry_count = row[0] if row else 0
        
        if retry and retry_count < 3:
            # Retry with backoff
            new_priority = 10 + retry_count  # Lower priority for retries
            self.cursor.execute("""
                UPDATE processing_jobs 
                SET status = 'pending', retry_count = ?, 
                    error_message = ?, priority = ?, last_updated = ?
                WHERE job_id = ?
            """, (retry_count + 1, error, new_priority, datetime.now().isoformat(), job_id))
        else:
            # Mark as failed permanently
            self.cursor.execute("""
                UPDATE processing_jobs 
                SET status = 'failed', error_message = ?, last_updated = ?
                WHERE job_id = ?
            """, (error, datetime.now().isoformat(), job_id))
        
        self.conn.commit()
    
    def save_checkpoint(self, document_name: str, last_page: int, total_pages: int,
                       completed_chunks: List[str], failed_chunks: List[str]):
        """Save processing checkpoint"""
        self.cursor.execute("""
            INSERT OR REPLACE INTO document_checkpoints 
            (document_name, last_processed_page, total_pages, 
             completed_chunks, failed_chunks, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            document_name, last_page, total_pages,
            json.dumps(completed_chunks), json.dumps(failed_chunks),
            datetime.now().isoformat()
        ))
        self.conn.commit()
    
    def get_checkpoint(self, document_name: str) -> Optional[Dict]:
        """Get checkpoint for document"""
        self.cursor.execute("""
            SELECT * FROM document_checkpoints WHERE document_name = ?
        """, (document_name,))
        row = self.cursor.fetchone()
        
        if row:
            return {
                'last_page': row[1],
                'total_pages': row[2],
                'completed_chunks': json.loads(row[3]),
                'failed_chunks': json.loads(row[4])
            }
        return None
