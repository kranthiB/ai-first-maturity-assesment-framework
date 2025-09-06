-- migrations/002_add_indexes_sqlite.sql  
-- SQLite-specific performance indexes for AFS Assessment Framework

INSERT INTO schema_migrations (version, description) VALUES ('002', 'Add performance indexes');

-- Primary lookup indexes
CREATE INDEX idx_areas_section ON areas(section_id, display_order);
CREATE INDEX idx_questions_area ON questions(area_id, display_order);
CREATE INDEX idx_questions_active ON questions(is_active, display_order);

-- Assessment query indexes  
CREATE INDEX idx_assessments_status ON assessments(status, created_at);
CREATE INDEX idx_assessments_team ON assessments(team_name, created_at);
CREATE INDEX idx_assessments_completion ON assessments(completion_date DESC);
CREATE INDEX idx_assessments_score ON assessments(overall_score, deviq_classification);

-- Response analysis indexes
CREATE INDEX idx_responses_assessment ON responses(assessment_id, question_id);
CREATE INDEX idx_responses_question ON responses(question_id, score);
CREATE INDEX idx_responses_timestamp ON responses(timestamp);

-- Section scores indexes
CREATE INDEX idx_assessment_sections_assessment ON assessment_sections(assessment_id, section_id);
CREATE INDEX idx_assessment_sections_score ON assessment_sections(section_id, average_score);

-- Analytics indexes
CREATE INDEX idx_recommendations_assessment ON assessment_recommendations(assessment_id, priority_level);
CREATE INDEX idx_recommendations_area ON assessment_recommendations(area_id, priority_level);

-- Export tracking indexes
CREATE INDEX idx_exports_created ON assessment_exports(created_at);
CREATE INDEX idx_exports_expires ON assessment_exports(expires_at);

-- Composite indexes for common queries
CREATE INDEX idx_assessments_team_score ON assessments(team_name, overall_score, completion_date);
CREATE INDEX idx_responses_score_analysis ON responses(question_id, score, timestamp);
