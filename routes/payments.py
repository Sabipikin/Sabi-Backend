"""Payment Management Routes with Payoneer Integration"""
import os
import json
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db
from models import (
    Payment, User, Course, Program, Diploma,
    Enrollment, ProgramEnrollment, DiplomaEnrollment
)
from schemas import (
    PaymentCreate, PaymentResponse, 
    PaymentCheckoutRequest, PaymentWebhookRequest
)
from auth import decode_access_token
from services.payoneer_service import PayoneerService, PayoneerError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payments", tags=["payments"])

# Environment variables
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


@router.post("/checkout", response_model=dict)
async def initiate_checkout(
    checkout_request: PaymentCheckoutRequest,
    token: dict = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    """
    Initiate a Payoneer checkout session for purchasing courses, programs, or diplomas
    """
    try:
        user = db.query(User).filter(User.id == token["user_id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get the item being purchased
        item_type = checkout_request.item_type.lower()
        item_id = checkout_request.item_id
        amount = 0
        item_name = ""
        description = ""
        
        if item_type == "course":
            item = db.query(Course).filter(Course.id == item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail="Course not found")
            amount = item.fee
            item_name = item.title
            description = f"Course: {item.title}"
            
        elif item_type == "program":
            item = db.query(Program).filter(Program.id == item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail="Program not found")
            amount = item.fee
            item_name = item.title
            description = f"Program: {item.title}"
            
        elif item_type == "diploma":
            item = db.query(Diploma).filter(Diploma.id == item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail="Diploma not found")
            amount = item.fee
            item_name = item.title
            description = f"Diploma: {item.title}"
        else:
            raise HTTPException(status_code=400, detail=f"Invalid item type: {item_type}")
        
        # Check if amount is 0 (free item)
        if amount == 0:
            raise HTTPException(status_code=400, detail="This item is free")
        
        # Create payment record
        payment = Payment(
            user_id=user.id,
            amount=amount,
            currency=checkout_request.currency.lower(),
            status="pending",
            payment_method="payoneer",
            item_type=item_type,
            course_id=item_id if item_type == "course" else None,
            program_id=item_id if item_type == "program" else None,
            diploma_id=item_id if item_type == "diploma" else None,
            description=description
        )
        db.add(payment)
        db.flush()
        
        # Prepare redirect URLs
        success_url = f"{FRONTEND_URL}/payment/success?payment_id={payment.id}"
        cancel_url = f"{FRONTEND_URL}/payment/cancel?payment_id={payment.id}"
        
        # Create Payoneer checkout
        try:
            checkout_data = PayoneerService.create_checkout(
                amount=amount,
                currency=checkout_request.currency,
                user_email=user.email,
                user_name=user.full_name or user.email,
                item_type=item_type,
                item_id=item_id,
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
                "order_id": checkout_data.get("order_id"),
                "amount": amount,
                "currency": checkout_request.currency.upper(),
                "item_type": item_type,
                "item_id": item_id,
                "item_name": item_name
            }
            
        except PayoneerError as e:
            db.delete(payment)
            db.commit()
            logger.error(f"Payoneer checkout failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Checkout failed: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Checkout initiation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate checkout")


@router.get("/status/{payment_id}", response_model=PaymentResponse)
async def get_payment_status(
    payment_id: int,
    token: dict = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    """Get the current status of a payment"""
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == token["user_id"]
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return payment


@router.post("/webhook")
async def payoneer_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Payoneer webhook for payment status updates"""
    try:
        # Get raw body for signature verification
        body = await request.body()
        webhook_data = json.loads(body)
        
        # Verify webhook signature
        signature = request.headers.get("X-Payoneer-Signature")
        if signature:
            is_valid = PayoneerService.verify_webhook_signature(body.decode(), signature)
            if not is_valid:
                logger.warning("Invalid Payoneer webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process webhook data
        processed_data = PayoneerService.process_webhook(webhook_data)
        
        # Find payment by order_id
        payment = db.query(Payment).filter(
            Payment.payoneer_order_id == processed_data.get("order_id")
        ).first()
        
        if not payment:
            logger.warning(f"Payment not found for order: {processed_data.get('order_id')}")
            return {"status": "ok"}
        
        # Update payment status
        payment.status = processed_data["status"]
        payment.transaction_id = processed_data.get("transaction_id")
        payment.payoneer_webhook_response = json.dumps(webhook_data)
        payment.webhook_verified = True
        
        # If payment is completed, create enrollment
        if processed_data["status"] == "completed":
            payment.completed_at = datetime.utcnow()
            
            if payment.item_type == "course" and payment.course_id:
                existing = db.query(Enrollment).filter(
                    Enrollment.user_id == payment.user_id,
                    Enrollment.course_id == payment.course_id
                ).first()
                if not existing:
                    enrollment = Enrollment(
                        user_id=payment.user_id,
                        course_id=payment.course_id,
                        progress_percentage=0
                    )
                    db.add(enrollment)
            
            elif payment.item_type == "program" and payment.program_id:
                existing = db.query(ProgramEnrollment).filter(
                    ProgramEnrollment.user_id == payment.user_id,
                    ProgramEnrollment.program_id == payment.program_id
                ).first()
                if not existing:
                    enrollment = ProgramEnrollment(
                        user_id=payment.user_id,
                        program_id=payment.program_id
                    )
                    db.add(enrollment)
            
            elif payment.item_type == "diploma" and payment.diploma_id:
                existing = db.query(DiplomaEnrollment).filter(
                    DiplomaEnrollment.user_id == payment.user_id,
                    DiplomaEnrollment.diploma_id == payment.diploma_id
                ).first()
                if not existing:
                    enrollment = DiplomaEnrollment(
                        user_id=payment.user_id,
                        diploma_id=payment.diploma_id
                    )
                    db.add(enrollment)
        
        db.commit()
        logger.info(f"Payment {payment.id} updated to status: {processed_data['status']}")
        
        return {"status": "ok", "payment_id": payment.id}
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/list", response_model=list)
async def list_payments(
    token: dict = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    """List all payments for the current user"""
    payments = db.query(Payment).filter(
        Payment.user_id == token["user_id"]
    ).order_by(Payment.created_at.desc()).all()
    
    return payments
