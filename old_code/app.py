import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, flash, session
from werkzeug.utils import secure_filename
from functools import wraps
import hashlib
from datetime import datetime

from config import config, Config
from database import db_pool, FileRepository
from model import extract_text_and_translate
from file_utils import FileUploader, FileDeleter

# Configure logging
def setup_logging(app):
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler('logs/pdf_ocr.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('PDF OCR application startup')

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize database pool
    db_pool.initialize()
    
    # Setup logging
    setup_logging(app)
    
    # File repositories
    file_repo = FileRepository()
    file_uploader = FileUploader()
    file_deleter = FileDeleter()
    
    # Authentication decorator
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                flash('Please login to access this page', 'warning')
                return redirect(url_for('loginpage'))
            return f(*args, **kwargs)
        return decorated_function
    
    # Routes
    @app.route('/')
    @login_required
    def index():
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page
        files = file_repo.get_files(limit=per_page, offset=offset)
        return render_template('pdf_library.html', files=files, page=page)
    
    @app.route('/loginpage')
    def loginpage():
        if session.get('logged_in'):
            return redirect(url_for('index'))
        return render_template('loginpage.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if username == Config.VALID_USERNAME and password == Config.VALID_PASSWORD:
                session['logged_in'] = True
                session['username'] = username
                session['login_time'] = datetime.now().isoformat()
                app.logger.info(f"User {username} logged in successfully")
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            
            app.logger.warning(f"Failed login attempt for username: {username}")
            flash('Invalid username or password', 'danger')
            return render_template('loginpage.html')
        
        return render_template('loginpage.html')
    
    @app.route('/logout')
    def logout():
        session.clear()
        flash('You have been logged out', 'info')
        return redirect(url_for('loginpage'))
    
    @app.route('/upload', methods=['POST'])
    @login_required
    def upload():
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(url_for('index'))
        
        uploaded_file = request.files['file']
        input_language = request.form.get('input-language')
        
        if uploaded_file.filename == '':
            flash('No file selected', 'danger')
            return redirect(url_for('index'))
        
        # Validate file type
        if not uploaded_file.filename.lower().endswith('.pdf'):
            flash('Only PDF files are allowed', 'danger')
            return redirect(url_for('index'))
        
        # Process file
        result = file_uploader.process_file(uploaded_file, input_language)
        
        if result['status'] == 'success':
            # Save to database
            file_repo.insert_file(
                result['filename'], 
                result['file_size'], 
                'pdf'
            )
            flash(f'File "{result["filename"]}" uploaded and processed successfully!', 'success')
            app.logger.info(f"File uploaded: {result['filename']}")
            return redirect(url_for('index'))
        elif result['status'] == 'exists':
            flash('File already exists', 'warning')
        else:
            flash('Error processing file', 'danger')
            app.logger.error(f"File upload failed: {result.get('error', 'Unknown error')}")
        
        return redirect(url_for('index'))
    
    @app.route('/search', methods=['GET'])
    @login_required
    def search():
        query = request.args.get('query', '').strip()
        if query:
            files = file_repo.get_files(query)
        else:
            files = []
        return render_template('library.html', files=files, query=query)
    
    @app.route('/pdf_search', methods=['GET'])
    @login_required
    def pdf_search():
        query = request.args.get('query', '').strip()
        files = file_repo.get_files(query) if query else []
        return render_template('pdf_library.html', files=files, query=query)
    
    @app.route('/delete/<filename>', methods=['DELETE'])
    @login_required
    def delete(filename):
        success = file_deleter.delete_file(filename)
        
        if success:
            file_repo.delete_file(filename)
            app.logger.info(f"File deleted: {filename}")
            return jsonify({"message": "File deleted successfully"}), 200
        else:
            return jsonify({"message": "File not found"}), 404
    
    @app.route('/library')
    @login_required
    def library():
        files = file_repo.get_files()
        return render_template('library.html', files=files)
    
    @app.route('/stats')
    @login_required
    def stats():
        stats = file_repo.get_file_stats()
        return render_template('stats.html', stats=stats)
    
    @app.route('/download/<filename>')
    @login_required
    def download(filename):
        file_path = os.path.join(Config.OUTPUT_DOCX_FILES_DIR, f"{filename}.docx")
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=f"{filename}_translated.docx")
        else:
            flash('File not found', 'danger')
            return redirect(url_for('index'))
    
    @app.route('/view/<filename>')
    @login_required
    def view(filename):
        file_path = os.path.join(Config.OUTPUT_FILES_DIR, f"{filename}.pdf")
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=False)
        else:
            flash('File not found', 'danger')
            return redirect(url_for('index'))
    
    @app.route('/view_ocr/<filename>')
    @login_required
    def view_ocr(filename):
        file_path = os.path.join(Config.OUTPUT_OCR_FILES_DIR, f"{filename}.docx")
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            flash('File not found', 'danger')
            return redirect(url_for('index'))
    
    @app.route('/raw/<filename>')
    @login_required
    def raw(filename):
        file_path = os.path.join(Config.RAW_FILES_DIR, f"{filename}.pdf")
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=False)
        else:
            flash('File not found', 'danger')
            return redirect(url_for('index'))
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}')
        return render_template('500.html'), 500
    
    return app

# Create application instance
app = create_app(os.environ.get('FLASK_CONFIG', 'development'))

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])