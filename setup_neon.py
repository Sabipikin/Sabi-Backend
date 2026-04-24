#!/usr/bin/env python3
"""
Helper script to update .env with Neon connection string
"""

import os
import re

def update_env_file():
    env_path = '.env'

    # Read current .env
    with open(env_path, 'r') as f:
        content = f.read()

    print("Current DATABASE_URL in .env:")
    current_url = re.search(r'DATABASE_URL=(.+)', content)
    if current_url:
        print(f"  {current_url.group(1)}")

    print("\n" + "="*50)
    print("📝 UPDATE YOUR .ENV FILE")
    print("="*50)
    print("1. Go to https://console.neon.tech")
    print("2. Select your project (Sabipikin/Sabi-Educate)")
    print("3. Go to 'Connection Details' or 'Dashboard'")
    print("4. Copy the connection string")
    print("5. Replace the DATABASE_URL line in backend/.env")
    print("")
    print("Example connection string format:")
    print("postgresql://neondb_owner:AbCdEfGhIjKl@ep-cool-mode-123456.us-east-1.aws.neon.tech/neondb?sslmode=require")
    print("")
    print("Your .env should look like:")
    print("DATABASE_URL=postgresql://[your-connection-string-here]?sslmode=require")
    print("DEBUG=False")
    print("")
    print("❓ Do you have your Neon connection string ready?")
    response = input("Enter 'yes' when ready, or 'help' for more guidance: ").strip().lower()

    if response == 'yes':
        new_url = input("Paste your Neon connection string: ").strip()
        if new_url and 'postgresql://' in new_url:
            # Update the .env file
            updated_content = re.sub(
                r'DATABASE_URL=.+',
                f'DATABASE_URL={new_url}',
                content
            )

            with open(env_path, 'w') as f:
                f.write(updated_content)

            print("✅ Updated .env file!")
            print("🔄 Testing connection...")

            # Test the connection
            os.environ['DATABASE_URL'] = new_url
            try:
                from sqlalchemy import create_engine, text
                engine = create_engine(new_url)
                with engine.connect() as conn:
                    result = conn.execute(text('SELECT 1'))
                    print("✅ Database connection successful!")
                    print("🎉 Ready to run: python3 main.py")
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                print("💡 Check your connection string and Neon project status")
        else:
            print("❌ Invalid connection string format")
    elif response == 'help':
        print("\n" + "="*50)
        print("🔍 HOW TO GET YOUR NEON CONNECTION STRING")
        print("="*50)
        print("1. Visit: https://console.neon.tech")
        print("2. Sign in with your account")
        print("3. Find your project: 'Sabipikin/Sabi-Educate'")
        print("4. Click on 'Connection Details' or go to Dashboard")
        print("5. Copy the full connection string")
        print("6. Make sure it includes '?sslmode=require' at the end")
        print("")
        print("If you don't see the connection string:")
        print("- Make sure your project is active")
        print("- Try refreshing the page")
        print("- Check if you have the right permissions")
    else:
        print("Run this script again when you have your connection string ready.")

if __name__ == "__main__":
    update_env_file()