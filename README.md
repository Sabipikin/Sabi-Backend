# Sabi Backend

FastAPI backend for the Sabi Educate platform with payment processing, authentication, and course management.

---

## 📋 Table of Contents

1. [Quick Start](#-quick-start)
2. [API Keys & Environment Variables](#-api-keys--environment-variables)
3. [Local Development](#-local-development)
4. [Deployment](#-deployment)
5. [API Documentation](#-api-documentation)
6. [Project Structure](#-project-structure)

---

## 🚀 Quick Start

### Local Setup

```bash
# Clone repository
git clone <your-repo-url>
cd sabi-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Run development server
uvicorn main:app --reload
```

**Visit:** `http://localhost:8000/docs` for API documentation

---

## 🔐 API Keys & Environment Variables

### **Database Configuration**

| Variable | Description | How to Get |
|----------|-------------|-----------|
| `DATABASE_URL` | PostgreSQL connection string | See [Database Setup](#database-setup) |

#### Database Setup

**Option 1: Neon (Recommended for Production)**
1. Go to [Neon Console](https://console.neon.tech/)
2. Click "New Project"
3. Select PostgreSQL version
4. Copy connection string from "Connection string" tab
5. Select "Connection pooling" for better performance
6. Format: `postgresql://user:password@host:5432/database`

**Option 2: Render PostgreSQL**
1. In [Render Dashboard](https://dashboard.render.com), click "New" → "PostgreSQL"
2. Configure instance (choose free tier for testing)
3. Copy connection string

**Option 3: Supabase**
1. Go to [Supabase](https://supabase.com/)
2. Create new project
3. In Settings → Database, copy connection string
4. Use pooler connection for better performance

---

### **Authentication & Security**

| Variable | Description | How to Get | Example |
|----------|-------------|-----------|---------|
| `SECRET_KEY` | JWT signing key | Generate random 32+ char string | `your-random-secret-key-at-least-32-chars-long` |
| `ALGORITHM` | JWT algorithm | Use `HS256` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry time | Set as needed (default: 30) | `30` |

#### Generate SECRET_KEY

```bash
# Option 1: Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 2: Using OpenSSL
openssl rand -hex 32
```

---

### **Payoneer Payment Gateway**

| Variable | Description | How to Get | Example |
|----------|-------------|-----------|---------|
| `PAYONEER_API_URL` | Payoneer API endpoint | Set accordingly | `https://api.payoneer.com/v2` |
| `PAYONEER_CLIENT_ID` | OAuth client ID | [Payoneer Business Dashboard](https://business.payoneer.com/) → Settings → API Settings | `abc123xyz789` |
| `PAYONEER_CLIENT_SECRET` | OAuth client secret | Payoneer Business Dashboard → API Settings → Generate Secret | `secret_xyz_abc_123` |
| `PAYONEER_PARTNER_ID` | Payoneer partner ID | Payoneer Business Account Settings | `PARTNER_12345` |
| `PAYONEER_WEBHOOK_SECRET` | Webhook signature key | Payoneer Dashboard → Webhooks → Generate Secret | `webhook_secret_key` |
| `PAYONEER_WEBHOOK_URL` | Where Payoneer sends updates | Your backend webhook endpoint | `https://your-domain.onrender.com/api/payments/webhook` |

#### Get Payoneer Credentials

1. **Create Payoneer Business Account**
   - Go to [Payoneer Business](https://business.payoneer.com/)
   - Sign up or log in
   - Verify your account

2. **Get API Credentials**
   - Navigate to Settings → API Settings / Developer
   - Click "Create Application"
   - Fill in app details (Name: "Sabi Educate")
   - Generate credentials
   - Copy CLIENT_ID and CLIENT_SECRET

3. **Get Partner ID**
   - Go to Account Settings
   - Look for "Partner ID" or "Merchant ID"
   - Copy the value

4. **Setup Webhooks**
   - Go to Webhooks section
   - Add webhook URL: `https://your-domain.onrender.com/api/payments/webhook`
   - Generate webhook secret
   - Select events: Payment Completed, Failed, Pending, Refunded

---

### **Email Configuration (Payment Notifications)**

#### Gmail (Recommended for Testing)

| Variable | Description | How to Get |
|----------|-------------|-----------|
| `SMTP_SERVER` | Gmail SMTP | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SENDER_EMAIL` | Your Gmail address | Your email address |
| `SENDER_PASSWORD` | App-specific password | See below |
| `SENDER_NAME` | Display name | `Sabi Educate` |
| `SUPPORT_EMAIL` | Support email | `support@sabieducate.com` |

**Generate Gmail App Password:**
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (if not enabled)
3. Click "App passwords"
4. Select "Mail" and "Windows Computer"
5. Copy the 16-character password

#### SendGrid (Production)

| Variable | Value |
|----------|-------|
| `SMTP_SERVER` | `smtp.sendgrid.net` |
| `SMTP_PORT` | `587` |
| `SENDER_PASSWORD` | SendGrid API Key |

**Get SendGrid API Key:**
1. Create account at [SendGrid](https://sendgrid.com/)
2. Go to Settings → API Keys
3. Click "Create API Key"
4. Copy the key

---

### **Company Information (For Invoices)**

| Variable | Description | Example |
|----------|-------------|---------|
| `COMPANY_NAME` | Your company name | `Sabi Educate Ltd` |
| `COMPANY_ADDRESS` | Company address | `123 Business Street, London, UK` |
| `COMPANY_PHONE` | Company phone | `+44-20-1234-5678` |

---

### **Application Settings**

| Variable | Description | Value |
|----------|-------------|-------|
| `DEBUG` | Debug mode | `true` (development) / `false` (production) |
| `CORS_ORIGINS` | Allowed frontend domains | `["https://frontend-domain.com", "https://admin-domain.com"]` |

---

## 📝 Complete .env Template

```bash
# ============================================
# DATABASE CONFIGURATION
# ============================================
DATABASE_URL=postgresql://user:password@host:5432/database

# ============================================
# AUTHENTICATION & SECURITY
# ============================================
SECRET_KEY=your-random-secret-key-at-least-32-chars-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ============================================
# PAYONEER PAYMENT GATEWAY
# ============================================
PAYONEER_API_URL=https://api.payoneer.com/v2
PAYONEER_CLIENT_ID=your_client_id_here
PAYONEER_CLIENT_SECRET=your_client_secret_key_here
PAYONEER_PARTNER_ID=your_partner_id_here
PAYONEER_WEBHOOK_SECRET=your_webhook_secret_key_here
PAYONEER_WEBHOOK_URL=https://your-backend-domain.onrender.com/api/payments/webhook

# ============================================
# EMAIL CONFIGURATION
# ============================================
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your_app_password_here
SENDER_NAME=Sabi Educate
SUPPORT_EMAIL=support@sabieducate.com

# ============================================
# INVOICE GENERATION
# ============================================
COMPANY_NAME=Sabi Educate Ltd
COMPANY_ADDRESS=123 Business Street, London, UK
COMPANY_PHONE=+44-20-1234-5678

# ============================================
# APPLICATION SETTINGS
# ============================================
DEBUG=false
CORS_ORIGINS=["https://sabieducate.netlify.app", "https://admin.sabieducate.com"]
FRONTEND_URL=https://sabieducate.netlify.app
BACKEND_URL=https://your-backend-domain.onrender.com
```

---

## 🏗️ Local Development

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- pip package manager

### Setup Steps

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
cp .env.example .env

# 4. Update .env with local values
# - DATABASE_URL: PostgreSQL connection
# - SECRET_KEY: Generate using: python -c "import secrets; print(secrets.token_urlsafe(32))"
# - Payoneer credentials: Use sandbox values (optional for local testing)

# 5. Run migrations (if using Alembic)
alembic upgrade head

# 6. Start development server
uvicorn main:app --reload

# 7. Test API
# Visit: http://localhost:8000/docs
# Or: http://localhost:8000/redoc
```

### Project Structure

```
sabi-backend/
├── main.py                 # FastAPI application
├── auth.py                 # Authentication utilities
├── database.py             # Database configuration
├── models.py               # SQLAlchemy models
├── schemas.py              # Pydantic schemas
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── routes/                 # API endpoints
│   ├── auth.py
│   ├── payments.py
│   ├── subscriptions.py
│   ├── courses.py
│   ├── programs.py
│   ├── diplomas.py
│   └── ...
├── services/               # Business logic
│   ├── email_service.py
│   ├── invoice_generator.py
│   └── payoneer_service.py
├── templates/              # Email templates
│   └── emails/
├── tests/                  # Test files
└── README.md
```

---

## 🚀 Deployment

### Option 1: Deploy to Render (Recommended)

#### Using Render Dashboard

1. **Connect Repository:**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service:**
   - **Name:** `sabi-backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Region:** Choose closest to your users
   - **Branch:** `main`

3. **Add Environment Variables:**
   - Click "Environment"
   - Add all variables from `.env` template above
   - For DATABASE_URL: Use Neon PostgreSQL
   - For PAYONEER_WEBHOOK_URL: Use your Render service URL

4. **Deploy:**
   - Click "Create Web Service"
   - Render builds and deploys automatically

#### Using render.yaml (Blueprint)

1. Push `render.yaml` to repository:
   ```bash
   git add render.yaml
   git commit -m "Add Render deployment config"
   git push origin main
   ```

2. In Render Dashboard:
   - Click "New" → "Blueprint"
   - Connect your repository
   - Render reads `render.yaml` and creates services

### Option 2: Deploy to Other Platforms

#### Heroku
```bash
heroku login
heroku create sabi-backend
git push heroku main
heroku config:set DATABASE_URL=<your-db-url>
heroku config:set SECRET_KEY=<generated-key>
# Set other environment variables...
```

#### Railway
1. Go to [Railway](https://railway.app/)
2. Create new project
3. Connect GitHub repository
4. Add environment variables
5. Deploy

#### AWS EC2
```bash
# SSH into EC2 instance
ssh -i key.pem ubuntu@your-instance-ip

# Install Python and dependencies
sudo apt update
sudo apt install python3-pip python3-venv postgresql-client

# Clone and setup
git clone <repo-url>
cd sabi-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
nano .env

# Run with gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

---

## 📚 API Documentation

### Access Documentation

After deployment, visit:
- **Swagger UI:** `https://your-backend-url/docs`
- **ReDoc:** `https://your-backend-url/redoc`
- **OpenAPI JSON:** `https://your-backend-url/openapi.json`

### Key API Endpoints

**Authentication:**
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/refresh` - Refresh token

**Payments:**
- `POST /api/payments/checkout` - Create payment checkout
- `GET /api/payments/{payment_id}` - Get payment details
- `POST /api/payments/webhook` - Payoneer webhook

**Subscriptions:**
- `POST /api/subscriptions/checkout` - Create subscription
- `GET /api/subscriptions/plans` - List subscription plans
- `GET /api/subscriptions/current` - Get current subscription
- `POST /api/subscriptions/{id}/cancel` - Cancel subscription

**Courses:**
- `GET /api/courses` - List all courses
- `GET /api/courses/{id}` - Get course details
- `POST /api/courses` - Create course (admin)

**Admin:**
- `GET /api/admin/payments` - List all payments
- `GET /api/admin/subscriptions/analytics` - Subscription analytics
- `POST /api/admin/subscriptions/plans` - Create subscription plan

---

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run specific test file
pytest tests/test_payment_webhook.py

# Run with coverage
pytest --cov=. tests/
```

### Test Payment Webhook

```bash
# Run webhook tests
pytest tests/test_payment_webhook.py -v

# Tests include:
# - Webhook signature verification
# - Email notifications
# - Invoice generation
# - Payment status updates
```

---

## 🐛 Troubleshooting

### Common Issues

**Issue:** `ModuleNotFoundError: No module named 'main'`
- **Solution:** Ensure you're in the correct directory and virtual environment is activated

**Issue:** `SQLALCHEMY_DATABASE_URL not set`
- **Solution:** Add `DATABASE_URL` to `.env` file

**Issue:** `PAYONEER_CLIENT_ID not set`
- **Solution:** Add all Payoneer variables to `.env` from [API Keys section](#-api-keys--environment-variables)

**Issue:** `Email not sending`
- **Solution:** 
  - For Gmail: Use 16-character App Password
  - Verify SMTP credentials are correct
  - Check firewall allows port 587

**Issue:** `Webhook signature verification failed`
- **Solution:** Verify `PAYONEER_WEBHOOK_SECRET` matches Payoneer dashboard

---

## 📞 Support

For additional help:
- Check [PAYONEER_ENV_GUIDE.md](./PAYONEER_ENV_GUIDE.md) for detailed payment setup
- Review [Payoneer API Documentation](https://payoneer-business.readme.io/)
- Check logs: `uvicorn main:app --log-level debug`

---

## 📄 License

This project is private and confidential.

---

## ✅ Deployment Checklist

Before deploying to production:

- [ ] All API keys configured in environment variables
- [ ] Database URL set to production PostgreSQL (Neon recommended)
- [ ] SECRET_KEY generated and stored securely
- [ ] Debug mode set to `false`
- [ ] CORS_ORIGINS updated with production domains
- [ ] PAYONEER_WEBHOOK_URL set to production backend URL
- [ ] Email credentials configured (Gmail App Password or SendGrid)
- [ ] Tests pass: `pytest`
- [ ] All routes tested in Swagger UI
- [ ] Payment webhook tested with test payment
- [ ] SSL certificate configured (automatic on Render)
- [ ] Monitoring and logging setup
- [ ] Backup strategy for database implemented

---

Last Updated: April 2026