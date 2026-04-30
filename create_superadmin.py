#!/usr/bin/env python3
"""
Script to create a super admin user
"""
import sys
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, User, Role, AdminUser
from auth import hash_password


def create_superadmin(
    email: str,
    password: str,
    full_name: str,
    username: str = None
):
    """Create a super admin user"""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"❌ User with email {email} already exists")
            return False
        
        # Check if admin already exists
        existing_admin = db.query(AdminUser).filter(
            AdminUser.username == (username or email)
        ).first()
        if existing_admin:
            print(f"❌ Admin with username {username or email} already exists")
            return False
        
        # Get or create super_admin role
        role = db.query(Role).filter(Role.name == "super_admin").first()
        if not role:
            role = Role(
                name="super_admin",
                description="Super Administrator with full access",
                permissions="all"
            )
            db.add(role)
            db.commit()
            print("✅ Created super_admin role")
        
        # Create user
        hashed_pwd = hash_password(password)
        user = User(
            email=email,
            hashed_password=hashed_pwd,
            full_name=full_name,
            is_active=True,
            region="uk"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ Created user: {email}")
        
        # Create admin user
        admin_user = AdminUser(
            user_id=user.id,
            role_id=role.id,
            username=username or email,
            department="Management",
            is_verified=True,  # Auto-verify super admin
            theme_preference="dark"
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"✅ Created super admin user: {username or email}")
        
        print("\n" + "="*50)
        print("✅ SUPER ADMIN CREATED SUCCESSFULLY")
        print("="*50)
        print(f"Email: {email}")
        print(f"Username: {username or email}")
        print(f"Full Name: {full_name}")
        print(f"Role: super_admin")
        print(f"Status: Verified")
        print("="*50)
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating super admin: {str(e)}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    # Create super admin for Caleb Leo
    success = create_superadmin(
        email="sabipikin247@gmail.com",
        password="favCaleb@45!*#",
        full_name="Caleb Leo",
        username="caleb_leo"
    )
    
    sys.exit(0 if success else 1)
