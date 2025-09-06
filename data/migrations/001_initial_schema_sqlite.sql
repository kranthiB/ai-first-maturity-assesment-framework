-- migrations/001_initial_schema_sqlite.sql
-- SQLite-specific initial database schema for AFS Assessment Framework

-- Enable foreign key support
PRAGMA foreign_keys = ON;

-- Drop tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS responses;
DROP TABLE IF EXISTS assessment_recommendations;
DROP TABLE IF EXISTS assessment_sections;
DROP TABLE IF EXISTS assessment_exports;
DROP TABLE IF EXISTS assessments;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS areas;
DROP TABLE IF EXISTS sections;
DROP TABLE IF EXISTS schema_migrations;

-- Create schema migrations tracking table
CREATE TABLE schema_migrations (
    version TEXT PRIMARY KEY,
    description TEXT,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial migration record
INSERT INTO schema_migrations (version, description) VALUES ('001', 'Initial schema creation');

-- Create sections table
CREATE TABLE sections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    color TEXT DEFAULT '#3b82f6',
    icon TEXT DEFAULT 'fas fa-cog',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create areas table  
CREATE TABLE areas (
    id TEXT PRIMARY KEY,
    section_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    timeline_l1_l2 TEXT,
    timeline_l2_l3 TEXT,
    timeline_l3_l4 TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (section_id) REFERENCES sections(id)
);

-- Create questions table
CREATE TABLE questions (
    id TEXT PRIMARY KEY,
    area_id TEXT NOT NULL,
    question TEXT NOT NULL,
    level_1_desc TEXT NOT NULL,
    level_2_desc TEXT NOT NULL,
    level_3_desc TEXT NOT NULL,
    level_4_desc TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (area_id) REFERENCES areas(id)
);

-- Create assessments table
CREATE TABLE assessments (
    id TEXT PRIMARY KEY,
    team_name TEXT NOT NULL,
    overall_score REAL,
    deviq_classification TEXT,
    completion_date DATETIME,
    results_json TEXT,
    status TEXT DEFAULT 'IN_PROGRESS',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Computed scores stored for performance
    foundational_score REAL,
    transformation_score REAL, 
    enterprise_score REAL,
    governance_score REAL,
    
    -- Additional metadata
    assessment_duration_minutes INTEGER,
    ip_address TEXT,
    user_agent TEXT
);

-- Create responses table
CREATE TABLE responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 1 AND score <= 4),
    notes TEXT,
    response_time_seconds INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (assessment_id) REFERENCES assessments(id),
    FOREIGN KEY (question_id) REFERENCES questions(id),
    
    -- Ensure one response per question per assessment
    UNIQUE(assessment_id, question_id)
);

-- Create assessment_sections table for storing section-level scores
CREATE TABLE assessment_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id TEXT NOT NULL,
    section_id TEXT NOT NULL,
    average_score REAL NOT NULL,
    area_scores_json TEXT,
    maturity_level TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (assessment_id) REFERENCES assessments(id),
    FOREIGN KEY (section_id) REFERENCES sections(id),
    
    -- Ensure one record per section per assessment
    UNIQUE(assessment_id, section_id)
);

-- Create recommendations table for storing generated recommendations
CREATE TABLE assessment_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id TEXT NOT NULL,
    recommendation_text TEXT NOT NULL,
    priority_level INTEGER DEFAULT 1,
    category TEXT,
    area_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (assessment_id) REFERENCES assessments(id),
    FOREIGN KEY (area_id) REFERENCES areas(id)
);

-- Create exports table for tracking data exports
CREATE TABLE assessment_exports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_ids TEXT NOT NULL,
    export_type TEXT NOT NULL,
    file_path TEXT,
    exported_by TEXT,
    export_parameters_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);

-- Insert default sections data
INSERT INTO sections (id, name, description, display_order, color, icon) VALUES
('FC', 'FOUNDATIONAL CAPABILITIES', 'Core building blocks for AI-driven development, including infrastructure, team skills, code generation processes, and knowledge management systems that enable basic AI integration into software engineering workflows', 1, '#3b82f6', 'fas fa-foundation'),
('TC', 'TRANSFORMATION CAPABILITIES', 'Advanced capabilities that fundamentally transform how software is built, including intelligent architecture translation, autonomous testing, smart CI/CD, monitoring systems, and legacy modernization using AI', 2, '#10b981', 'fas fa-magic'),
('EI', 'ENTERPRISE INTEGRATION', 'Enterprise-scale capabilities for integrating AI development practices across the organization, including data governance, vendor management, system integration, cost optimization, scalability, and business continuity', 3, '#f59e0b', 'fas fa-building'),
('SG', 'STRATEGIC GOVERNANCE', 'Leadership and governance frameworks for responsible, compliant, and strategically aligned AI adoption, including ethics, performance measurement, IP management, risk management, change management, and future readiness', 4, '#8b5cf6', 'fas fa-shield-alt');
