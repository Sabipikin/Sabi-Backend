#!/usr/bin/env python3
"""
Neon Database Setup and Testing Script
Run this script to test your Neon database connection and initialize tables.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test the database connection"""
    try:
        from sqlalchemy import create_engine, text
        db_url = os.getenv('DATABASE_URL')

        if not db_url:
            print("❌ DATABASE_URL not found in environment variables")
            return False

        if '<' in db_url or '>' in db_url:
            print("❌ DATABASE_URL still contains placeholder values")
            print("Please update your .env file with the real Neon connection string")
            return False

        print("🔄 Testing database connection...")
        engine = create_engine(db_url)

        with engine.connect() as conn:
            result = conn.execute(text('SELECT 1 as test'))
            row = result.fetchone()
            if row and row[0] == 1:
                print("✅ Database connection successful!")
                return True
            else:
                print("❌ Unexpected query result")
                return False

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def create_tables():
    """Create all database tables"""
    try:
        from database import engine, Base
        print("🔄 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

def main():
    print("🚀 Neon Database Setup and Testing")
    print("=" * 40)

    # Test connection
    if not test_connection():
        print("\n💡 To fix connection issues:")
        print("1. Update backend/.env with your Neon connection string")
        print("2. Make sure sslmode=require is included")
        print("3. Verify your Neon project is active")
        sys.exit(1)

    # Create tables
    if not create_tables():
        print("\n💡 Table creation failed. Check your database permissions.")
        sys.exit(1)

    print("\n🎉 Neon database is ready!")
    print("You can now start the backend server:")
    print("cd backend && python3 main.py")

if __name__ == "__main__":
    main()