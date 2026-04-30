"""
Test suite for Payoneer payment webhook verification and processing
Tests webhook signature validation, payment status updates, and enrollment creation
"""
import pytest
import json
import hmac
import hashlib
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# This assumes FastAPI app setup - adjust imports based on your structure
# from main import app
# from database import Base, get_db


class TestPaymentWebhook:
    """Test payment webhook verification and processing"""

    @pytest.fixture
    def mock_webhook_data(self):
        """Create mock webhook payload"""
        return {
            "order_id": "test_order_12345",
            "transaction_id": "txn_123456",
            "status": "completed",
            "amount": 9999,
            "currency": "GBP",
            "customer_email": "test@example.com",
            "timestamp": datetime.utcnow().isoformat(),
        }

    @pytest.fixture
    def webhook_signature(self, mock_webhook_data):
        """Generate valid webhook signature"""
        payload = json.dumps(mock_webhook_data, sort_keys=True)
        webhook_secret = "test_webhook_secret"
        signature = hmac.new(
            webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def test_valid_webhook_signature(self, mock_webhook_data, webhook_signature):
        """Test webhook with valid signature is accepted"""
        from services.payoneer_service import PayoneerService

        payload = json.dumps(mock_webhook_data, sort_keys=True)
        # Mock environment variable
        with patch.dict("os.environ", {"PAYONEER_WEBHOOK_SECRET": "test_webhook_secret"}):
            is_valid = PayoneerService.verify_webhook_signature(payload, webhook_signature)
            assert is_valid is True

    def test_invalid_webhook_signature(self, mock_webhook_data):
        """Test webhook with invalid signature is rejected"""
        from services.payoneer_service import PayoneerService

        payload = json.dumps(mock_webhook_data, sort_keys=True)
        invalid_signature = "invalid_signature_12345"

        with patch.dict("os.environ", {"PAYONEER_WEBHOOK_SECRET": "test_webhook_secret"}):
            is_valid = PayoneerService.verify_webhook_signature(payload, invalid_signature)
            assert is_valid is False

    def test_tampered_webhook_payload(self, mock_webhook_data, webhook_signature):
        """Test webhook with tampered payload is rejected"""
        from services.payoneer_service import PayoneerService

        # Tamper with data
        mock_webhook_data["amount"] = 50000  # Changed amount
        payload = json.dumps(mock_webhook_data, sort_keys=True)

        with patch.dict("os.environ", {"PAYONEER_WEBHOOK_SECRET": "test_webhook_secret"}):
            is_valid = PayoneerService.verify_webhook_signature(payload, webhook_signature)
            assert is_valid is False

    def test_webhook_process_completed_status(self):
        """Test webhook processing for completed payment"""
        from services.payoneer_service import PayoneerService

        webhook_data = {
            "order_id": "test_order_12345",
            "transaction_id": "txn_123456",
            "status": "completed",
            "amount": 9999,
            "currency": "GBP",
        }

        processed = PayoneerService.process_webhook(webhook_data)

        assert processed["status"] == "completed"
        assert processed["order_id"] == "test_order_12345"
        assert processed["transaction_id"] == "txn_123456"

    def test_webhook_process_pending_status(self):
        """Test webhook processing for pending payment"""
        from services.payoneer_service import PayoneerService

        webhook_data = {
            "order_id": "test_order_12345",
            "transaction_id": "txn_123456",
            "status": "pending",
            "amount": 9999,
            "currency": "GBP",
        }

        processed = PayoneerService.process_webhook(webhook_data)

        assert processed["status"] == "pending"

    def test_webhook_process_failed_status(self):
        """Test webhook processing for failed payment"""
        from services.payoneer_service import PayoneerService

        webhook_data = {
            "order_id": "test_order_12345",
            "transaction_id": "txn_123456",
            "status": "failed",
            "amount": 9999,
            "currency": "GBP",
        }

        processed = PayoneerService.process_webhook(webhook_data)

        assert processed["status"] == "failed"


class TestPaymentEmailNotifications:
    """Test payment confirmation and receipt emails"""

    @pytest.fixture
    def payment_data(self):
        """Create mock payment data"""
        return {
            "id": 123,
            "amount": 9999,  # in cents
            "currency": "GBP",
            "item_type": "course",
            "item_name": "Python Basics",
            "payoneer_order_id": "order_123",
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "status": "completed",
        }

    @pytest.fixture
    def user_data(self):
        """Create mock user data"""
        return {
            "email": "user@example.com",
            "full_name": "John Doe",
            "region": "UK",
        }

    @patch("services.email_service.smtplib.SMTP")
    def test_send_payment_confirmation_email(
        self, mock_smtp, payment_data, user_data
    ):
        """Test payment confirmation email is sent"""
        from services.email_service import EmailService

        email_service = EmailService()

        with patch.dict(
            "os.environ",
            {
                "SENDER_EMAIL": "noreply@test.com",
                "SENDER_PASSWORD": "test_password",
                "FRONTEND_URL": "http://localhost:3000",
            },
        ):
            result = email_service.send_payment_confirmation(
                user_email=user_data["email"],
                user_name=user_data["full_name"],
                payment_data=payment_data,
            )

        assert result is True

    @patch("services.email_service.smtplib.SMTP")
    def test_send_payment_receipt_email(
        self, mock_smtp, payment_data, user_data
    ):
        """Test payment receipt email is sent"""
        from services.email_service import EmailService

        email_service = EmailService()

        with patch.dict(
            "os.environ",
            {
                "SENDER_EMAIL": "noreply@test.com",
                "SENDER_PASSWORD": "test_password",
                "FRONTEND_URL": "http://localhost:3000",
            },
        ):
            result = email_service.send_payment_receipt(
                user_email=user_data["email"],
                user_name=user_data["full_name"],
                payment_data=payment_data,
            )

        assert result is True

    @patch("services.email_service.smtplib.SMTP")
    def test_send_refund_notification_email(
        self, mock_smtp, payment_data, user_data
    ):
        """Test refund notification email is sent"""
        from services.email_service import EmailService

        email_service = EmailService()

        with patch.dict(
            "os.environ",
            {
                "SENDER_EMAIL": "noreply@test.com",
                "SENDER_PASSWORD": "test_password",
                "SUPPORT_EMAIL": "support@test.com",
            },
        ):
            result = email_service.send_refund_notification(
                user_email=user_data["email"],
                user_name=user_data["full_name"],
                payment_data=payment_data,
            )

        assert result is True


class TestInvoiceGeneration:
    """Test PDF invoice generation"""

    @pytest.fixture
    def payment_data(self):
        """Create mock payment data"""
        return {
            "id": 123,
            "amount": 9999,  # in cents
            "currency": "GBP",
            "item_type": "course",
            "item_name": "Python Basics",
            "payoneer_order_id": "order_123",
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "status": "completed",
            "description": "Course: Python Basics",
        }

    @pytest.fixture
    def user_data(self):
        """Create mock user data"""
        return {
            "email": "user@example.com",
            "full_name": "John Doe",
            "region": "UK",
        }

    def test_generate_invoice_pdf(self, payment_data, user_data):
        """Test invoice PDF generation"""
        from services.invoice_generator import InvoiceGenerator

        generator = InvoiceGenerator()
        pdf_bytes = generator.generate_payment_invoice(
            payment_data=payment_data,
            user_data=user_data,
        )

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"  # PDF file signature

    def test_invoice_contains_order_details(self, payment_data, user_data):
        """Test generated invoice contains order details"""
        from services.invoice_generator import InvoiceGenerator

        generator = InvoiceGenerator()
        pdf_bytes = generator.generate_payment_invoice(
            payment_data=payment_data,
            user_data=user_data,
        )

        assert pdf_bytes is not None
        # Note: Full content verification requires PDF parsing library
        assert len(pdf_bytes) > 1000  # Reasonable PDF size

    def test_invoice_formatting_different_currencies(self):
        """Test invoice formatting with different currencies"""
        from services.invoice_generator import InvoiceGenerator

        generator = InvoiceGenerator()

        for currency in ["GBP", "USD", "EUR"]:
            payment_data = {
                "id": 123,
                "amount": 9999,
                "currency": currency,
                "item_type": "course",
                "item_name": "Test Course",
                "payoneer_order_id": "order_123",
                "created_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "description": "Test",
                "status": "completed",
            }
            user_data = {
                "email": "user@example.com",
                "full_name": "Test User",
                "region": "UK",
            }

            pdf_bytes = generator.generate_payment_invoice(
                payment_data=payment_data,
                user_data=user_data,
            )

            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0


class TestWebhookIntegration:
    """Integration tests for webhook processing"""

    @pytest.fixture
    def sample_webhook_payload(self):
        """Create complete webhook payload for integration testing"""
        return {
            "order_id": "integration_test_order_001",
            "transaction_id": "txn_integration_001",
            "status": "completed",
            "amount": 9999,
            "currency": "GBP",
            "customer_email": "integration@test.com",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def test_webhook_idempotency(self, sample_webhook_payload):
        """Test webhook processing is idempotent (same webhook processed twice)"""
        from services.payoneer_service import PayoneerService

        processed1 = PayoneerService.process_webhook(sample_webhook_payload)
        processed2 = PayoneerService.process_webhook(sample_webhook_payload)

        assert processed1 == processed2
        assert processed1["order_id"] == sample_webhook_payload["order_id"]

    def test_webhook_missing_required_fields(self):
        """Test webhook processing handles missing required fields"""
        from services.payoneer_service import PayoneerService

        incomplete_payload = {
            "order_id": "test_order",
            # Missing status, transaction_id, etc
        }

        processed = PayoneerService.process_webhook(incomplete_payload)
        # Should handle gracefully without crashing
        assert processed is not None


# Example of how to run these tests:
# pytest test_payment_webhook.py -v
# pytest test_payment_webhook.py -v --cov=services
# pytest test_payment_webhook.py::TestPaymentWebhook::test_valid_webhook_signature -v
