#!/usr/bin/env python
"""Bootstrap script to create test users and admin accounts"""

from database import engine, Base, SessionLocal
from models import User, AdminUser, Role
from auth import hash_password

# Create all tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Create super_admin role if it doesn't exist
    admin_role = db.query(Role).filter(Role.name == 'super_admin').first()
    if not admin_role:
        admin_role = Role(
            name='super_admin',
            description='Super Administrator with full system access'
        )
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)
        print('✓ Super admin role created')
    else:
        print('✓ Super admin role already exists')

    # Create super admin user
    super_admin = db.query(AdminUser).join(Role).filter(
        Role.name == 'super_admin'
    ).first()
    
    if not super_admin:
        admin_user = User(
            email='admin@example.com',
            full_name='Super Admin',
            hashed_password=hash_password('AdminPassword123'),
            region='uk',
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        admin_record = AdminUser(
            user_id=admin_user.id,
            role_id=admin_role.id,
            username='superadmin',
            department='Management',
            is_verified=True
        )
        db.add(admin_record)
        db.commit()
        print('✓ Super admin created: admin@example.com / AdminPassword123')
    else:
        print('✓ Super admin already exists')

    # Create a regular test user if it doesn't exist
    test_user = db.query(User).filter(User.email == 'test@example.com').first()
    if not test_user:
        test_user = User(
            email='test@example.com',
            full_name='Test User',
            hashed_password=hash_password('password123'),
            region='uk',
            is_active=True
        )
        db.add(test_user)
        db.commit()
        print('✓ Test user created: test@example.com / password123')
    else:
        print('✓ Test user already exists')

    print('\n✅ Bootstrap complete!')
    print('\nYou can now login with:')
    print('  Admin: admin@example.com / AdminPassword123')
    print('  User: test@example.com / password123')

finally:
    db.close()
