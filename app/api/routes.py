import os
import logging
from flask import Blueprint, render_template, request, redirect, url_for, send_file, jsonify, flash, session, current_app
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime

from config.settings import Config
from app.models.database import FileRepository
from app.services.pdf_service import PDFService

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

def safe_remove(path: str, retries: int = 3, delay: float = 0.5) -> bool:
    """
    Delete a file with retries — needed on Windows where file handles
    can be held briefly after close() returns.
    """
    import time
    for attempt in range(retries):
        try:
            if os.path.exists(path):
                os.remove(path)
            return True
        except PermissionError:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logger.warning(f"Could not delete '{path}' after {retries} attempts — skipping.")
    return False


# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please login to access this page', 'warning')
            return redirect(url_for('main.login_page'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
def index():
    file_repo = FileRepository()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    files = file_repo.get_files(limit=per_page, offset=offset)
    return render_template('pdf_library.html', files=files, page=page)

@bp.route('/login', methods=['GET', 'POST'])
def login_page():
    if session.get('logged_in'):
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == Config.VALID_USERNAME and password == Config.VALID_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            session['login_time'] = datetime.now().isoformat()
            current_app.logger.info(f"User {username} logged in successfully")
            flash('Login successful!', 'success')
            return redirect(url_for('main.index'))
        
        current_app.logger.warning(f"Failed login attempt for username: {username}")
        flash('Invalid username or password', 'danger')
        return render_template('loginpage.html')
    
    return render_template('loginpage.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.login_page'))

@bp.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('main.index'))
    
    uploaded_file = request.files['file']
    input_language = request.form.get('input-language', 'en')
    
    if uploaded_file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('main.index'))
    
    # Validate file type
    if not uploaded_file.filename.lower().endswith('.pdf'):
        flash('Only PDF files are allowed', 'danger')
        return redirect(url_for('main.index'))
    
    # Secure filename
    original_filename = secure_filename(uploaded_file.filename)
    filename_without_ext = os.path.splitext(original_filename)[0]
    
    # Check if file already exists in database
    file_repo = FileRepository()
    existing_file = file_repo.get_file_by_name(filename_without_ext)
    
    if existing_file:
         flash(f'File "{original_filename}" already exists.', 'warning')
         return redirect(url_for('main.index'))

    # Save to raw files directory
    raw_file_path = os.path.join(Config.RAW_FILES_DIR, original_filename)
    if not os.path.exists(Config.RAW_FILES_DIR):
        os.makedirs(Config.RAW_FILES_DIR)
        
    uploaded_file.save(raw_file_path)
    file_size = os.path.getsize(raw_file_path)

    # Process file with PDFService
    pdf_service = PDFService(gemini_api_key=Config.GEMINI_API_KEY)
    success = pdf_service.process_pdf(raw_file_path, filename_without_ext, input_language)
    
    if success:
        # Save to database
        file_repo.insert_file(
            filename_without_ext, 
            file_size, 
            'pdf'
        )
        flash(f'File "{original_filename}" uploaded and processed successfully!', 'success')
        current_app.logger.info(f"File uploaded: {original_filename}")
        return redirect(url_for('main.index'))
    else:
        # Clean up if processing failed
        safe_remove(raw_file_path)
        flash('Error processing file', 'danger')
        current_app.logger.error(f"File processing failed: {original_filename}")
    
    return redirect(url_for('main.index'))

@bp.route('/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('query', '').strip()
    file_repo = FileRepository()
    files = file_repo.get_files(query) if query else []
    return render_template('pdf_library.html', files=files, query=query)

@bp.route('/delete/<filename>', methods=['DELETE'])
@login_required
def delete(filename):
    file_repo = FileRepository()
    
    # Delete from filesystem
    files_to_delete = [
        os.path.join(Config.OUTPUT_FILES_DIR, f"{filename}.pdf"),
        os.path.join(Config.OUTPUT_OCR_FILES_DIR, f"{filename}.docx"),
        os.path.join(Config.OUTPUT_DOCX_FILES_DIR, f"{filename}.docx"),
        os.path.join(Config.RAW_FILES_DIR, f"{filename}.pdf")
    ]
    
    deleted = False
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            if safe_remove(file_path):
                deleted = True
    
    if deleted:
        file_repo.delete_file(filename)
        current_app.logger.info(f"File deleted: {filename}")
        return jsonify({"message": "File deleted successfully"}), 200
    else:
        return jsonify({"message": "File not found"}), 404

@bp.route('/stats')
@login_required
def stats():
    file_repo = FileRepository()
    stats = file_repo.get_file_stats()
    return render_template('stats.html', stats=stats)

@bp.route('/download/<filename>')
@login_required
def download(filename):
    file_path = os.path.join(Config.OUTPUT_DOCX_FILES_DIR, f"{filename}.docx")
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=f"{filename}_translated.docx")
    else:
        flash('File not found', 'danger')
        return redirect(url_for('main.index'))

@bp.route('/view/<filename>')
@login_required
def view(filename):
    file_path = os.path.join(Config.OUTPUT_FILES_DIR, f"{filename}.pdf")
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=False)
    else:
        flash('File not found', 'danger')
        return redirect(url_for('main.index'))

@bp.route('/view_ocr/<filename>')
@login_required
def view_ocr(filename):
    file_path = os.path.join(Config.OUTPUT_OCR_FILES_DIR, f"{filename}.docx")
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('File not found', 'danger')
        return redirect(url_for('main.index'))

@bp.route('/raw/<filename>')
@login_required
def raw(filename):
    file_path = os.path.join(Config.RAW_FILES_DIR, f"{filename}.pdf")
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=False)
    else:
        flash('File not found', 'danger')
        return redirect(url_for('main.index'))
