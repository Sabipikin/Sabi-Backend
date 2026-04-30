"""
Subscription Management Routes
Handle recurring payment subscriptions to access all courses
"""
import os
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
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
from routes.admin_auth import get_current_admin
from services.payoneer_service import PayoneerService, PayoneerError
from services.email_service import EmailService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

# Environment variables
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


# === USER: GET AVAILABLE PLANS ===

@router.get("/plans", response_model=list)
async def get_subscription_plans(db: Session = Depends(get_db)):
    """Get all active subscription plans"""
    plans = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.is_active == True
    ).order_by(SubscriptionPlan.duration_days.asc()).all()
    
    return [
        {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "duration_days": plan.duration_days,
            "price": plan.price,
            "price_formatted": f"£{plan.price / 100:.2f}",
            "monthly_price": f"£{(plan.price / plan.duration_days * 30) / 100:.2f}" if plan.duration_days > 0 else "N/A",
            "created_at": plan.created_at.isoformat(),
        }
        for plan in plans
    ]


# === USER: SUBSCRIBE TO PLAN (CHECKOUT) ===

@router.post("/checkout", response_model=dict)
async def initiate_subscription_checkout(
    plan_id: int,
    token: dict = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    """Initiate Payoneer checkout for subscription"""
    try:
        user = db.query(User).filter(User.id == token["user_id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get subscription plan
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == plan_id,
            SubscriptionPlan.is_active == True
        ).first()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Check for existing active subscription
        existing_subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status.in_(["active", "paused"])
        ).first()
        
        if existing_subscription:
            raise HTTPException(
                status_code=400,
                detail="You already have an active subscription"
            )
        
        # Create payment record
        description = f"Subscription: {plan.name} ({plan.duration_days} days)"
        
        payment = Payment(
            user_id=user.id,
            amount=plan.price,
            currency="gbp",
            status="pending",
            payment_method="payoneer",
            item_type="subscription",
            description=description
        )
        db.add(payment)
        db.flush()
        
        # Prepare redirect URLs
        success_url = f"{FRONTEND_URL}/subscription/success?payment_id={payment.id}&plan_id={plan_id}"
        cancel_url = f"{FRONTEND_URL}/subscription/cancel?payment_id={payment.id}"
        
        # Create Payoneer checkout
        try:
            checkout_data = PayoneerService.create_checkout(
                amount=plan.price,
                currency="gbp",
                user_email=user.email,
                user_name=user.full_name or user.email,
                item_type="subscription",
                item_id=plan_id,
                description=description,
                success_url=success_url,
                cancel_url=cancel_url
            )
            
            # Update payment with Payoneer details
            payment.payoneer_order_id = checkout_data.get("order_id")
            payment.checkout_url = checkout_data.get("checkout_url")
            db.commit()
            db.refresh(payment)
            
            return {
                "payment_id": payment.id,
                "checkout_url": checkout_data.get("checkout_url"),
                "plan_id": plan_id,
                "plan_name": plan.name,
                "amount": plan.price,
                "currency": "GBP",
            }
            
        except PayoneerError as e:
            db.delete(payment)
            db.commit()
            logger.error(f"Payoneer checkout failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Checkout failed: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription checkout failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate subscription")


# === USER: GET CURRENT SUBSCRIPTION ===

@router.get("/current", response_model=dict)
async def get_current_subscription(
    token: dict = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    """Get user's current active subscription"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == token["user_id"],
        Subscription.status.in_(["active", "paused"])
    ).first()
    
    if not subscription:
        return {
            "active": False,
            "message": "No active subscription"
        }
    
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == subscription.plan_id
    ).first()
    
    days_remaining = (subscription.end_date - datetime.utcnow()).days
    
    return {
        "active": True,
        "subscription": {
            "id": subscription.id,
            "plan": {
                "id": plan.id,
                "name": plan.name,
                "duration_days": plan.duration_days,
                "price": plan.price,
            },
            "status": subscription.status,
            "start_date": subscription.start_date.isoformat(),
            "end_date": subscription.end_date.isoformat(),
            "days_remaining": max(0, days_remaining),
            "auto_renew": subscription.auto_renew,
        }
    }


# === USER: SUBSCRIPTION HISTORY ===

@router.get("/history", response_model=list)
async def get_subscription_history(
    token: dict = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    """Get user's subscription history"""
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == token["user_id"]
    ).order_by(Subscription.created_at.desc()).all()
    
    result = []
    for sub in subscriptions:
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == sub.plan_id
        ).first()
        
        result.append({
            "id": sub.id,
            "plan": {
                "name": plan.name if plan else "Unknown",
                "duration_days": plan.duration_days if plan else 0,
            },
            "status": sub.status,
            "start_date": sub.start_date.isoformat(),
            "end_date": sub.end_date.isoformat(),
            "auto_renew": sub.auto_renew,
            "created_at": sub.created_at.isoformat(),
        })
    
    return result


# === USER: CANCEL SUBSCRIPTION ===

@router.post("/{subscription_id}/cancel", response_model=dict)
async def cancel_subscription(
    subscription_id: int,
    token: dict = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    """Cancel an active subscription"""
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == token["user_id"]
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    if subscription.status in ["cancelled", "expired"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel a {subscription.status} subscription"
        )
    
    subscription.status = "cancelled"
    subscription.auto_renew = False
    db.commit()
    
    # Send cancellation email
    user = db.query(User).filter(User.id == token["user_id"]).first()
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == subscription.plan_id
    ).first()
    
    email_service = EmailService()
    email_service.send_email(
        to_email=user.email,
        subject="Subscription Cancelled",
        template_name="subscription_cancelled.html",
        context={
            "user_name": user.full_name or user.email,
            "plan_name": plan.name if plan else "Unknown",
            "end_date": subscription.end_date.strftime("%B %d, %Y"),
            "support_email": os.getenv("SUPPORT_EMAIL", "support@sabieducate.com"),
        }
    )
    
    return {
        "status": "ok",
        "message": "Subscription cancelled successfully",
        "subscription_id": subscription_id,
        "access_until": subscription.end_date.isoformat(),
    }


# === USER: PAUSE SUBSCRIPTION ===

@router.post("/{subscription_id}/pause", response_model=dict)
async def pause_subscription(
    subscription_id: int,
    token: dict = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    """Pause an active subscription"""
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == token["user_id"]
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    if subscription.status != "active":
        raise HTTPException(
            status_code=400,
            detail="Only active subscriptions can be paused"
        )
    
    subscription.status = "paused"
    db.commit()
    
    return {
        "status": "ok",
        "message": "Subscription paused",
        "subscription_id": subscription_id,
    }


# === USER: RESUME SUBSCRIPTION ===

@router.post("/{subscription_id}/resume", response_model=dict)
async def resume_subscription(
    subscription_id: int,
    token: dict = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    """Resume a paused subscription"""
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == token["user_id"]
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    if subscription.status != "paused":
        raise HTTPException(
            status_code=400,
            detail="Only paused subscriptions can be resumed"
        )
    
    subscription.status = "active"
    db.commit()
    
    return {
        "status": "ok",
        "message": "Subscription resumed",
        "subscription_id": subscription_id,
    }


# === ADMIN: MANAGE SUBSCRIPTION PLANS ===

@router.post("/admin/plans", response_model=dict)
async def create_subscription_plan(
    plan_data: SubscriptionPlanCreate,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new subscription plan (admin only)"""
    plan = SubscriptionPlan(
        name=plan_data.name,
        description=plan_data.description,
        duration_days=plan_data.duration_days,
        price=plan_data.price,
        stripe_price_id=plan_data.stripe_price_id,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return {
        "id": plan.id,
        "name": plan.name,
        "description": plan.description,
        "duration_days": plan.duration_days,
        "price": plan.price,
        "created_at": plan.created_at.isoformat(),
    }


@router.get("/admin/plans", response_model=list)
async def list_subscription_plans(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all subscription plans (admin only)"""
    plans = db.query(SubscriptionPlan).all()
    
    return [
        {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "duration_days": plan.duration_days,
            "price": plan.price,
            "is_active": plan.is_active,
            "created_at": plan.created_at.isoformat(),
        }
        for plan in plans
    ]


# === ADMIN: VIEW ALL SUBSCRIPTIONS ===

@router.get("/admin/subscriptions", response_model=dict)
async def list_all_subscriptions(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    status_filter: str = Query(None),
):
    """List all subscriptions (admin only)"""
    query = db.query(Subscription)
    
    if status_filter:
        query = query.filter(Subscription.status == status_filter)
    
    total = query.count()
    subscriptions = query.offset(skip).limit(limit).all()
    
    result = {
        "total": total,
        "subscriptions": []
    }
    
    for sub in subscriptions:
        user = db.query(User).filter(User.id == sub.user_id).first()
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == sub.plan_id
        ).first()
        
        result["subscriptions"].append({
            "id": sub.id,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.full_name,
            },
            "plan": {
                "id": plan.id,
                "name": plan.name,
            },
            "status": sub.status,
            "start_date": sub.start_date.isoformat(),
            "end_date": sub.end_date.isoformat(),
            "auto_renew": sub.auto_renew,
            "created_at": sub.created_at.isoformat(),
        })
    
    return result


# === ADMIN: SUBSCRIPTION ANALYTICS ===

@router.get("/admin/analytics", response_model=dict)
async def get_subscription_analytics(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
):
    """Get subscription analytics (admin only)"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Count by status
    total_active = db.query(func.count(Subscription.id)).filter(
        Subscription.status == "active"
    ).scalar()
    
    total_paused = db.query(func.count(Subscription.id)).filter(
        Subscription.status == "paused"
    ).scalar()
    
    total_cancelled = db.query(func.count(Subscription.id)).filter(
        Subscription.status == "cancelled",
        Subscription.updated_at >= cutoff_date
    ).scalar()
    
    total_expired = db.query(func.count(Subscription.id)).filter(
        Subscription.status == "expired",
        Subscription.updated_at >= cutoff_date
    ).scalar()
    
    # Revenue metrics
    active_subscriptions = db.query(Subscription).filter(
        Subscription.status.in_(["active", "paused"])
    ).all()
    
    monthly_recurring_revenue = 0
    for sub in active_subscriptions:
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == sub.plan_id
        ).first()
        if plan:
            # Calculate monthly equivalent
            monthly_price = (plan.price / plan.duration_days * 30) if plan.duration_days > 0 else plan.price
            monthly_recurring_revenue += monthly_price
    
    # Churn rate
    total_subscriptions = db.query(func.count(Subscription.id)).scalar()
    churn_rate = (total_cancelled / max(total_subscriptions, 1)) * 100 if total_cancelled > 0 else 0
    
    return {
        "period_days": days,
        "active_subscriptions": total_active,
        "paused_subscriptions": total_paused,
        "cancelled_subscriptions": total_cancelled,
        "expired_subscriptions": total_expired,
        "total_subscriptions": total_subscriptions,
        "monthly_recurring_revenue_cents": int(monthly_recurring_revenue),
        "monthly_recurring_revenue_formatted": f"£{monthly_recurring_revenue / 100:.2f}",
        "churn_rate_percent": round(churn_rate, 2),
    }

