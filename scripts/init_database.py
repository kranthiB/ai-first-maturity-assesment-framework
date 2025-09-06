#!/usr/bin/env python3
"""
Database Initialization Script for AFS Assessment Framework
Executes migrations and seeds data for initial setup
"""

import os
import json
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Initialize the AFS Assessment Framework database with schema and seed data"""
    
    def __init__(self, db_path: str = "app.db"):
        """Initialize with database path"""
        self.db_path = Path(db_path)
        self.project_root = Path(__file__).parent.parent
        self.migrations_dir = self.project_root / "data" / "migrations"
        self.seeds_dir = self.project_root / "data" / "seeds"
        
    def create_database(self) -> None:
        """Create database and execute migrations"""
        logger.info(f"Creating database at {self.db_path}")
        
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing database if it exists
        if self.db_path.exists():
            logger.info("Removing existing database")
            self.db_path.unlink()
            
        # Create new database and execute migrations
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Execute SQLite-specific migrations in order
            sqlite_migrations = [
                "001_initial_schema_sqlite.sql",
                "002_add_indexes_sqlite.sql", 
                "003_add_analytics_sqlite.sql"
            ]
            
            migrations = []
            for migration_name in sqlite_migrations:
                migration_path = self.migrations_dir / migration_name
                if migration_path.exists():
                    migrations.append(migration_path)
                else:
                    logger.warning(f"Migration not found: {migration_name}")
            
            for migration_file in migrations:
                logger.info(f"Executing migration: {migration_file.name}")
                
                # Read and adapt SQL for SQLite
                sql_content = self.read_sql_file(migration_file)
                adapted_sql = self.adapt_sql_for_sqlite(sql_content)
                
                try:
                    # Execute each statement separately
                    statements = self.split_sql_statements(adapted_sql)
                    for statement in statements:
                        if statement.strip():
                            conn.execute(statement)
                    
                    conn.commit()
                    logger.info(f"Successfully executed {migration_file.name}")
                    
                except Exception as e:
                    logger.error(f"Error executing {migration_file.name}: {str(e)}")
                    conn.rollback()
                    raise
                    
    def read_sql_file(self, file_path: Path) -> str:
        """Read SQL file content"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    def adapt_sql_for_sqlite(self, sql_content: str) -> str:
        """Adapt SQL for SQLite compatibility"""
        # Replace AUTO_INCREMENT with AUTOINCREMENT for SQLite
        sql_content = sql_content.replace("AUTO_INCREMENT", "AUTOINCREMENT")
        
        # Replace TEXT data type issues
        sql_content = sql_content.replace("TEXT NOT NULL", "TEXT")
        
        # Remove COMMENT clauses (not supported in SQLite)
        import re
        sql_content = re.sub(r'COMMENT\s+[\'"][^\'\"]*[\'"]', '', sql_content)
        
        # Replace CASCADE constraints for better SQLite compatibility
        sql_content = sql_content.replace("ON DELETE CASCADE", "")
        sql_content = sql_content.replace("ON DELETE RESTRICT", "")
        sql_content = sql_content.replace("ON DELETE SET NULL", "")
        
        # Remove GENERATED ALWAYS AS (not supported in older SQLite)
        sql_content = re.sub(r'GENERATED ALWAYS AS \([^)]+\)', '', sql_content)
        
        return sql_content
        
    def split_sql_statements(self, sql_content: str) -> List[str]:
        """Split SQL content into individual statements"""
        # Remove comments
        lines = []
        for line in sql_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('--'):
                lines.append(line)
        
        content = ' '.join(lines)
        
        # Split by semicolon, but be careful with string literals
        statements = []
        current_statement = ""
        in_string = False
        escape_next = False
        
        for char in content:
            if escape_next:
                current_statement += char
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                current_statement += char
                continue
                
            if char in ["'", '"'] and not escape_next:
                in_string = not in_string
                current_statement += char
                continue
                
            if char == ';' and not in_string:
                if current_statement.strip():
                    statements.append(current_statement.strip())
                current_statement = ""
                continue
                
            current_statement += char
            
        # Add final statement if it exists
        if current_statement.strip():
            statements.append(current_statement.strip())
            
        return statements
        
    def seed_database(self) -> None:
        """Load seed data into the database"""
        logger.info("Loading seed data")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Load seed files in dependency order
            seed_files = [
                "sections.json",
                "areas.json", 
                "questions.json",
                "recommendations.json"
            ]
            
            for seed_file in seed_files:
                file_path = self.seeds_dir / seed_file
                if file_path.exists():
                    logger.info(f"Loading seed data from {seed_file}")
                    self.load_seed_file(conn, file_path)
                else:
                    logger.warning(f"Seed file not found: {seed_file}")
                    
    def load_seed_file(self, conn: sqlite3.Connection, file_path: Path) -> None:
        """Load data from a specific seed file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if file_path.name == "sections.json":
                self.load_sections(conn, data.get("sections", []))
            elif file_path.name == "areas.json":
                self.load_areas(conn, data.get("areas", []))
            elif file_path.name == "questions.json":
                self.load_questions(conn, data.get("questions", []))
            elif file_path.name == "recommendations.json":
                # Recommendations are template data, not directly loaded
                logger.info("Recommendations data available for application logic")
                
        except Exception as e:
            logger.error(f"Error loading {file_path.name}: {str(e)}")
            raise
            
    def load_sections(self, conn: sqlite3.Connection, sections: List[Dict[str, Any]]) -> None:
        """Load sections data"""
        for section in sections:
            conn.execute("""
                INSERT OR REPLACE INTO sections 
                (id, name, description, display_order, color, icon, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                section["id"],
                section["name"],
                section["description"],
                section["display_order"],
                section["color"],
                section["icon"]
            ))
        logger.info(f"Loaded {len(sections)} sections")
        
    def load_areas(self, conn: sqlite3.Connection, areas: List[Dict[str, Any]]) -> None:
        """Load areas data"""
        for area in areas:
            conn.execute("""
                INSERT OR REPLACE INTO areas 
                (id, section_id, name, description, display_order, 
                 timeline_l1_l2, timeline_l2_l3, timeline_l3_l4, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                area["id"],
                area["section_id"],
                area["name"],
                area["description"],
                area["display_order"],
                area.get("timeline_l1_l2"),
                area.get("timeline_l2_l3"),
                area.get("timeline_l3_l4")
            ))
        logger.info(f"Loaded {len(areas)} areas")
        
    def load_questions(self, conn: sqlite3.Connection, questions: List[Dict[str, Any]]) -> None:
        """Load questions data"""
        for question in questions:
            conn.execute("""
                INSERT OR REPLACE INTO questions 
                (id, area_id, question, level_1_desc, level_2_desc, level_3_desc, level_4_desc,
                 display_order, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                question["id"],
                question["area_id"],
                question["question"],
                question["level_1_desc"],
                question["level_2_desc"],
                question["level_3_desc"],
                question["level_4_desc"],
                question["display_order"],
                question.get("is_active", True)
            ))
        logger.info(f"Loaded {len(questions)} questions")
        
    def verify_database(self) -> bool:
        """Verify database was created successfully"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check that all main tables exist and have data
                tables_to_check = [
                    ("sections", 4),  # Should have 4 sections
                    ("areas", 23),    # Should have 23 areas  
                    ("questions", 23) # Should have 23 questions
                ]
                
                for table_name, expected_count in tables_to_check:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                    actual_count = cursor.fetchone()[0]
                    
                    if actual_count != expected_count:
                        logger.error(f"Table {table_name}: expected {expected_count}, got {actual_count}")
                        return False
                    else:
                        logger.info(f"Table {table_name}: {actual_count} records ✓")
                        
                # Verify foreign key relationships
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM areas a 
                    JOIN sections s ON a.section_id = s.id
                """)
                area_section_links = cursor.fetchone()[0]
                
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM questions q 
                    JOIN areas a ON q.area_id = a.id
                """)
                question_area_links = cursor.fetchone()[0]
                
                logger.info(f"Foreign key relationships: {area_section_links} area-section links, {question_area_links} question-area links ✓")
                
                return True
                
        except Exception as e:
            logger.error(f"Database verification failed: {str(e)}")
            return False
            
    def run_full_initialization(self) -> bool:
        """Run complete database initialization process"""
        try:
            logger.info("Starting AFS Assessment Framework database initialization")
            
            # Create database and run migrations
            self.create_database()
            
            # Load seed data
            self.seed_database()
            
            # Verify everything worked
            if self.verify_database():
                logger.info("Database initialization completed successfully! ✓")
                return True
            else:
                logger.error("Database verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize AFS Assessment Framework database")
    parser.add_argument("--db-path", default="app.db", help="Database file path")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing database")
    
    args = parser.parse_args()
    
    initializer = DatabaseInitializer(args.db_path)
    
    if args.verify_only:
        if initializer.verify_database():
            print("Database verification passed ✓")
            return 0
        else:
            print("Database verification failed ✗")
            return 1
    else:
        if initializer.run_full_initialization():
            print("Database initialization completed successfully ✓")
            return 0
        else:
            print("Database initialization failed ✗")
            return 1


if __name__ == "__main__":
    exit(main())
