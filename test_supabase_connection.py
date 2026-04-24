import psycopg2
import sys

try:
    print("🔄 Attempting to connect to Supabase...")
    conn = psycopg2.connect(
        host="db.owwanbixzrvehkesmyao.supabase.co",
        database="postgres",
        user="postgres",
        password="favCaleb@45!*#",
        port=5432,
        connect_timeout=5
    )
    print("✅ Connection successful!")
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"📌 PostgreSQL version: {version[0][:80]}...")
    conn.close()
    print("✅ Test complete - Supabase is reachable!")
except Exception as e:
    print(f"❌ Connection failed: {type(e).__name__}: {e}")
    sys.exit(1)
