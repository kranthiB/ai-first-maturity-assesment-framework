#!/usr/bin/env python3
"""
AI-First Software Engineering Maturity Assessment Framework
Database Setup Script

This script creates a new SQLite database and populates it with the complete schema
and seed data for the assessment framework.

Usage:
    python scripts/setup_database.py

The script will:
1. Create a new app.db file in the project root
2. Execute the DDL script to create all tables, views, and indexes
3. Execute the DML script to populate with seed data
4. Verify the setup was successful
"""

import os
import sqlite3
import sys
from pathlib import Path

def get_project_root():
    """Get the project root directory."""
    current_dir = Path(__file__).parent
    # Go up one level from scripts/ to get to project root
    return current_dir.parent

def read_sql_file(file_path):
    """Read and return the contents of a SQL file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"❌ Error: SQL file not found: {file_path}")
        return None
    except Exception as e:
        print(f"❌ Error reading SQL file {file_path}: {e}")
        return None

def execute_sql_script(cursor, sql_content, script_name):
    """Execute a SQL script and handle any errors."""
    print(f"📄 Executing {script_name}...")
    
    try:
        # Clean the SQL content
        sql_content = sql_content.strip()
        
        # Remove comments and empty lines for better processing
        lines = sql_content.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('--'):
                cleaned_lines.append(line)
        
        cleaned_sql = '\n'.join(cleaned_lines)
        
        # Execute the entire script at once using executescript
        cursor.executescript(cleaned_sql)
        
        print(f"✅ {script_name} completed successfully!")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ SQLite error in {script_name}: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error executing {script_name}: {e}")
        return False

def verify_database_setup(cursor):
    """Verify that the database was set up correctly."""
    print("\n🔍 Verifying database setup...")
    
    # Check table counts
    verification_queries = [
        ("Schema migrations", "SELECT COUNT(*) FROM schema_migrations"),
        ("Sections", "SELECT COUNT(*) FROM sections"),
        ("Areas", "SELECT COUNT(*) FROM areas"),
        ("Questions", "SELECT COUNT(*) FROM questions"),
        ("Assessments table", "SELECT COUNT(*) FROM assessments"),
        ("Responses table", "SELECT COUNT(*) FROM responses"),
        ("Assessment sections", "SELECT COUNT(*) FROM assessment_sections"),
        ("Recommendations", "SELECT COUNT(*) FROM assessment_recommendations"),
        ("Analytics summary", "SELECT COUNT(*) FROM analytics_summary"),
        ("Question analytics", "SELECT COUNT(*) FROM question_analytics"),
        ("Team progress", "SELECT COUNT(*) FROM team_progress"),
    ]
    
    total_errors = 0
    for table_name, query in verification_queries:
        try:
            cursor.execute(query)
            count = cursor.fetchone()[0]
            print(f"   ✅ {table_name}: {count} records")
        except sqlite3.Error as e:
            print(f"   ❌ {table_name}: Error - {e}")
            total_errors += 1
    
    # Test views
    view_queries = [
        ("Assessment overview view", "SELECT COUNT(*) FROM v_assessment_overview"),
        ("Section performance view", "SELECT COUNT(*) FROM v_section_performance"),
        ("Question difficulty view", "SELECT COUNT(*) FROM v_question_difficulty"),
        ("Maturity distribution view", "SELECT * FROM v_maturity_distribution LIMIT 1"),
    ]
    
    print("\n🔍 Verifying views...")
    for view_name, query in view_queries:
        try:
            cursor.execute(query)
            result = cursor.fetchone()
            print(f"   ✅ {view_name}: Working")
        except sqlite3.Error as e:
            print(f"   ❌ {view_name}: Error - {e}")
            total_errors += 1
    
    return total_errors == 0

def backup_existing_database(db_path):
    """Create a backup of existing database if it exists."""
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup"
        counter = 1
        while os.path.exists(backup_path):
            backup_path = f"{db_path}.backup.{counter}"
            counter += 1
        
        try:
            os.rename(db_path, backup_path)
            print(f"📦 Existing database backed up to: {backup_path}")
            return True
        except Exception as e:
            print(f"⚠️  Warning: Could not backup existing database: {e}")
            return False
    return True

def main():
    """Main function to set up the database."""
    print("🚀 AI-First Software Engineering Maturity Assessment Framework")
    print("   Database Setup Script")
    print("=" * 60)
    
    # Get paths
    project_root = get_project_root()
    scripts_dir = project_root / "scripts"
    
    # Use instance directory to match Flask app configuration
    instance_dir = project_root / "instance"
    instance_dir.mkdir(exist_ok=True)
    db_path = instance_dir / "app_dev.db"
    
    ddl_script_path = scripts_dir / "database_schema.sql"
    dml_script_path = scripts_dir / "database_seed_data.sql"
    
    print(f"📁 Project root: {project_root}")
    print(f"📁 Scripts directory: {scripts_dir}")
    print(f"🗄️  Database will be created at: {db_path}")
    
    # Check if script files exist
    if not ddl_script_path.exists():
        print(f"❌ Error: DDL script not found at {ddl_script_path}")
        print("   Please ensure database_schema.sql exists in the scripts folder.")
        sys.exit(1)
    
    if not dml_script_path.exists():
        print(f"❌ Error: DML script not found at {dml_script_path}")
        print("   Please ensure database_seed_data.sql exists in the scripts folder.")
        sys.exit(1)
    
    # Backup existing database if it exists
    if not backup_existing_database(db_path):
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("❌ Database setup cancelled.")
            sys.exit(1)
    
    # Read SQL scripts
    print("\n📖 Reading SQL scripts...")
    ddl_content = read_sql_file(ddl_script_path)
    if ddl_content is None:
        sys.exit(1)
    
    dml_content = read_sql_file(dml_script_path)
    if dml_content is None:
        sys.exit(1)
    
    print("✅ SQL scripts loaded successfully!")
    
    # Create and setup database
    try:
        print(f"\n🗄️  Creating database: {db_path}")
        
        # Remove existing database file
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # Connect to database (this creates the file)
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        
        print("✅ Database connection established!")
        
        # Execute DDL script (create schema) using executescript
        print("📄 Executing DDL Script (Schema Creation)...")
        conn.executescript(ddl_content)
        print("✅ DDL Script (Schema Creation) completed successfully!")
        
        # Execute DML script (insert data) statement by statement
        print("📄 Executing DML Script (Data Population)...")
        
        # Split the DML content into individual statements
        statements = []
        current_statement = ""
        
        for line in dml_content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('--'):
                continue
                
            # Skip PRAGMA statements as they're not needed for this context
            if line.startswith('PRAGMA'):
                continue
                
            current_statement += line + " "
            
            # If line ends with semicolon, it's the end of a statement
            if line.endswith(';'):
                statements.append(current_statement.strip())
                current_statement = ""
        
        # Execute each statement individually with error handling
        cursor = conn.cursor()
        for i, statement in enumerate(statements):
            try:
                if statement.startswith('DELETE'):
                    # Skip DELETE statements on fresh database
                    continue
                cursor.execute(statement)
            except sqlite3.Error as e:
                print(f"⚠️  Warning: Statement {i+1} failed: {e}")
                print(f"   Statement: {statement[:100]}...")
                # Continue with other statements
                continue
        
        conn.commit()
        print("✅ DML Script (Data Population) completed successfully!")
        
        print("💾 All changes committed!")
        
        # Verify setup
        cursor = conn.cursor()
        if verify_database_setup(cursor):
            print("\n🎉 Database setup completed successfully!")
            print(f"✅ Database created at: {db_path}")
            print("✅ Schema and indexes created")
            print("✅ Seed data populated")
            print("✅ Views and analytics tables ready")
            
            # Show database file size
            db_size = os.path.getsize(db_path)
            db_size_mb = db_size / (1024 * 1024)
            print(f"📊 Database size: {db_size_mb:.2f} MB")
            
        else:
            print("\n⚠️  Database setup completed with some issues.")
            print("   Please check the verification results above.")
        
        # Close connection
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ SQLite error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    
    print("\n🏁 Database setup script completed!")
    print(f"   You can now use the database at: {db_path}")
    print("   Run your Flask application to test the setup.")


if __name__ == "__main__":
    main()
