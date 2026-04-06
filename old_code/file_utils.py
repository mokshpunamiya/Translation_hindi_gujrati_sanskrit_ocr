import os
import hashlib
from pathlib import Path
from werkzeug.utils import secure_filename
from config import Config
from model import extract_text_and_translate
import logging

logger = logging.getLogger(__name__)

class FileUploader:
    def __init__(self):
        self._ensure_directories()
    
    def _ensure_directories(self):
        directories = [
            Config.RAW_FILES_DIR,
            Config.OUTPUT_FILES_DIR,
            Config.OUTPUT_OCR_FILES_DIR,
            Config.OUTPUT_DOCX_FILES_DIR
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _calculate_file_hash(self, file):
        """Calculate file hash for duplicate detection"""
        file.seek(0)
        sha256_hash = hashlib.sha256()
        for chunk in iter(lambda: file.read(4096), b""):
            sha256_hash.update(chunk)
        file.seek(0)
        return sha256_hash.hexdigest()
    
    def process_file(self, uploaded_file, input_language):
        try:
            # Secure filename
            original_filename = secure_filename(uploaded_file.filename)
            name_without_ext = os.path.splitext(original_filename)[0]
            
            # Check if file already exists
            raw_file_path = os.path.join(Config.RAW_FILES_DIR, original_filename)
            if os.path.exists(raw_file_path):
                return {
                    'status': 'exists',
                    'filename': name_without_ext
                }
            
            # Save file
            file_size = len(uploaded_file.read())
            uploaded_file.seek(0)
            uploaded_file.save(raw_file_path)
            
            # Process file
            result = extract_text_and_translate(raw_file_path, name_without_ext, input_language)
            
            if result == 'success':
                return {
                    'status': 'success',
                    'filename': name_without_ext,
                    'file_size': file_size,
                    'original_name': original_filename
                }
            else:
                # Clean up if processing failed
                if os.path.exists(raw_file_path):
                    os.remove(raw_file_path)
                return {
                    'status': 'error',
                    'error': 'Processing failed'
                }
                
        except Exception as e:
            logger.error(f"File upload error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

class FileDeleter:
    def delete_file(self, filename):
        try:
            files_to_delete = [
                os.path.join(Config.OUTPUT_FILES_DIR, f"{filename}.pdf"),
                os.path.join(Config.OUTPUT_OCR_FILES_DIR, f"{filename}.docx"),
                os.path.join(Config.OUTPUT_DOCX_FILES_DIR, f"{filename}.docx"),
                os.path.join(Config.RAW_FILES_DIR, f"{filename}.pdf")
            ]
            
            deleted = False
            for file_path in files_to_delete:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted = True
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting file {filename}: {e}")
            return False