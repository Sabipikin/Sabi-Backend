"""
Subscription and Course Payment Management Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from database import get_db
from models import (
    User, Subscription, SubscriptionPlan, Payment, Course, Enrollment
)
from schemas import (
    SubscriptionPlanCreate, SubscriptionPlanResponse,
    SubscriptionCreate, SubscriptionResponse,
    EnrollmentDetailResponse
)
from auth import decode_access_token

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


# ============ Subscription Plans ============

@router.get("/plans", response_model=list[SubscriptionPlanResponse])
async def get_subscription_plans(
    db: Session = Depends(get_db),
    active_only: bool = True
):
    """Get available subscription plans"""
    query = db.query(SubscriptionPlan)
    if active_only:
        query = query.filter(SubscriptionPlan.is_active == True)
    return query.all()


@router.post("/plans", response_model=SubscriptionPlanResponse)
async def create_subscription_plan(
    plan_data: SubscriptionPlanCreate,
    token: str,
    db: Session = Depends(get_db)
):
    """Create a new subscription plan (Admin only)"""
    new_plan = SubscriptionPlan(
        name=plan_data.name,
        description=plan_data.description,
        duration_days=plan_data.duration_days,
        price=plan_data.price,
        stripe_price_id=plan_data.stripe_price_id,
        is_active=True
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return new_plan


# ============ User Subscriptions ============

@router.get("/my-subscription", response_model=SubscriptionResponse)
async def get_my_subscription(
    token: str,
    db: Session = Depends(get_db)
):
    """Get current user's active subscription"""
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get active subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active",
        Subscription.end_date > datetime.utcnow()
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription")
    
    return subscription


@router.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe_to_plan(
    plan_id: int,
    payment_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Subscribe user to a plan after payment"""
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify plan exists
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == plan_id,
        SubscriptionPlan.is_active == True
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    
    # Verify payment
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == user.id,
        Payment.status == "completed"
    ).first()
    if not payment:
        raise HTTPException(status_code=400, detail="Payment not verified")
    
    # Cancel existing subscriptions
    db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active"
    ).update({"status": "cancelled"})
    
    # Create new subscription
    end_date = datetime.utcnow() + timedelta(days=plan.duration_days)
    
    new_subscription = Subscription(
        user_id=user.id,
        plan_id=plan_id,
        payment_id=payment_id,
        status="active",
        end_date=end_date,
        auto_renew=True
    )
    db.add(new_subscription)
    db.commit()
    db.refresh(new_subscription)
    
    return new_subscription


@router.get("/is-subscribed", response_model=dict)
async def check_subscription_status(
    token: str,
    db: Session = Depends(get_db)
):
    """Check if user has active subscription"""
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check active subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active",
        Subscription.end_date > datetime.utcnow()
    ).first()
    
    if subscription:
        return {
            "is_subscribed": True,
            "subscription_id": subscription.id,
            "plan_id": subscription.plan_id,
            "end_date": subscription.end_date,
            "days_remaining": (subscription.end_date - datetime.utcnow()).days
        }
    
    return {
        "is_subscribed": False,
        "subscription_id": None,
        "plan_id": None,
        "end_date": None,
        "days_remaining": None
    }


@router.post("/cancel")
async def cancel_subscription(
    token: str,
    db: Session = Depends(get_db)
):
    """Cancel user's subscription"""
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription")
    
    subscription.status = "cancelled"
    subscription.auto_renew = False
    db.commit()
    
    return {"message": "Subscription cancelled successfully"}
