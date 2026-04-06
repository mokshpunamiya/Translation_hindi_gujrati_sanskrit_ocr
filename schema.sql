-- Note: PostgreSQL creation syntax
-- Run this part separately if the DB doesn't exist:
-- CREATE DATABASE pdf_ocr_db;

-- Connect to your database before running the table creation below.
-- \c pdf_ocr_db;

-- Enhanced file_names table
CREATE TABLE IF NOT EXISTS file_names (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL UNIQUE,
    original_filename VARCHAR(255),
    file_size BIGINT,
    file_type VARCHAR(50),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_filename ON file_names(filename);
CREATE INDEX IF NOT EXISTS idx_upload_date ON file_names(upload_date);
CREATE INDEX IF NOT EXISTS idx_status ON file_names(status);

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100),
    session_token VARCHAR(255),
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_time TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_session_token ON user_sessions(session_token);

-- Processing logs table
CREATE TABLE IF NOT EXISTS processing_logs (
    id SERIAL PRIMARY KEY,
    file_id INT REFERENCES file_names(id) ON DELETE CASCADE,
    page_number INT,
    processing_time FLOAT,
    ocr_confidence FLOAT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_file_id ON processing_logs(file_id);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100),
    action VARCHAR(50),
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_username ON audit_logs(username);
CREATE INDEX IF NOT EXISTS idx_created_at ON audit_logs(created_at);