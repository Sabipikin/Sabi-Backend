#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/sabipikin/Documents/Sabi Educate/sabipath/backend')

from database import SessionLocal, engine
from models import Base, User, AdminUser, Role
from auth import hash_password

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Check if super admin role exists
    super_admin_role = db.query(Role).filter(Role.name == "super_admin").first()
    if not super_admin_role:
        super_admin_role = Role(
            name="super_admin",
            description="Super Administrator with full system access"
        )
        db.add(super_admin_role)
        db.commit()
        print("✓ Created super_admin role")
    
    # Check if user already exists
    user = db.query(User).filter(User.email == "sabipikin247@gmail.com").first()
    if not user:
        user = User(
            email="sabipikin247@gmail.com",
            full_name="Super Administrator",
            hashed_password=hash_password("favCaleb@45!*#"),
            is_active=True
        )
        db.add(user)
        db.commit()
        print(f"✓ Created User with ID: {user.id}")
    else:
        # Update password if user exists
        user.hashed_password = hash_password("favCaleb@45!*#")
        db.commit()
        print(f"✓ Updated existing User with ID: {user.id}")
    
    # Check if admin user already exists
    admin_user = db.query(AdminUser).filter(AdminUser.username == "superadmin").first()
    if not admin_user:
        admin_user = AdminUser(
            user_id=user.id,
            role_id=super_admin_role.id,
            username="superadmin",
            department=None,
            theme_preference="dark",
            is_verified=True,
            created_by=None
        )
        db.add(admin_user)
        db.commit()
        print(f"✓ Created AdminUser with ID: {admin_user.id}")
    else:
        admin_user.user_id = user.id
        admin_user.role_id = super_admin_role.id
        db.commit()
        print(f"✓ Updated existing AdminUser with ID: {admin_user.id}")
    
    print(f"\n✅ Super Admin Account Ready!")
    print(f"   Email: sabipikin247@gmail.com")
    print(f"   Username: superadmin")
    print(f"   Role: Super Admin")
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
