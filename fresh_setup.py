#!/usr/bin/env python3
"""Fresh setup - create clean database with test credentials"""

from database import engine, SessionLocal, Base
from models import User, UserProfile, AdminUser, Role
from auth import hash_password

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Create a role
admin_role = Role(name='super_admin', description='Super Admin')
db.add(admin_role)
db.commit()
db.refresh(admin_role)

# Create regular user
regular_user = User(
    email='user@test.com',
    full_name='Test User',
    hashed_password=hash_password('password'),
    region='uk',
    is_active=True
)
db.add(regular_user)
db.commit()
db.refresh(regular_user)

# Create admin user
admin_user_obj = User(
    email='admin@test.com',
    full_name='Admin',
    hashed_password=hash_password('admin'),
    region='uk',
    is_active=True
)
db.add(admin_user_obj)
db.commit()
db.refresh(admin_user_obj)

admin_record = AdminUser(
    user_id=admin_user_obj.id,
    role_id=admin_role.id,
    username='admin',
    is_verified=True
)
db.add(admin_record)
db.commit()

print("✓ Database ready")
print("\n🔑 Test Credentials:")
print("  User: user@test.com / password")
print("  Admin: admin@test.com / admin")

db.close()
