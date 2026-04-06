# Indic-Language PDF OCR & Translation Pipeline

An advanced, production-ready Flask web application designed to natively parse, extract, and accurately translate highly complex documents (including large 1000+ page PDFs) spanning Indic languages like Gujarati, Hindi, Marathi, and Sanskrit.

## 🚀 Key Features

* **Hybrid OCR Architecture**: Dynamically routes page analysis between Tesseract 5 (leveraged heavily for pristine Indic script accuracy) and PaddleOCR (for generalized CJK/European workloads).
* **Massive Document Architecture**: Includes an enterprise scale SQLite-backed asynchronous pipeline. Capable of slicing 1000+ page PDFs into semantic blocks, scoring importance, and persisting checkpoints to avoid data loss.
* **Smart Translation (Gemini SDK)**: Harnesses Google's powerful `gemini-2.5-flash` via the latest `google-genai` SDK, wrapped rigorously in token buckets, jittered exponential backoffs, and rate-limit tracking to survive free-tier bounds smoothly.
* **Dynamic Font Resilience**: Outputs properly structured translated PDFs (via FPDF) equipped with active fallback mapping across Devanagari and Arial font spaces, cleanly gracefully dodging `latin-1` layout crashes entirely, backed further by exact `.docx` equivalents.
* **PostgreSQL Integration**: Complete schema setup mapping out user management and library sessions tightly against a modern `psycopg2` thread-pool.

## 🛠️ Prerequisites

* Python 3.10+
* **Tesseract-OCR**: Ensure Tesseract is installed on your OS and that you have downloaded the required `.traineddata` sets (`guj`, `hin`, `san`, `mar`) into your `tessdata` directory.
* **PostgreSQL**: Standing Postgres database natively listening for connections.
* **uv Package Manager** (Optional, but recommended for blisteringly fast dependency management)

## 💻 Getting Started

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/mokshpunamiya/Translation_hindi_gujrati_sanskrit_ocr.git
cd Translation_hindi_gujrati_sanskrit_ocr

# Install the dependencies natively using uv
uv sync
```

### 2. Environment Configuration
Create a `.env` file at the root of the project:

```env
# Google Gemini SDK Key
GEMINI_API_KEY=your_gemini_api_key_here

# PostgreSQL Database Credentials
DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_NAME=pdf_ocr_db

# Application Admin Accounts
ADMIN_USERNAME=admin
ADMIN_PASSWORD=pdfocr
SECRET_KEY=your_secure_flask_secret_key
```

### 3. Startup

```bash
# First start will trigger the app/models/database.py to
# execute schema.sql and build all missing tables automatically.

uv run python run.py
```

Navigate to `http://localhost:5000` inside your browser, log in utilizing your admin credentials, and begin uploading your PDFs.

## 📁 Repository Map

* `app/api/`: Flask Blueprint routers determining uploads, library deletes, and file downloads.
* `app/services/`: Core logic (OCR routing, PDF synthesis bounding, Gemini API management).
* `app/services/large_doc/` & `config/large_document_config.py`: The high-throughput modular pipeline (chunkers, distributed workers, adaptive token rate-limits).
* `app/models/`: Database pooling handling PG interactions.

---
*Built intricately for precise formatting preservation and indic-script durability.*
