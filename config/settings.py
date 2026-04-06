import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB max file size
    # Database settings
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'pdf_ocr_db')
    
    # Gemini API settings
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    
    # App settings
    VALID_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    VALID_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'pdfocr')
    
    # Base directory of the project
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # File paths (Using Absolute Paths to prevent Flask send_file resolution errors)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    RAW_FILES_DIR = os.path.join(BASE_DIR, 'raw_files')
    OUTPUT_FILES_DIR = os.path.join(BASE_DIR, 'output_files')
    OUTPUT_OCR_FILES_DIR = os.path.join(BASE_DIR, 'output_ocr_files')
    OUTPUT_DOCX_FILES_DIR = os.path.join(BASE_DIR, 'output_docx_files')
    FONT_DIR = os.path.join(BASE_DIR, 'font_files')

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
