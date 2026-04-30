"""
Payoneer Payment Integration
"""
import os
import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Payment, User
from schemas import PaymentCreate, PaymentResponse
from auth import decode_access_token

router = APIRouter(prefix="/api/payments", tags=["payments"])

# Payoneer API Configuration
PAYONEER_API_URL = "https://api.payoneer.com/v2"
PAYONEER_CLIENT_ID = os.getenv("PAYONEER_CLIENT_ID")
PAYONEER_CLIENT_SECRET = os.getenv("PAYONEER_CLIENT_SECRET")

def get_payoneer_access_token():
    """Get access token from Payoneer"""
    response = requests.post(f"{PAYONEER_API_URL}/oauth/token", data={
        "grant_type": "client_credentials",
        "client_id": PAYONEER_CLIENT_ID,
        "client_secret": PAYONEER_CLIENT_SECRET
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise HTTPException(status_code=500, detail="Failed to authenticate with Payoneer")

@router.post("/create-payment", response_model=dict)
async def create_payoneer_payment(
    payment_data: PaymentCreate,
    token: str = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    """Create a payment using Payoneer Checkout"""
    user = db.query(User).filter(User.id == token["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get Payoneer access token
    access_token = get_payoneer_access_token()

    # Create payment request to Payoneer
    payment_request = {
        "amount": payment_data.amount,
        "currency": payment_data.currency.upper(),
        "description": payment_data.description,
        "customer": {
            "email": user.email,
            "name": user.full_name
        },
        "redirect_urls": {
            "success_url": f"{os.getenv('FRONTEND_URL')}/payment/success",
            "cancel_url": f"{os.getenv('FRONTEND_URL')}/payment/cancel"
        }
    }

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(
        f"{PAYONEER_API_URL}/payments",
        json=payment_request,
        headers=headers
    )

    if response.status_code == 201:
        payment_data = response.json()

        # Save payment record in our database
        db_payment = Payment(
            user_id=user.id,
            amount=payment_data["amount"],
            currency=payment_data["currency"].lower(),
            status="pending",
            payment_method="payoneer",
            transaction_id=payment_data["id"],
            description=payment_data["description"]
        )
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)

        return {
            "payment_id": db_payment.id,
            "checkout_url": payment_data["checkout_url"],
            "transaction_id": payment_data["id"]
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to create payment")

@router.post("/webhook")
async def payoneer_webhook(
    webhook_data: dict,
    db: Session = Depends(get_db)
):
    """Handle Payoneer webhook for payment status updates"""
    # Verify webhook signature (implement signature verification)
    transaction_id = webhook_data.get("transaction_id")
    status_update = webhook_data.get("status")

    if transaction_id and status_update:
        payment = db.query(Payment).filter(Payment.transaction_id == transaction_id).first()
        if payment:
            payment.status = status_update
            db.commit()

    return {"status": "ok"}</content>
<parameter name="filePath">/Users/sabipikin/Documents/Sabi Educate/sabipath-split/sabi-backend/routes/payments.py