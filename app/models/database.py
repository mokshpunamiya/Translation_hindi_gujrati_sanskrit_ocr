import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class DatabasePool:
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self, config):
        if self._pool is None:
            try:
                self._pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=config.get('DB_HOST', 'localhost'),
                    user=config.get('DB_USER', 'postgres'),
                    password=config.get('DB_PASSWORD', ''),
                    dbname=config.get('DB_NAME', 'pdf_ocr_db')
                )
                logger.info("Database connection pool initialized")
                self._create_tables()
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {e}")
                
    def _create_tables(self):
        import os
        schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'schema.sql')
        if not os.path.exists(schema_path):
            logger.warning(f"Schema file not found at {schema_path}, skipping table creation.")
            return
            
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    with open(schema_path, 'r') as f:
                        schema_sql = f.read()
                        cursor.execute(schema_sql)
                conn.commit()
                logger.info("Database tables created/verified successfully.")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            
    @contextmanager
    def get_connection(self):
        if not self._pool:
             raise Exception("Database pool not initialized. Call initialize() first.")
        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
        except Exception as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self._pool.putconn(conn)

db_pool = DatabasePool()

class FileRepository:
    def __init__(self):
        self.db = db_pool
    
    def get_file_by_name(self, filename):
        with self.db.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM file_names WHERE filename = %s", (filename,))
            return cursor.fetchone()
    
    def insert_file(self, filename, file_size, file_type):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO file_names (filename, file_size, file_type, upload_date) VALUES (%s, %s, %s, CURRENT_TIMESTAMP) RETURNING id",
                (filename, file_size, file_type)
            )
            inserted_id = cursor.fetchone()[0]
            conn.commit()
            return inserted_id
    
    def get_files(self, query=None, limit=100, offset=0):
        with self.db.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            if query:
                sql_query = "SELECT * FROM file_names WHERE filename LIKE %s ORDER BY upload_date DESC LIMIT %s OFFSET %s"
                cursor.execute(sql_query, ('%' + query + '%', limit, offset))
            else:
                cursor.execute("SELECT * FROM file_names ORDER BY upload_date DESC LIMIT %s OFFSET %s", (limit, offset))
            return cursor.fetchall()
    
    def delete_file(self, filename):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM file_names WHERE filename = %s", (filename,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_file_stats(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT COUNT(*) as total FROM file_names")
            total = cursor.fetchone()
            cursor.execute("""
                SELECT DATE(upload_date) as date, COUNT(*) as count 
                FROM file_names 
                GROUP BY DATE(upload_date) 
                ORDER BY date DESC
            """)
            daily_stats = cursor.fetchall()
            return {'total': total['total'] if total else 0, 'daily_stats': daily_stats}
