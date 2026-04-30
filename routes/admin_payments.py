"""
Admin payment management routes
Admins can view all payments, process refunds, and access analytics
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from database import get_db
from models import Payment, User, Enrollment, ProgramEnrollment, DiplomaEnrollment, Course, Program, Diploma
from routes.admin_auth import get_current_admin
from services.email_service import EmailService
from datetime import datetime, timedelta
from typing import Optional, List

router = APIRouter(prefix="/api/admin/payments", tags=["admin-payments"])


# === LIST PAYMENTS ===

@router.get("/", response_model=dict)
async def list_payments(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    status_filter: Optional[str] = Query(None),
    item_type_filter: Optional[str] = Query(None),
    user_search: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    sort_by: str = Query("created_at", regex="^(created_at|amount|status)$"),
    order: str = Query("desc", regex="^(asc|desc)$")
):
    """Get all payments with filtering and sorting"""
    
    query = db.query(Payment)
    
    # Apply filters
    if status_filter:
        query = query.filter(Payment.status == status_filter)
    
    if item_type_filter:
        query = query.filter(Payment.item_type == item_type_filter)
    
    if user_search:
        query = query.join(User).filter(
            or_(
                User.email.ilike(f"%{user_search}%"),
                User.full_name.ilike(f"%{user_search}%")
            )
        )
    
    if date_from:
        try:
            from_date = datetime.fromisoformat(date_from)
            query = query.filter(Payment.created_at >= from_date)
        except:
            pass
    
    if date_to:
        try:
            to_date = datetime.fromisoformat(date_to)
            query = query.filter(Payment.created_at <= to_date)
        except:
            pass
    
    # Count total before pagination
    total = query.count()
    
    # Sort
    if sort_by == "created_at":
        query = query.order_by(Payment.created_at.desc() if order == "desc" else Payment.created_at.asc())
    elif sort_by == "amount":
        query = query.order_by(Payment.amount.desc() if order == "desc" else Payment.amount.asc())
    elif sort_by == "status":
        query = query.order_by(Payment.status.desc() if order == "desc" else Payment.status.asc())
    
    # Paginate
    payments = query.offset(skip).limit(limit).all()
    
    # Format response
    result = {
        "total": total,
        "skip": skip,
        "limit": limit,
        "payments": []
    }
    
    for payment in payments:
        user = db.query(User).filter(User.id == payment.user_id).first()
        item_name = ""
        
        if payment.item_type == "course" and payment.course_id:
            course = db.query(Course).filter(Course.id == payment.course_id).first()
            item_name = course.title if course else "Unknown Course"
        elif payment.item_type == "program" and payment.program_id:
            program = db.query(Program).filter(Program.id == payment.program_id).first()
            item_name = program.title if program else "Unknown Program"
        elif payment.item_type == "diploma" and payment.diploma_id:
            diploma = db.query(Diploma).filter(Diploma.id == payment.diploma_id).first()
            item_name = diploma.title if diploma else "Unknown Diploma"
        
        result["payments"].append({
            "id": payment.id,
            "user_id": payment.user_id,
            "user_email": user.email if user else "Unknown",
            "user_name": user.full_name if user else "Unknown",
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status,
            "item_type": payment.item_type,
            "item_name": item_name,
            "item_id": payment.course_id or payment.program_id or payment.diploma_id,
            "payoneer_order_id": payment.payoneer_order_id,
            "webhook_verified": payment.webhook_verified,
            "created_at": payment.created_at.isoformat(),
            "completed_at": payment.completed_at.isoformat() if payment.completed_at else None
        })
    
    return result


# === GET PAYMENT DETAILS ===

@router.get("/{payment_id}", response_model=dict)
async def get_payment_detail(
    payment_id: int,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific payment"""
    
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    user = db.query(User).filter(User.id == payment.user_id).first()
    
    item_name = ""
    item_details = {}
    
    if payment.item_type == "course" and payment.course_id:
        course = db.query(Course).filter(Course.id == payment.course_id).first()
        if course:
            item_name = course.title
            item_details = {
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "category": course.category,
                "difficulty": course.difficulty
            }
    elif payment.item_type == "program" and payment.program_id:
        program = db.query(Program).filter(Program.id == payment.program_id).first()
        if program:
            item_name = program.title
            item_details = {
                "id": program.id,
                "title": program.title,
                "description": program.description,
                "difficulty": program.difficulty,
                "duration_months": program.duration_months
            }
    elif payment.item_type == "diploma" and payment.diploma_id:
        diploma = db.query(Diploma).filter(Diploma.id == payment.diploma_id).first()
        if diploma:
            item_name = diploma.title
            item_details = {
                "id": diploma.id,
                "title": diploma.title,
                "description": diploma.description,
                "level": diploma.level,
                "duration_years": diploma.duration_years
            }
    
    # Check enrollment
    enrollment_record = None
    if payment.item_type == "course" and payment.course_id:
        enrollment_record = db.query(Enrollment).filter(
            Enrollment.user_id == payment.user_id,
            Enrollment.course_id == payment.course_id
        ).first()
    elif payment.item_type == "program" and payment.program_id:
        enrollment_record = db.query(ProgramEnrollment).filter(
            ProgramEnrollment.user_id == payment.user_id,
            ProgramEnrollment.program_id == payment.program_id
        ).first()
    elif payment.item_type == "diploma" and payment.diploma_id:
        enrollment_record = db.query(DiplomaEnrollment).filter(
            DiplomaEnrollment.user_id == payment.user_id,
            DiplomaEnrollment.diploma_id == payment.diploma_id
        ).first()
    
    return {
        "id": payment.id,
        "user": {
            "id": user.id if user else None,
            "email": user.email if user else None,
            "full_name": user.full_name if user else None,
            "region": user.region if user else None
        },
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status,
        "item_type": payment.item_type,
        "item_name": item_name,
        "item_details": item_details,
        "enrollment": {
            "exists": enrollment_record is not None,
            "status": enrollment_record.status if enrollment_record else None,
            "enrolled_at": enrollment_record.enrolled_at.isoformat() if enrollment_record else None,
            "started_at": enrollment_record.started_at.isoformat() if enrollment_record and enrollment_record.started_at else None,
            "completed_at": enrollment_record.completed_at.isoformat() if enrollment_record and enrollment_record.completed_at else None
        },
        "payoneer_order_id": payment.payoneer_order_id,
        "checkout_url": payment.checkout_url,
        "webhook_verified": payment.webhook_verified,
        "created_at": payment.created_at.isoformat(),
        "completed_at": payment.completed_at.isoformat() if payment.completed_at else None
    }


# === PROCESS REFUND ===

@router.post("/{payment_id}/refund", response_model=dict)
async def process_refund(
    payment_id: int,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Process a refund for a payment (admin only)"""
    
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    if payment.status == "refunded":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already refunded"
        )
    
    if payment.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only refund completed payments"
        )
    
    # Update payment status
    payment.status = "refunded"
    payment.completed_at = datetime.utcnow()
    
    # Remove enrollment if it exists
    if payment.item_type == "course" and payment.course_id:
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == payment.user_id,
            Enrollment.course_id == payment.course_id
        ).first()
        if enrollment:
            db.delete(enrollment)
    elif payment.item_type == "program" and payment.program_id:
        enrollment = db.query(ProgramEnrollment).filter(
            ProgramEnrollment.user_id == payment.user_id,
            ProgramEnrollment.program_id == payment.program_id
        ).first()
        if enrollment:
            db.delete(enrollment)
    elif payment.item_type == "diploma" and payment.diploma_id:
        enrollment = db.query(DiplomaEnrollment).filter(
            DiplomaEnrollment.user_id == payment.user_id,
            DiplomaEnrollment.diploma_id == payment.diploma_id
        ).first()
        if enrollment:
            db.delete(enrollment)
    
    db.commit()
    
    # Send refund notification email
    user = db.query(User).filter(User.id == payment.user_id).first()
    if user:
        payment_data = {
            "id": payment.id,
            "amount": payment.amount,
            "currency": payment.currency,
            "item_type": payment.item_type,
            "item_name": payment.description or "",
            "payoneer_order_id": payment.payoneer_order_id,
            "status": payment.status,
        }
        email_service = EmailService()
        email_service.send_refund_notification(
            user_email=user.email,
            user_name=user.full_name or user.email,
            payment_data=payment_data
        )
    
    return {
        "status": "ok",
        "message": "Refund processed successfully",
        "payment_id": payment.id,
        "new_status": "refunded",
        "amount_refunded": payment.amount
    }


# === ANALYTICS ===

@router.get("/analytics/summary", response_model=dict)
async def get_analytics_summary(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
):
    """Get payment analytics for admin dashboard"""
    
    date_from = datetime.utcnow() - timedelta(days=days)
    
    # Total payments in period
    total_payments = db.query(func.count(Payment.id)).filter(
        Payment.created_at >= date_from
    ).scalar() or 0
    
    # Total revenue
    total_revenue = db.query(func.sum(Payment.amount)).filter(
        and_(
            Payment.created_at >= date_from,
            Payment.status == "completed"
        )
    ).scalar() or 0
    
    # Completed payments
    completed_payments = db.query(func.count(Payment.id)).filter(
        and_(
            Payment.created_at >= date_from,
            Payment.status == "completed"
        )
    ).scalar() or 0
    
    # Failed/Cancelled payments
    failed_payments = db.query(func.count(Payment.id)).filter(
        and_(
            Payment.created_at >= date_from,
            Payment.status.in_(["failed", "cancelled"])
        )
    ).scalar() or 0
    
    # Pending payments
    pending_payments = db.query(func.count(Payment.id)).filter(
        and_(
            Payment.created_at >= date_from,
            Payment.status == "pending"
        )
    ).scalar() or 0
    
    # Refunded payments
    refunded_payments = db.query(func.count(Payment.id)).filter(
        and_(
            Payment.created_at >= date_from,
            Payment.status == "refunded"
        )
    ).scalar() or 0
    
    # Revenue by item type
    revenue_by_type = db.query(
        Payment.item_type,
        func.count(Payment.id).label("count"),
        func.sum(Payment.amount).label("total")
    ).filter(
        and_(
            Payment.created_at >= date_from,
            Payment.status == "completed"
        )
    ).group_by(Payment.item_type).all()
    
    # Average order value
    aov = (total_revenue / completed_payments * 100) if completed_payments > 0 else 0
    
    # Conversion rate
    conversion_rate = (completed_payments / total_payments * 100) if total_payments > 0 else 0
    
    return {
        "period_days": days,
        "summary": {
            "total_payments": total_payments,
            "completed_payments": completed_payments,
            "pending_payments": pending_payments,
            "failed_payments": failed_payments,
            "refunded_payments": refunded_payments,
            "total_revenue_cents": int(total_revenue),
            "total_revenue_formatted": f"£{total_revenue / 100:.2f}" if total_revenue > 0 else "£0.00",
            "average_order_value_cents": int(aov),
            "average_order_value_formatted": f"£{aov / 100:.2f}" if aov > 0 else "£0.00",
            "conversion_rate_percent": round(conversion_rate, 2)
        },
        "by_item_type": [
            {
                "item_type": item_type,
                "count": count,
                "total_revenue_cents": int(total) if total else 0,
                "total_revenue_formatted": f"£{total / 100:.2f}" if total else "£0.00"
            }
            for item_type, count, total in revenue_by_type
        ]
    }


# === DAILY REVENUE ===

@router.get("/analytics/daily", response_model=dict)
async def get_daily_revenue(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
):
    """Get daily revenue breakdown"""
    
    date_from = datetime.utcnow() - timedelta(days=days)
    
    daily_data = db.query(
        func.date(Payment.created_at).label("date"),
        func.count(Payment.id).label("transactions"),
        func.sum(Payment.amount).label("revenue")
    ).filter(
        and_(
            Payment.created_at >= date_from,
            Payment.status == "completed"
        )
    ).group_by(func.date(Payment.created_at)).order_by(
        func.date(Payment.created_at).desc()
    ).all()
    
    return {
        "period_days": days,
        "daily_breakdown": [
            {
                "date": str(date),
                "transactions": transactions,
                "revenue_cents": int(revenue) if revenue else 0,
                "revenue_formatted": f"£{revenue / 100:.2f}" if revenue else "£0.00"
            }
            for date, transactions, revenue in daily_data
        ]
    }


# === TOP CUSTOMERS ===

@router.get("/analytics/top-customers", response_model=dict)
async def get_top_customers(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=100)
):
    """Get top paying customers"""
    
    date_from = datetime.utcnow() - timedelta(days=days)
    
    top_customers = db.query(
        User.id,
        User.email,
        User.full_name,
        func.count(Payment.id).label("payment_count"),
        func.sum(Payment.amount).label("total_spent")
    ).join(
        Payment, Payment.user_id == User.id
    ).filter(
        and_(
            Payment.created_at >= date_from,
            Payment.status == "completed"
        )
    ).group_by(
        User.id, User.email, User.full_name
    ).order_by(
        func.sum(Payment.amount).desc()
    ).limit(limit).all()
    
    return {
        "period_days": days,
        "top_customers": [
            {
                "user_id": user_id,
                "email": email,
                "full_name": full_name,
                "payment_count": payment_count,
                "total_spent_cents": int(total_spent),
                "total_spent_formatted": f"£{total_spent / 100:.2f}" if total_spent else "£0.00"
            }
            for user_id, email, full_name, payment_count, total_spent in top_customers
        ]
    }
