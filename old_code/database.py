import mysql.connector
from mysql.connector import pooling
from contextlib import contextmanager
import logging
from config import Config

logger = logging.getLogger(__name__)

class DatabasePool:
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self):
        if self._pool is None:
            try:
                self._pool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name="pdf_ocr_pool",
                    pool_size=10,
                    pool_reset_session=True,
                    host=Config.DB_HOST,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    database=Config.DB_NAME
                )
                logger.info("Database connection pool initialized")
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {e}")
                raise
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = self._pool.get_connection()
            yield conn
        except Exception as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

db_pool = DatabasePool()

class FileRepository:
    def __init__(self):
        self.db = db_pool
    
    def get_file_by_name(self, filename):
        with self.db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM file_names WHERE filename = %s", (filename,))
            return cursor.fetchone()
    
    def insert_file(self, filename, file_size, file_type):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO file_names (filename, file_size, file_type, upload_date) VALUES (%s, %s, %s, NOW())",
                (filename, file_size, file_type)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_files(self, query=None, limit=100, offset=0):
        with self.db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            if query:
                sql_query = "SELECT * FROM file_names WHERE filename LIKE %s LIMIT %s OFFSET %s"
                cursor.execute(sql_query, ('%' + query + '%', limit, offset))
            else:
                cursor.execute("SELECT * FROM file_names LIMIT %s OFFSET %s", (limit, offset))
            return cursor.fetchall()
    
    def delete_file(self, filename):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM file_names WHERE filename = %s", (filename,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_file_stats(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total FROM file_names")
            total = cursor.fetchone()
            cursor.execute("SELECT DATE(upload_date) as date, COUNT(*) as count FROM file_names GROUP BY DATE(upload_date)")
            daily_stats = cursor.fetchall()
            return {'total': total['total'], 'daily_stats': daily_stats}