# Sabi Backend

FastAPI backend for the Sabi Educate platform.

## 🚀 Deployment to Render

### Option 1: Using Render Dashboard (Recommended)

1. **Connect Repository:**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Web Service"
   - Connect your `Sabi-Backend` GitHub repository

2. **Configure Service:**
   - **Name:** `sabi-backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Region:** Choose closest to your users
   - **Branch:** `main`

3. **Environment Variables:**
   ```
   DATABASE_URL=postgresql://user:password@host:5432/database
   DEBUG=false
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

4. **Deploy:**
   - Click "Create Web Service"
   - Render will build and deploy automatically

### Option 2: Using render.yaml (Blueprint)

1. **Push render.yaml:**
   ```bash
   git add render.yaml
   git commit -m "Add Render deployment config"
   git push origin main
   ```

2. **Connect via Blueprint:**
   - In Render Dashboard, click "New" → "Blueprint"
   - Connect your repository
   - Render will read `render.yaml` and create the service

## 🔧 Environment Setup

1. **Database:** Use PostgreSQL (Render, Neon, Supabase, etc.)
2. **Copy environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your production values
   ```

## 📋 API Documentation

Once deployed, visit `https://your-service-url/docs` for interactive API documentation.

## 🏗️ Local Development

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```