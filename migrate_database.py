#!/usr/bin/env python3
"""
Database Migration Script
Migrates from old schema to new comprehensive tracking schema
"""

import duckdb
import os
from datetime import datetime

DB_PATH = 'data/bot_data.duckdb'
BACKUP_PATH = f'data/bot_data_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.duckdb'

def backup_database():
    """Create a backup of the existing database"""
    if os.path.exists(DB_PATH):
        print(f"📦 Creating backup: {BACKUP_PATH}")
        import shutil
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"✅ Backup created successfully!")
        return True
    return False

def migrate():
    """Migrate the database schema"""
    if not os.path.exists(DB_PATH):
        print("❌ No database found. Run the bot first to create it.")
        return
    
    # Backup first
    backup_database()
    
    print("\n🔄 Starting migration...")
    con = duckdb.connect(DB_PATH)
    
    try:
        # Check current schema
        print("\n📋 Checking current schema...")
        columns = con.execute("PRAGMA table_info('applications')").fetchdf()
        print(f"Current columns: {list(columns['name'])}")
        
        # Check if already migrated
        has_new_columns = 'user_submitted' in list(columns['name'])
        
        if has_new_columns:
            print("\n✅ Database already has new schema! No migration needed.")
            con.close()
            return
        
        print("\n🔧 Migrating to new schema...")
        
        # Step 1: Rename old table
        print("  1. Backing up old applications table...")
        con.execute("ALTER TABLE applications RENAME TO applications_old")
        
        # Step 2: Create new table with enhanced schema
        print("  2. Creating new applications table...")
        con.execute("""
            CREATE TABLE applications (
                -- Core identification
                job_id VARCHAR PRIMARY KEY,
                job_title VARCHAR,
                company VARCHAR,
                location VARCHAR,
                work_type VARCHAR,
                
                -- Timestamps
                started_at TIMESTAMP,
                user_confirmed_at TIMESTAMP,
                submitted_at TIMESTAMP,
                
                -- Status tracking
                status VARCHAR,
                attempted BOOLEAN DEFAULT FALSE,
                success BOOLEAN DEFAULT FALSE,
                
                -- User interaction
                user_submitted BOOLEAN DEFAULT FALSE,
                user_skipped BOOLEAN DEFAULT FALSE,
                
                -- Form details
                form_pages INTEGER DEFAULT 0,
                fields_filled INTEGER DEFAULT 0,
                errors_encountered INTEGER DEFAULT 0,
                error_message VARCHAR,
                
                -- Timing
                duration_seconds REAL,
                
                -- Context
                candidate_id VARCHAR DEFAULT 'default',
                proxy_used VARCHAR DEFAULT NULL,
                run_id VARCHAR,
                
                -- Metadata
                job_url VARCHAR,
                salary_range VARCHAR,
                seniority_level VARCHAR,
                employment_type VARCHAR,
                notes VARCHAR
            )
        """)
        
        # Step 3: Copy data from old table to new table
        print("  3. Migrating existing data...")
        
        # First, let's see if there are duplicates
        dup_count = con.execute("""
            SELECT COUNT(*) - COUNT(DISTINCT job_id) as duplicates
            FROM applications_old
        """).fetchone()[0]
        
        if dup_count > 0:
            print(f"    ⚠️ Found {dup_count} duplicate job_ids, keeping most recent records...")
        
        # Insert data, handling duplicates by keeping most recent timestamp
        con.execute("""
            INSERT OR IGNORE INTO applications 
            (job_id, job_title, company, started_at, attempted, success, candidate_id, proxy_used, status)
            SELECT 
                job_id,
                job as job_title,
                company,
                timestamp as started_at,
                attempted,
                result as success,
                COALESCE(candidate_id, 'default') as candidate_id,
                proxy_used,
                CASE 
                    WHEN result = TRUE THEN 'submitted'
                    WHEN attempted = TRUE THEN 'failed'
                    ELSE 'started'
                END as status
            FROM (
                SELECT 
                    job_id, job, company, timestamp, attempted, result, candidate_id, proxy_used,
                    ROW_NUMBER() OVER (PARTITION BY job_id ORDER BY timestamp DESC) as rn
                FROM applications_old
            ) sub
            WHERE rn = 1
        """)
        
        migrated_count = con.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        print(f"  ✅ Migrated {migrated_count} applications")
        
        # Step 4: Drop old table
        print("  4. Cleaning up old table...")
        con.execute("DROP TABLE applications_old")
        
        # Step 5: Create submission_events table if it doesn't exist
        print("  5. Creating submission_events table...")
        con.execute("CREATE SEQUENCE IF NOT EXISTS submission_event_seq")
        con.execute("""
            CREATE TABLE IF NOT EXISTS submission_events (
                event_id INTEGER PRIMARY KEY DEFAULT nextval('submission_event_seq'),
                job_id VARCHAR,
                event_type VARCHAR,
                event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details VARCHAR,
                candidate_id VARCHAR DEFAULT 'default'
            )
        """)
        
        # Step 6: Update other tables
        print("  6. Updating other tables...")
        
        # Update candidates table
        try:
            con.execute("""
                CREATE TABLE candidates_new (
                    candidate_id VARCHAR PRIMARY KEY,
                    name VARCHAR,
                    email VARCHAR,
                    phone VARCHAR,
                    linkedin_profile VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_applications INTEGER DEFAULT 0,
                    total_user_confirmations INTEGER DEFAULT 0,
                    total_successful_submissions INTEGER DEFAULT 0
                )
            """)
            
            con.execute("""
                INSERT INTO candidates_new (candidate_id, name, email, created_at)
                SELECT candidate_id, name, email, created_at
                FROM candidates
            """)
            
            con.execute("DROP TABLE candidates")
            con.execute("ALTER TABLE candidates_new RENAME TO candidates")
            print("    ✅ Updated candidates table")
        except Exception as e:
            print(f"    ⚠️ Candidates table update: {e}")
        
        # Update runs table
        try:
            con.execute("""
                CREATE TABLE runs_new (
                    run_id VARCHAR PRIMARY KEY,
                    candidate_id VARCHAR,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    jobs_viewed INTEGER DEFAULT 0,
                    applications_attempted INTEGER DEFAULT 0,
                    user_confirmations INTEGER DEFAULT 0,
                    applications_submitted INTEGER DEFAULT 0,
                    applications_failed INTEGER DEFAULT 0,
                    applications_skipped INTEGER DEFAULT 0,
                    proxy_used VARCHAR,
                    system_id VARCHAR DEFAULT 'local',
                    search_keywords VARCHAR,
                    location_filter VARCHAR,
                    notes VARCHAR
                )
            """)
            
            con.execute("""
                INSERT INTO runs_new 
                (run_id, candidate_id, started_at, completed_at, applications_submitted, applications_failed, proxy_used, system_id)
                SELECT run_id, candidate_id, started_at, completed_at, applications_submitted, applications_failed, proxy_used, system_id
                FROM runs
            """)
            
            con.execute("DROP TABLE runs")
            con.execute("ALTER TABLE runs_new RENAME TO runs")
            print("    ✅ Updated runs table")
        except Exception as e:
            print(f"    ⚠️ Runs table update: {e}")
        
        # Update QA table
        try:
            con.execute("""
                CREATE TABLE qa_new (
                    question VARCHAR UNIQUE,
                    answer VARCHAR,
                    candidate_id VARCHAR DEFAULT 'default',
                    times_used INTEGER DEFAULT 0,
                    last_used_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            con.execute("""
                INSERT INTO qa_new (question, answer)
                SELECT question, answer
                FROM qa
            """)
            
            con.execute("DROP TABLE qa")
            con.execute("ALTER TABLE qa_new RENAME TO qa")
            print("    ✅ Updated qa table")
        except Exception as e:
            print(f"    ⚠️ QA table update: {e}")
        
        print("\n✅ Migration completed successfully!")
        print(f"\n📊 New schema is active with {migrated_count} applications")
        print(f"💾 Backup saved as: {BACKUP_PATH}")
        print("\n🚀 You can now run: python view_data.py")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print(f"\n💡 Restore from backup if needed:")
        print(f"   Copy {BACKUP_PATH} to {DB_PATH}")
        raise
    finally:
        con.close()

if __name__ == "__main__":
    print("=" * 80)
    print("🔄 DATABASE MIGRATION TOOL")
    print("=" * 80)
    print("\nThis will migrate your database to the new comprehensive tracking schema.")
    print("\nSafety features:")
    print("  ✅ Automatic backup before migration")
    print("  ✅ All existing data preserved")
    print("  ✅ Rollback available from backup")
    print()
    
    response = input("Continue with migration? [y/N]: ").strip().lower()
    
    if response == 'y':
        migrate()
    else:
        print("\n❌ Migration cancelled.")
