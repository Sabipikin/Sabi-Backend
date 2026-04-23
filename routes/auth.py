from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserProfile
from schemas import UserCreate, UserResponse, UserLogin, Token
from auth import hash_password, verify_password, create_access_token, decode_access_token
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


class RegionUpdate(BaseModel):
    region: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    email = decode_access_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.post("/signup", response_model=Token)
async def signup(user_create: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_create.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    hashed_password = hash_password(user_create.password)
    new_user = User(
        email=user_create.email,
        hashed_password=hashed_password,
        full_name=user_create.full_name,
        region=user_create.region,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create user profile
    user_profile = UserProfile(user_id=new_user.id)
    db.add(user_profile)
    db.commit()

    # Create access token
    access_token = create_access_token(data={"sub": new_user.email})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(new_user),
    }


@router.post("/login", response_model=Token)
async def login(user_login: UserLogin, db: Session = Depends(get_db)):
    # Get user by email
    user = db.query(User).filter(User.email == user_login.email).first()
    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user),
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_endpoint(current_user: User = Depends(get_current_user)):
    return UserResponse.from_orm(current_user)


@router.put("/region", response_model=UserResponse)
async def update_user_region(
    region_data: RegionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's region (uk, ie, eu)"""
    region = region_data.region
    if region not in ['uk', 'ie', 'eu']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid region. Must be 'uk', 'ie', or 'eu'",
        )
    
    current_user.region = region
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.from_orm(current_user)
