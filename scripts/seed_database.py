# scripts/seed_database.py
#!/usr/bin/env python3
"""
AFS Assessment Framework - Database Seeding Script
Handles database initialization, migration execution, and data seeding.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import sqlite3
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseSeeder:
    """Database initialization and seeding manager"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.project_root = Path(__file__).parent.parent
        self.migrations_dir = self.project_root / 'data' / 'migrations'
        self.seeds_dir = self.project_root / 'data' / 'seeds'
        self.database_url = database_url or self._get_database_url()
        self.connection = None
        
    def seed_database(self, force: bool = False) -> bool:
        """Complete database seeding process"""
        logger.info("Starting database seeding process...")
        
        try:
            self._connect_database()
            
            if force:
                logger.info("Force mode: Dropping all tables")
                self._drop_all_tables()
            
            self._run_migrations()
            self._seed_reference_data()
            self._verify_seeding()
            
            logger.info("Database seeding completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Database seeding failed: {str(e)}")
            return False
        finally:
            if self.connection:
                self.connection.close()
    
    def _get_database_url(self) -> str:
        """Get database URL from environment or default"""
        try:
            from dotenv import load_dotenv
            load_dotenv(self.project_root / '.env')
            return os.getenv('DATABASE_URL', 'sqlite:///data/afs_assessment.db')
        except ImportError:
            return 'sqlite:///data/afs_assessment.db'
    
    def _connect_database(self) -> None:
        """Establish database connection"""
        logger.info("Connecting to database...")
        
        if 'sqlite' in self.database_url.lower() or self.database_url.startswith('sqlite'):
            # Extract database file path
            if ':///' in self.database_url:
                db_path = self.database_url.split(':///', 1)[1]
            else:
                db_path = self.database_url
            
            # Ensure database directory exists
            db_file = self.project_root / db_path
            db_file.parent.mkdir(parents=True, exist_ok=True)
            
            self.connection = sqlite3.connect(str(db_file))
            self.connection.execute("PRAGMA foreign_keys = ON")
        else:
            raise NotImplementedError(f"Database type not implemented: {self.database_url}")
        
        logger.info("Database connection established")
    
    def _drop_all_tables(self) -> None:
        """Drop all tables for fresh install"""
        logger.info("Dropping all existing tables...")
        
        # Get list of all tables
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        tables = cursor.fetchall()
        
        # Drop tables in reverse dependency order
        drop_order = [
            'responses', 'assessment_recommendations', 'assessment_sections',
            'assessment_exports', 'assessments', 'questions', 'areas',
            'sections', 'question_analytics', 'analytics_summary', 
            'team_progress', 'schema_migrations'
        ]
        
        for table_name in drop_order:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            except Exception as e:
                logger.warning(f"Could not drop table {table_name}: {e}")
        
        self.connection.commit()
        logger.info("All tables dropped")
    
    def _run_migrations(self) -> None:
        """Execute database migrations"""
        logger.info("Running database migrations...")
        
        migration_files = sorted(self.migrations_dir.glob('*.sql'))
        
        for migration_file in migration_files:
            logger.info(f"Executing migration: {migration_file.name}")
            
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            # Execute migration (split on statement separator for SQLite)
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement.upper().startswith(('CREATE', 'ALTER', 'INSERT', 'DROP')):
                    try:
                        self.connection.execute(statement)
                    except Exception as e:
                        logger.warning(f"Migration statement failed: {e}")
                        logger.debug(f"Statement: {statement[:100]}...")
            
            self.connection.commit()
        
        logger.info("Migrations completed")
    
    def _seed_reference_data(self) -> None:
        """Load reference data from seed files"""
        logger.info("Loading reference data...")
        
        # Load sections
        self._load_sections()
        
        # Load areas
        self._load_areas()
        
        # Load questions
        self._load_questions()
        
        logger.info("Reference data loaded successfully")
    
    def _load_sections(self) -> None:
        """Load sections from seed data"""
        sections_file = self.seeds_dir / 'sections.json'
        
        if not sections_file.exists():
            logger.warning("Sections seed file not found")
            return
        
        with open(sections_file, 'r') as f:
            data = json.load(f)
        
        cursor = self.connection.cursor()
        
        for section in data.get('sections', []):
            cursor.execute("""
                INSERT OR REPLACE INTO sections 
                (id, name, description, display_order, color, icon)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                section['id'],
                section['name'],
                section['description'],
                section['display_order'],
                section.get('color', '#3b82f6'),
                section.get('icon', 'fas fa-cog')
            ))
        
        self.connection.commit()
        logger.info(f"Loaded {len(data.get('sections', []))} sections")
    
    def _load_areas(self) -> None:
        """Load areas from seed data"""
        areas_file = self.seeds_dir / 'areas.json'
        
        if not areas_file.exists():
            logger.warning("Areas seed file not found")
            return
        
        with open(areas_file, 'r') as f:
            data = json.load(f)
        
        cursor = self.connection.cursor()
        
        for area in data.get('areas', []):
            cursor.execute("""
                INSERT OR REPLACE INTO areas 
                (id, section_id, name, description, display_order, 
                 timeline_l1_l2, timeline_l2_l3, timeline_l3_l4)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                area['id'],
                area['section_id'],
                area['name'],
                area['description'],
                area['display_order'],
                area.get('timeline_l1_l2'),
                area.get('timeline_l2_l3'),
                area.get('timeline_l3_l4')
            ))
        
        self.connection.commit()
        logger.info(f"Loaded {len(data.get('areas', []))} areas")
    
    def _load_questions(self) -> None:
        """Load questions from seed data"""
        questions_file = self.seeds_dir / 'questions.json'
        
        if not questions_file.exists():
            logger.warning("Questions seed file not found")
            return
        
        with open(questions_file, 'r') as f:
            data = json.load(f)
        
        cursor = self.connection.cursor()
        
        for question in data.get('questions', []):
            cursor.execute("""
                INSERT OR REPLACE INTO questions 
                (id, area_id, question, level_1_desc, level_2_desc, 
                 level_3_desc, level_4_desc, display_order, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                question['id'],
                question['area_id'],
                question['question'],
                question['level_1_desc'],
                question['level_2_desc'],
                question['level_3_desc'],
                question['level_4_desc'],
                question['display_order'],
                question.get('is_active', True)
            ))
        
        self.connection.commit()
        logger.info(f"Loaded {len(data.get('questions', []))} questions")
    
    def _verify_seeding(self) -> None:
        """Verify that seeding was successful"""
        logger.info("Verifying database seeding...")
        
        cursor = self.connection.cursor()
        
        # Check record counts
        tables_to_check = ['sections', 'areas', 'questions']
        
        for table in tables_to_check:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info(f"{table}: {count} records")
            
            if count == 0:
                logger.warning(f"No records found in {table}")
        
        # Verify data integrity
        cursor.execute("""
            SELECT COUNT(*) FROM areas a 
            LEFT JOIN sections s ON a.section_id = s.id 
            WHERE s.id IS NULL
        """)
        orphaned_areas = cursor.fetchone()[0]
        
        if orphaned_areas > 0:
            logger.warning(f"Found {orphaned_areas} orphaned areas")
        
        cursor.execute("""
            SELECT COUNT(*) FROM questions q 
            LEFT JOIN areas a ON q.area_id = a.id 
            WHERE a.id IS NULL
        """)
        orphaned_questions = cursor.fetchone()[0]
        
        if orphaned_questions > 0:
            logger.warning(f"Found {orphaned_questions} orphaned questions")
        
        logger.info("Database verification completed")

def main():
    """Main entry point for database seeding"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AFS Database Seeding Script')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Force seeding (drop all existing data)')
    parser.add_argument('--database-url', '-d', 
                       help='Database URL (overrides environment)')
    
    args = parser.parse_args()
    
    seeder = DatabaseSeeder(args.database_url)
    success = seeder.seed_database(args.force)
    
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
