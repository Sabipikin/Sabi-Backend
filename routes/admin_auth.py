"""
Admin-specific authentication routes
Completely separate from user authentication to avoid confusion
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User, AdminUser, Role
from schemas import AdminUserCreate, AdminUserResponse, Token
from auth import hash_password, verify_password, create_access_token, decode_access_token
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["admin-auth"])
security = HTTPBearer()


class AdminLoginRequest(BaseModel):
    email: str
    password: str


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated admin user and verify their role"""
    token = credentials.credentials
    email = decode_access_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive",
        )
    
    # Check if user is an admin
    admin_user = db.query(AdminUser).filter(AdminUser.user_id == user.id).first()
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an admin user",
        )
    
    if not admin_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account not verified",
        )
    
    return admin_user


@router.post("/login")
async def admin_login(
    login_data: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """Admin-only login endpoint"""
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    
    # Verify password
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive",
        )
    
    # Check if user is an admin
    admin_user = db.query(AdminUser).filter(AdminUser.user_id == user.id).first()
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not an admin account",
        )
    
    # Get role name
    role = db.query(Role).filter(Role.id == admin_user.role_id).first()
    role_name = role.name if role else "super_admin"
    
    # Create admin token
    access_token = create_access_token(data={"sub": user.email})
    
    # Build response with role name included
    admin_response = AdminUserResponse.from_orm(admin_user).dict()
    admin_response["role_name"] = role_name
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin_user": admin_response
    }


@router.get("/me", response_model=AdminUserResponse)
async def get_current_admin_info(
    admin: AdminUser = Depends(get_current_admin)
):
    """Get current logged-in admin info"""
    return admin


@router.post("/bootstrap-super-admin", response_model=AdminUserResponse)
async def bootstrap_super_admin(
    admin_user_data: AdminUserCreate,
    db: Session = Depends(get_db)
):
    """Bootstrap the first super admin user (only if no super admins exist)"""
    # Check if any super admin already exists
    existing_super_admin = db.query(AdminUser).join(Role).filter(
        Role.name == "super_admin"
    ).first()
    
    if existing_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin already exists",
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == admin_user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    
    # Create or get super_admin role
    role = db.query(Role).filter(Role.name == "super_admin").first()
    if not role:
        role = Role(
            name="super_admin",
            description="Super Administrator with full system access",
        )
        db.add(role)
        db.commit()
        db.refresh(role)
    
    # Create user
    hashed_password = hash_password(admin_user_data.password)
    new_user = User(
        email=admin_user_data.email,
        full_name=admin_user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create admin user
    admin_record = AdminUser(
        user_id=new_user.id,
        role_id=role.id,
        username=admin_user_data.username,
        department=admin_user_data.department or "Management",
        is_verified=True,
        created_by=None,  # Bootstrap admin has no creator
    )
    db.add(admin_record)
    db.commit()
    db.refresh(admin_record)
    
    return admin_record
