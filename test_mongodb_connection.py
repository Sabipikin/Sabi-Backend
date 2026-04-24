import pymongo
import sys

try:
    print("🔄 Attempting to connect to MongoDB Atlas...")
    uri = "mongodb+srv://sabipikin:Kettle452026@cluster0.jyy2mrx.mongodb.net/"
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
    
    # Test connection
    client.admin.command('ping')
    print("✅ Connection successful!")
    
    # Get server info
    info = client.server_info()
    print(f"📌 MongoDB version: {info['version']}")
    
    # List databases
    databases = client.list_database_names()
    print(f"📊 Existing databases: {databases}")
    
    client.close()
    print("✅ Test complete - MongoDB Atlas is reachable!")
except Exception as e:
    print(f"❌ Connection failed: {type(e).__name__}: {e}")
    sys.exit(1)
