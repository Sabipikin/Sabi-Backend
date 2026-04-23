#!/usr/bin/env python3
"""Setup test data for both frontend and admin systems"""

from database import engine, SessionLocal, Base
from models import User, AdminUser, Role
from auth import hash_password

# Setup database
Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    # Clear existing data
    db.query(AdminUser).delete()
    db.query(User).delete()
    db.query(Role).delete()
    db.commit()

    # Create roles
    super_admin_role = Role(name='super_admin', description='Super Administrator')
    db.add(super_admin_role)
    db.commit()
    db.refresh(super_admin_role)

    # Create REGULAR USER (for frontend login)
    regular_user = User(
        email='user@example.com',
        full_name='Regular User',
        hashed_password=hash_password('userpass123'),
        region='uk',
        is_active=True
    )
    db.add(regular_user)
    db.commit()
    db.refresh(regular_user)
    print(f"✓ Regular user created: user@example.com / userpass123")

    # Create ADMIN USER (for admin portal login)
    admin_user_obj = User(
        email='admin@example.com',
        full_name='Admin User',
        hashed_password=hash_password('adminpass123'),
        region='uk',
        is_active=True
    )
    db.add(admin_user_obj)
    db.commit()
    db.refresh(admin_user_obj)

    # Create admin record
    admin_record = AdminUser(
        user_id=admin_user_obj.id,
        role_id=super_admin_role.id,
        username='adminuser',
        department='Management',
        is_verified=True
    )
    db.add(admin_record)
    db.commit()
    print(f"✓ Admin user created: admin@example.com / adminpass123")

    print(f"\n✅ Test data setup complete!")
    print(f"\nFrontend Login (http://localhost:3000):")
    print(f"  Email: user@example.com")
    print(f"  Password: userpass123")
    print(f"\nAdmin Login (http://localhost:3002):")
    print(f"  Email: admin@example.com")
    print(f"  Password: adminpass123")

finally:
    db.close()
