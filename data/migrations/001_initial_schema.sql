-- migrations/001_initial_schema.sql
-- Initial database schema for AFS Assessment Framework
-- Compatible with H2, PostgreSQL, and MySQL

-- Drop tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS responses CASCADE;
DROP TABLE IF EXISTS assessments CASCADE;
DROP TABLE IF EXISTS questions CASCADE;
DROP TABLE IF EXISTS areas CASCADE;
DROP TABLE IF EXISTS sections CASCADE;
DROP TABLE IF EXISTS schema_migrations CASCADE;

-- Create schema migrations tracking table
CREATE TABLE schema_migrations (
    version VARCHAR(20) PRIMARY KEY,
    description VARCHAR(255),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial migration record
INSERT INTO schema_migrations (version, description) VALUES ('001', 'Initial schema creation');

-- Create sections table
CREATE TABLE sections (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    color VARCHAR(7) DEFAULT '#3b82f6',
    icon VARCHAR(50) DEFAULT 'fas fa-cog',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create areas table  
CREATE TABLE areas (
    id VARCHAR(20) PRIMARY KEY,
    section_id VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    timeline_l1_l2 VARCHAR(20),
    timeline_l2_l3 VARCHAR(20),
    timeline_l3_l4 VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
);

-- Create questions table
CREATE TABLE questions (
    id VARCHAR(20) PRIMARY KEY,
    area_id VARCHAR(20) NOT NULL,
    question TEXT NOT NULL,
    level_1_desc TEXT NOT NULL,
    level_2_desc TEXT NOT NULL,
    level_3_desc TEXT NOT NULL,
    level_4_desc TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE CASCADE
);

-- Create assessments table
CREATE TABLE assessments (
    id VARCHAR(50) PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    overall_score DECIMAL(3,2),
    deviq_classification VARCHAR(30),
    completion_date TIMESTAMP,
    results_json TEXT,
    status VARCHAR(20) DEFAULT 'IN_PROGRESS', -- IN_PROGRESS, COMPLETED, ARCHIVED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Computed scores stored for performance
    foundational_score DECIMAL(3,2),
    transformation_score DECIMAL(3,2), 
    enterprise_score DECIMAL(3,2),
    governance_score DECIMAL(3,2),
    
    -- Additional metadata
    assessment_duration_minutes INTEGER,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Create responses table
CREATE TABLE responses (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    assessment_id VARCHAR(50) NOT NULL,
    question_id VARCHAR(20) NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 1 AND score <= 4),
    notes TEXT,
    response_time_seconds INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE RESTRICT,
    
    -- Ensure one response per question per assessment
    UNIQUE(assessment_id, question_id)
);

-- Create assessment_sections table for storing section-level scores
CREATE TABLE assessment_sections (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    assessment_id VARCHAR(50) NOT NULL,
    section_id VARCHAR(10) NOT NULL,
    average_score DECIMAL(3,2) NOT NULL,
    area_scores_json TEXT, -- JSON object with area-level scores
    maturity_level VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE RESTRICT,
    
    -- Ensure one record per section per assessment
    UNIQUE(assessment_id, section_id)
);

-- Create recommendations table for storing generated recommendations
CREATE TABLE assessment_recommendations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    assessment_id VARCHAR(50) NOT NULL,
    recommendation_text TEXT NOT NULL,
    priority_level INTEGER DEFAULT 1, -- 1=High, 2=Medium, 3=Low
    category VARCHAR(50), -- quick_win, foundational, transformation, etc.
    area_id VARCHAR(20), -- Which area this recommendation targets
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE SET NULL
);

-- Create exports table for tracking data exports
CREATE TABLE assessment_exports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    assessment_ids TEXT NOT NULL, -- Comma-separated list of assessment IDs
    export_type VARCHAR(20) NOT NULL, -- csv, excel, pdf
    file_path VARCHAR(500),
    exported_by VARCHAR(100),
    export_parameters_json TEXT, -- Filter/formatting parameters
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP -- For cleanup of temporary export files
);

-- Insert default data
INSERT INTO sections (id, name, description, display_order, color, icon) VALUES
('FC', 'FOUNDATIONAL CAPABILITIES', 'Core building blocks for AI-driven development, including infrastructure, team skills, code generation processes, and knowledge management systems that enable basic AI integration into software engineering workflows', 1, '#3b82f6', 'fas fa-foundation'),
('TC', 'TRANSFORMATION CAPABILITIES', 'Advanced capabilities that fundamentally transform how software is built, including intelligent architecture translation, autonomous testing, smart CI/CD, monitoring systems, and legacy modernization using AI', 2, '#10b981', 'fas fa-magic'),
('EI', 'ENTERPRISE INTEGRATION', 'Enterprise-scale capabilities for integrating AI development practices across the organization, including data governance, vendor management, system integration, cost optimization, scalability, and business continuity', 3, '#f59e0b', 'fas fa-building'),
('SG', 'STRATEGIC GOVERNANCE', 'Leadership and governance frameworks for responsible, compliant, and strategically aligned AI adoption, including ethics, performance measurement, IP management, risk management, change management, and future readiness', 4, '#8b5cf6', 'fas fa-shield-alt');

COMMIT;
