#!/usr/bin/env python3
"""
Verify the super admin was created in Neon database
"""
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import User, AdminUser, Role


def verify_superadmin():
    """Verify super admin exists in Neon"""
    
    db = SessionLocal()
    
    try:
        # Get the user
        user = db.query(User).filter(User.email == "sabipikin247@gmail.com").first()
        if not user:
            print("❌ User not found in Neon database")
            return False
        
        # Get the admin
        admin = db.query(AdminUser).filter(AdminUser.user_id == user.id).first()
        if not admin:
            print("❌ Admin user not found in Neon database")
            return False
        
        # Get the role
        role = db.query(Role).filter(Role.id == admin.role_id).first()
        
        print("✅ SUPER ADMIN VERIFIED IN NEON DATABASE")
        print("="*60)
        print(f"User ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Full Name: {user.full_name}")
        print(f"Is Active: {user.is_active}")
        print(f"Region: {user.region}")
        print(f"Created At: {user.created_at}")
        print("\nAdmin Details:")
        print(f"Admin ID: {admin.id}")
        print(f"Username: {admin.username}")
        print(f"Role: {role.name if role else 'N/A'}")
        print(f"Is Verified: {admin.is_verified}")
        print(f"Department: {admin.department}")
        print(f"Theme Preference: {admin.theme_preference}")
        print(f"Created At: {admin.created_at}")
        print("="*60)
        print("✅ All data successfully stored in Neon!")
        print("\nLogin Credentials:")
        print(f"Email: {user.email}")
        print(f"Password: favCaleb@45!*#")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying super admin: {str(e)}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    verify_superadmin()
