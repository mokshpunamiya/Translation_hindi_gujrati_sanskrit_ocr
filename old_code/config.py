import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    
    # Database settings
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_USER = os.environ.get('DB_USER', '')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'pdf_ocr_db')
    
    # OpenAI settings
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    
    # App settings
    VALID_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    VALID_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'pdfocr')
    
    # File paths
    RAW_FILES_DIR = 'raw_files'
    OUTPUT_FILES_DIR = 'output_files'
    OUTPUT_OCR_FILES_DIR = 'output_ocr_files'
    OUTPUT_DOCX_FILES_DIR = 'output_docx_files'
    FONT_DIR = 'font_files'

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
class TestingConfig(Config):
    DEBUG = False
    TESTING = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}