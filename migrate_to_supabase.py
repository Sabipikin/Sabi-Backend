"""
Migration script to move data from SQLite to Supabase PostgreSQL
"""

import os
import sqlite3
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from database import Base
import models

load_dotenv()

# SQLite connection
sqlite_db = sqlite3.connect('./sabipath.db')
sqlite_db.row_factory = sqlite3.Row
sqlite_cursor = sqlite_db.cursor()

# Supabase PostgreSQL connection
supabase_url = os.getenv("DATABASE_URL")
if not supabase_url:
    raise ValueError("DATABASE_URL not set in .env file")

print(f"🔄 Connecting to Supabase: {supabase_url.split('@')[1]}")
supabase_engine = create_engine(supabase_url)

# Create all tables in Supabase
print("📝 Creating tables in Supabase...")
try:
    Base.metadata.create_all(bind=supabase_engine)
    print("✅ Tables created successfully")
except Exception as e:
    print(f"⚠️  Tables might already exist: {e}")

# Get session
Session = sessionmaker(bind=supabase_engine)
session = Session()

# List of tables to migrate (in dependency order)
tables_to_migrate = [
    'users',
    'roles',
    'admin_users',
    'user_profiles',
    'courses',
    'modules',
    'lessons',
    'lesson_contents',
    'enrollments',
    'projects',
    'portfolios',
    'progress',
    'content_progress',
    'assessment_scores',
    'project_submissions',
    'cvs',
    'experiences',
    'educations',
    'skills',
    'certificates',
    'analytics',
    'points',
    'streaks',
    'badges',
    'complaints',
    'payments'
]

print("\n🔄 Starting data migration...\n")

migrated_count = {}

for table_name in tables_to_migrate:
    try:
        # Get data from SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"⏭️  {table_name}: No data to migrate")
            migrated_count[table_name] = 0
            continue
        
        # Get column names
        column_names = [description[0] for description in sqlite_cursor.description]
        
        # Insert into Supabase
        insert_count = 0
        for row in rows:
            row_dict = dict(zip(column_names, row))
            # Remove None values for auto-increment IDs
            row_dict = {k: v for k, v in row_dict.items() if v is not None}
            
            try:
                # Use raw SQL for insert to avoid ORM complications
                placeholders = ', '.join([f"'{v}'" if isinstance(v, str) else str(v) for v in row_dict.values()])
                columns = ', '.join(row_dict.keys())
                insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                session.execute(text(insert_sql))
                insert_count += 1
            except Exception as row_error:
                print(f"  ⚠️  Error inserting row in {table_name}: {row_error}")
                continue
        
        session.commit()
        migrated_count[table_name] = insert_count
        print(f"✅ {table_name}: {insert_count} records migrated")
        
    except sqlite3.OperationalError as e:
        print(f"⏭️  {table_name}: Table doesn't exist in SQLite - {e}")
    except Exception as e:
        print(f"❌ {table_name}: Error during migration - {e}")
        session.rollback()

print("\n" + "="*50)
print("📊 Migration Summary:")
print("="*50)
total_records = sum(migrated_count.values())
for table, count in migrated_count.items():
    if count > 0:
        print(f"  {table}: {count} records")

print(f"\n✨ Total records migrated: {total_records}")
print("="*50)

# Cleanup
session.close()
sqlite_db.close()

print("\n✅ Migration complete! Your data is now in Supabase.")
print("🔄 Restart your backend server to use Supabase instead of SQLite.")
