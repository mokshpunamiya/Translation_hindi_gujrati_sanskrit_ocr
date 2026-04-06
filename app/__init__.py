import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from config.settings import config
from app.models.database import db_pool

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize database pool
    db_pool.initialize(app.config)
    
    # Configure logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler('logs/pdf_ocr.log', maxBytes=10*1024*1024, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('PDF OCR application startup')
    
    # Register blueprints
    from app.api.routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
