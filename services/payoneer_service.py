"""
Payoneer Payment Service
Handles all Payoneer API interactions for payment processing
"""
import os
import hashlib
import hmac
import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Payoneer API Configuration
PAYONEER_API_BASE_URL = os.getenv("PAYONEER_API_URL", "https://api.payoneer.com/v2")
PAYONEER_CLIENT_ID = os.getenv("PAYONEER_CLIENT_ID")
PAYONEER_CLIENT_SECRET = os.getenv("PAYONEER_CLIENT_SECRET")
PAYONEER_WEBHOOK_SECRET = os.getenv("PAYONEER_WEBHOOK_SECRET")
PAYONEER_PARTNER_ID = os.getenv("PAYONEER_PARTNER_ID")

# Supported currencies for Payoneer
SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "INR", "CAD", "AUD"]


class PayoneerError(Exception):
    """Custom exception for Payoneer errors"""
    pass


class PayoneerService:
    """Service class for Payoneer API integration"""
    
    @staticmethod
    def get_access_token() -> str:
        """
        Authenticate with Payoneer API and get access token
        
        Returns:
            str: Access token for API requests
            
        Raises:
            PayoneerError: If authentication fails
        """
        try:
            url = f"{PAYONEER_API_BASE_URL}/oauth/token"
            payload = {
                "grant_type": "client_credentials",
                "client_id": PAYONEER_CLIENT_ID,
                "client_secret": PAYONEER_CLIENT_SECRET
            }
            
            response = requests.post(url, data=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get("access_token")
            
        except requests.RequestException as e:
            logger.error(f"Payoneer authentication failed: {str(e)}")
            raise PayoneerError(f"Failed to authenticate with Payoneer: {str(e)}")
    
    @staticmethod
    def create_checkout(
        amount: int,
        currency: str,
        user_email: str,
        user_name: str,
        item_type: str,
        item_id: int,
        description: str,
        success_url: str,
        cancel_url: str,
    ) -> Dict[str, Any]:
        """
        Create a Payoneer checkout session
        
        Args:
            amount: Amount in cents
            currency: Currency code (USD, EUR, GBP, etc)
            user_email: Customer email
            user_name: Customer name
            item_type: Type of item being purchased (course, program, diploma, subscription)
            item_id: ID of the item
            description: Payment description
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment
            
        Returns:
            dict: Checkout response with checkout_url and order_id
            
        Raises:
            PayoneerError: If checkout creation fails
        """
        try:
            access_token = PayoneerService.get_access_token()
            url = f"{PAYONEER_API_BASE_URL}/checkout/sessions"
            
            # Convert amount from cents to proper decimal format
            amount_decimal = f"{amount / 100:.2f}"
            
            # Create unique order ID
            order_id = f"sabi-{item_type}-{item_id}-{int(datetime.now().timestamp())}"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "amount": amount_decimal,
                "currency": currency.upper(),
                "order_id": order_id,
                "customer": {
                    "email": user_email,
                    "name": user_name
                },
                "description": description,
                "success_url": success_url,
                "cancel_url": cancel_url,
                "redirect_type": "redirect_to_payment_page",
                "line_items": [
                    {
                        "name": f"{item_type.capitalize()}: {description}",
                        "description": description,
                        "quantity": 1,
                        "unit_price": amount_decimal,
                        "currency": currency.upper()
                    }
                ]
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "checkout_url": data.get("checkout_url"),
                "order_id": data.get("order_id", order_id),
                "session_id": data.get("session_id"),
                "expires_at": data.get("expires_at")
            }
            
        except requests.RequestException as e:
            logger.error(f"Payoneer checkout creation failed: {str(e)}")
            raise PayoneerError(f"Failed to create Payoneer checkout: {str(e)}")
    
    @staticmethod
    def verify_webhook_signature(payload: str, signature: str) -> bool:
        """
        Verify Payoneer webhook signature for security
        
        Args:
            payload: Raw webhook payload
            signature: Signature from webhook header
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        if not PAYONEER_WEBHOOK_SECRET:
            logger.warning("PAYONEER_WEBHOOK_SECRET not set, skipping signature verification")
            return True
        
        try:
            expected_signature = hmac.new(
                PAYONEER_WEBHOOK_SECRET.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            return False
    
    @staticmethod
    def get_payment_status(order_id: str) -> Dict[str, Any]:
        """
        Get payment status from Payoneer
        
        Args:
            order_id: Payoneer order ID
            
        Returns:
            dict: Payment status information
            
        Raises:
            PayoneerError: If status check fails
        """
        try:
            access_token = PayoneerService.get_access_token()
            url = f"{PAYONEER_API_BASE_URL}/payments/{order_id}"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "status": data.get("status"),
                "amount": data.get("amount"),
                "currency": data.get("currency"),
                "transaction_id": data.get("id"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at")
            }
            
        except requests.RequestException as e:
            logger.error(f"Payoneer payment status check failed: {str(e)}")
            raise PayoneerError(f"Failed to get payment status: {str(e)}")
    
    @staticmethod
    def process_webhook(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Payoneer webhook and extract payment information
        
        Args:
            webhook_data: Webhook payload from Payoneer
            
        Returns:
            dict: Processed webhook data with status mapping
        """
        # Map Payoneer status to our internal status
        payoneer_status = webhook_data.get("status", "").lower()
        status_mapping = {
            "completed": "completed",
            "approved": "completed",
            "pending": "pending",
            "failed": "failed",
            "canceled": "failed",
            "refunded": "refunded",
            "expired": "expired"
        }
        
        internal_status = status_mapping.get(payoneer_status, "pending")
        
        return {
            "transaction_id": webhook_data.get("id"),
            "order_id": webhook_data.get("order_id"),
            "status": internal_status,
            "payoneer_status": payoneer_status,
            "amount": webhook_data.get("amount"),
            "currency": webhook_data.get("currency"),
            "timestamp": webhook_data.get("timestamp"),
            "customer_email": webhook_data.get("customer", {}).get("email"),
            "description": webhook_data.get("description")
        }
