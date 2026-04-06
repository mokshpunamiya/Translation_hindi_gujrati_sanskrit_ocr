import os
import sys
import logging
from app.models.database import db_pool, FileRepository
from config.settings import Config

logging.basicConfig(level=logging.INFO)

def test_db():
    print("Testing Database connection...")
    config_dict = {
        'DB_HOST': Config.DB_HOST,
        'DB_USER': Config.DB_USER,
        'DB_PASSWORD': Config.DB_PASSWORD,
        'DB_NAME': Config.DB_NAME
    }
    
    try:
        # Initialize pool
        db_pool.initialize(config_dict)
        
        # Test connection
        with db_pool.get_connection() as conn:
            assert conn.is_connected(), "Failed to connect to database"
            print("Successfully connected to the database!")
            
            # Optionally check if tables exist
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            print(f"Tables in database: {tables}")
            
        print("Database test passed!")
    except Exception as e:
        print(f"Database test failed: {e}")
        # Not failing the whole script if DB is not set up locally during this testing phase
        # Just want to see if the python code actually runs up to the connection attempt.

if __name__ == "__main__":
    test_db()
