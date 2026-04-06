#!/bin/bash

# PDF OCR Application Deployment Script

echo "Starting deployment of PDF OCR application..."

# Check Python version
python_version=$(python3 --version)
echo "Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "Creating application directories..."
mkdir -p logs uploads raw_files output_files output_ocr_files output_docx_files font_files

# Copy font files if needed
if [ ! -f "font_files/DejaVuSansCondensed.ttf" ]; then
    echo "Warning: DejaVuSansCondensed.ttf not found in font_files directory"
    echo "Please add font file for proper PDF rendering"
fi

# Set up environment variables
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please update .env with your configuration"
fi

# Initialize database
echo "Initializing database..."
python -c "from app import app; from database import db_pool; db_pool.initialize()"

# Run database migrations if needed
if [ -f "migrations/schema.sql" ]; then
    echo "Running database migrations..."
    mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME < migrations/schema.sql
fi

# Set up logging
echo "Setting up logging..."
touch logs/pdf_ocr.log
chmod 666 logs/pdf_ocr.log

# Set up systemd service (optional)
if [ -f "pdf_ocr.service" ]; then
    echo "Setting up systemd service..."
    sudo cp pdf_ocr.service /etc/systemd/system/
    sudo systemctl daemon-reload
fi

echo "Deployment completed!"
echo "To start the application:"
echo "  source venv/bin/activate"
echo "  export FLASK_APP=app.py"
echo "  flask run"
echo ""
echo "Or with systemd:"
echo "  sudo systemctl start pdf_ocr"