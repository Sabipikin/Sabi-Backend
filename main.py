from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routes.auth import router as auth_router
from routes.admin_auth import router as admin_auth_router
from routes.courses import router as courses_router
from routes.modules import router as modules_router
from routes.portfolio import router as portfolio_router
from routes.gamification import router as gamification_router
from routes.admin import router as admin_router
from routes.enrollment import router as enrollment_router
from routes.assessments import router as assessments_router
from routes.subscriptions import router as subscriptions_router
from sqlalchemy import inspect

# Create database tables only if they don't already exist
inspector = inspect(engine)
if not inspector.get_table_names():
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")

app = FastAPI(
    title="Sabipath API",
    description="Backend API for Sabipath application",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:8000", "http://127.0.0.1:3000", "http://127.0.0.1:3001", "http://127.0.0.1:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(admin_auth_router)
app.include_router(courses_router)
app.include_router(modules_router)
app.include_router(portfolio_router)
app.include_router(gamification_router)
app.include_router(admin_router)
app.include_router(enrollment_router)
app.include_router(assessments_router)
app.include_router(subscriptions_router)


@app.get("/")
async def root():
    return {"message": "Welcome to Sabipath API"}


@app.get("/health")
async def health():
    return {"status": "OK"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
