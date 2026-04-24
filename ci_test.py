#!/usr/bin/env python3
"""
CI Test Script for Neon Database Branches
Run database tests and API validation for CI/CD pipelines.
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from database import Base

def test_database_connection():
    """Test database connection and basic functionality"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not set")
        return False

    try:
        print("🔄 Testing database connection...")
        engine = create_engine(db_url)

        # Test basic connection
        with engine.connect() as conn:
            result = conn.execute(text('SELECT 1 as test'))
            if result.fetchone()[0] == 1:
                print("✅ Database connection successful")
            else:
                print("❌ Unexpected query result")
                return False

        # Test table creation
        print("🔄 Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully")

        # Verify tables exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        expected_tables = ['users', 'courses', 'programs', 'enrollments']
        missing_tables = [t for t in expected_tables if t not in tables]

        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False

        print(f"✅ All expected tables present: {len(tables)} tables")

        # Test basic queries
        with engine.connect() as conn:
            # Test users table
            result = conn.execute(text('SELECT COUNT(*) FROM users'))
            user_count = result.fetchone()[0]
            print(f"✅ Users table accessible: {user_count} users")

            # Test courses table
            result = conn.execute(text('SELECT COUNT(*) FROM courses'))
            course_count = result.fetchone()[0]
            print(f"✅ Courses table accessible: {course_count} courses")

        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_api_endpoints():
    """Test basic API endpoints if server is running"""
    try:
        import requests
        import time

        # Try to connect to API
        api_url = os.getenv('API_URL', 'http://localhost:8000')

        print(f"🔄 Testing API endpoints at {api_url}...")

        # Test health endpoint
        response = requests.get(f"{api_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint responding")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False

        # Test programs endpoint
        response = requests.get(f"{api_url}/api/programs/", timeout=10)
        if response.status_code == 200:
            print("✅ Programs API endpoint responding")
        else:
            print(f"❌ Programs API failed: {response.status_code}")
            return False

        return True

    except ImportError:
        print("⚠️  requests library not available, skipping API tests")
        return True
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    print("🚀 CI Database and API Tests")
    print("=" * 40)

    success = True

    # Test database
    if not test_database_connection():
        success = False

    # Test API (if available)
    if not test_api_endpoints():
        success = False

    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()