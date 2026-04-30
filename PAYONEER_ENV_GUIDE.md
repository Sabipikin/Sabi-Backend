# Payoneer Payment Integration - Environment Variables Setup

## Quick Reference

Copy and paste the following template into your `.env` file, then fill in the placeholders with your actual credentials.

```bash
# ============================================
# PAYONEER PAYMENT GATEWAY CONFIGURATION
# ============================================

# Payoneer API Endpoint
# Production: https://api.payoneer.com/v2
# Sandbox: https://sandbox.payoneer.com/v2
PAYONEER_API_URL=https://api.payoneer.com/v2

# OAuth Credentials (Get from Payoneer Business Dashboard)
# https://business.payoneer.com/ → Settings → API/Developer Settings
PAYONEER_CLIENT_ID=your_client_id_here
PAYONEER_CLIENT_SECRET=your_client_secret_key_here

# Payoneer Partner ID (from your account settings)
PAYONEER_PARTNER_ID=your_partner_id_here

# Webhook Secret (Generate in Payoneer Dashboard → Webhooks)
PAYONEER_WEBHOOK_SECRET=your_webhook_secret_key_here

# Webhook Endpoint (where Payoneer sends payment updates)
PAYONEER_WEBHOOK_URL=https://your-backend-domain.onrender.com/api/payments/webhook

# ============================================
# EMAIL CONFIGURATION (Payment Notifications)
# ============================================

# SMTP Server
# Gmail: smtp.gmail.com
# SendGrid: smtp.sendgrid.net
SMTP_SERVER=smtp.gmail.com

# SMTP Port (587 for TLS, 465 for SSL)
SMTP_PORT=587

# Sender Email Address
SENDER_EMAIL=noreply@sabieducate.com

# SMTP Password or API Key
# Gmail: Use App Password from https://myaccount.google.com/apppasswords
# SendGrid: Use API Key
SENDER_PASSWORD=your_app_password_or_api_key_here

# Display name for emails
SENDER_NAME=Sabi Educate

# Support email shown in payment notifications
SUPPORT_EMAIL=support@sabieducate.com

# ============================================
# INVOICE GENERATION (Company Details)
# ============================================

COMPANY_NAME=Sabi Educate Ltd
COMPANY_ADDRESS=123 Business Street, London, UK
COMPANY_PHONE=+44-20-1234-5678

# ============================================
# FRONTEND URLs (for payment redirects)
# ============================================

FRONTEND_URL=https://sabieducate.netlify.app
BACKEND_URL=https://your-backend-domain.onrender.com
```

---

## How to Get Each Credential

### 1. PAYONEER_CLIENT_ID & PAYONEER_CLIENT_SECRET

**Steps:**
1. Go to [Payoneer Business Platform](https://business.payoneer.com/)
2. Log in with your business account
3. Navigate to **Settings** → **API Settings** or **Developer**
4. Click **Create Application** or **Add Application**
5. Fill in application details
6. Save the generated credentials

**What to fill in:**
```bash
PAYONEER_CLIENT_ID=abc123def456ghi789jkl012  # Example
PAYONEER_CLIENT_SECRET=secret_xyz789abc123def456ghi  # Example
```

### 2. PAYONEER_PARTNER_ID

**Steps:**
1. In Payoneer Business Dashboard, go to **Account Settings**
2. Look for **Partner ID** or **Merchant ID**
3. Copy the ID

**What to fill in:**
```bash
PAYONEER_PARTNER_ID=PARTNER_12345_ABC  # Example
```

### 3. PAYONEER_WEBHOOK_SECRET

**Steps:**
1. In Payoneer Business Dashboard, go to **Webhooks** or **Notification Settings**
2. Find **Webhook Secret** or **Signing Key**
3. Click **Generate** or copy the existing secret
4. Make sure webhook URL is set to: `https://your-backend-domain.onrender.com/api/payments/webhook`

**What to fill in:**
```bash
PAYONEER_WEBHOOK_SECRET=webhook_secret_key_12345_xyz  # Example
```

### 4. SMTP Credentials (Gmail)

**Steps:**
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (if not already enabled)
3. Generate **App Password** for "Mail" and "Windows Computer"
4. Copy the 16-character password

**What to fill in:**
```bash
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=abcd efgh ijkl mnop  # 16-character app password
```

### 5. SMTP Credentials (SendGrid Alternative)

**Steps:**
1. Create account at [SendGrid](https://sendgrid.com/)
2. Go to **Settings** → **API Keys**
3. Click **Create API Key**
4. Copy the key

**What to fill in:**
```bash
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SENDER_EMAIL=noreply@yourdomain.com
SENDER_PASSWORD=SG.your_sendgrid_api_key_here
```

---

## Environment Variable Details

### Payment Processing Variables

| Variable | Purpose | Format | Example |
|----------|---------|--------|---------|
| `PAYONEER_API_URL` | Payoneer API endpoint | URL | `https://api.payoneer.com/v2` |
| `PAYONEER_CLIENT_ID` | OAuth client identifier | String (50 chars) | `abc123xyz789` |
| `PAYONEER_CLIENT_SECRET` | OAuth client secret key | String (100+ chars) | `secret_key_string` |
| `PAYONEER_PARTNER_ID` | Your Payoneer partner ID | String (20-50 chars) | `PARTNER_ID_123` |
| `PAYONEER_WEBHOOK_SECRET` | Webhook signature key | String (50+ chars) | `webhook_secret_key` |
| `PAYONEER_WEBHOOK_URL` | Where to send webhooks | URL (HTTPS) | `https://backend.example.com/api/payments/webhook` |

### Email Variables

| Variable | Purpose | Options | Example |
|----------|---------|---------|---------|
| `SMTP_SERVER` | Email service | `smtp.gmail.com` or `smtp.sendgrid.net` | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` (TLS) or `465` (SSL) | `587` |
| `SENDER_EMAIL` | From address | Valid email | `noreply@sabieducate.com` |
| `SENDER_PASSWORD` | SMTP password | API key or app password | `16_char_app_pwd` |
| `SENDER_NAME` | Display name | Any text | `Sabi Educate` |
| `SUPPORT_EMAIL` | Reply-to address | Valid email | `support@sabieducate.com` |

### Invoice Variables

| Variable | Purpose | Format | Example |
|----------|---------|--------|---------|
| `COMPANY_NAME` | Invoice company name | Text | `Sabi Educate Ltd` |
| `COMPANY_ADDRESS` | Invoice address | Text | `123 Street, London, UK` |
| `COMPANY_PHONE` | Invoice phone | Phone number | `+44-20-1234-5678` |

---

## Testing Your Configuration

### Test Payment Flow

```bash
# 1. Start the backend
python -m uvicorn main:app --reload

# 2. Create a test payment
curl -X POST http://localhost:8000/api/payments/checkout \
  -H "Authorization: Bearer YOUR_TEST_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "item_type": "course",
    "item_id": 1,
    "currency": "gbp"
  }'

# 3. You should get a checkout_url from Payoneer
# 4. Redirect user to that URL to complete payment
# 5. After payment, Payoneer will send webhook to your backend
```

### Test Email Configuration

```python
from services.email_service import EmailService

email_service = EmailService()
email_service.send_email(
    to_email="your-email@example.com",
    subject="Test Email",
    template_name="payment_confirmation.html",
    context={
        "user_name": "John Doe",
        "order_date": "2024-01-01",
        "item_name": "Test Course",
        "amount": "99.99",
        "order_id": "12345"
    }
)
```

---

## Sandbox vs Production

### Sandbox (Testing)

```bash
PAYONEER_API_URL=https://sandbox.payoneer.com/v2
PAYONEER_CLIENT_ID=sandbox_test_client_id
PAYONEER_CLIENT_SECRET=sandbox_test_secret
DEBUG=true
```

**Use sandbox for:**
- Development
- Testing payment flows
- Testing webhook integration

### Production

```bash
PAYONEER_API_URL=https://api.payoneer.com/v2
PAYONEER_CLIENT_ID=your_production_client_id
PAYONEER_CLIENT_SECRET=your_production_secret
DEBUG=false
```

**Only use production when:**
- All testing is complete
- You're ready to accept real payments
- SSL/HTTPS is properly configured

---

## Common Issues & Solutions

### ❌ "PAYONEER_CLIENT_ID not set"
**Solution**: Make sure you've added it to `.env` file and restarted the application

### ❌ "Failed to authenticate with Payoneer"
**Solution**: 
- Verify CLIENT_ID and CLIENT_SECRET are correct
- Check if you're using the right API URL (sandbox vs production)
- Make sure credentials haven't expired

### ❌ "Webhook signature verification failed"
**Solution**:
- Verify PAYONEER_WEBHOOK_SECRET matches Payoneer dashboard
- Check webhook endpoint is publicly accessible
- Ensure HTTPS is used

### ❌ "Email not sending"
**Solution**:
- For Gmail: Use 16-character App Password (not regular password)
- Check SMTP_SERVER and SMTP_PORT are correct
- Verify SENDER_EMAIL has correct credentials

---

## Security Checklist

- [ ] Add `.env` to `.gitignore`
- [ ] Never commit credentials to Git
- [ ] Use strong CLIENT_SECRET (Payoneer generates this)
- [ ] Rotate credentials periodically
- [ ] Use HTTPS for all endpoints
- [ ] Verify webhook signatures on every request
- [ ] Keep SMTP password/API key secret
- [ ] Review webhook logs regularly
- [ ] Monitor failed payment attempts

---

## Additional Resources

- [Payoneer Business API Docs](https://payoneer-business.readme.io/)
- [Payoneer OAuth Flow](https://payoneer-business.readme.io/docs/oauth-flow)
- [Payoneer Webhook Events](https://payoneer-business.readme.io/docs/webhook-events)
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)
- [SendGrid Documentation](https://docs.sendgrid.com/)

---

## Next Steps After Setup

1. Test payment creation
2. Test webhook delivery
3. Test email notifications
4. Monitor logs for errors
5. Deploy to production
6. Monitor transactions and webhooks
7. Handle edge cases and errors
