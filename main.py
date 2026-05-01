from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from database import engine, Base
from routes.auth import router as auth_router
from routes.admin_auth import router as admin_auth_router
from routes.courses import router as courses_router
from routes.categories import router as categories_router
from routes.questions import router as questions_router
from routes.programs import router as programs_router, public_router as programs_public_router
from routes.diplomas import router as diplomas_router, public_router as diplomas_public_router
from routes.modules import router as modules_router
from routes.portfolio import router as portfolio_router
from routes.gamification import router as gamification_router
from routes.admin import router as admin_router
from routes.enrollment import router as enrollment_router
from routes.program_enrollment import router as program_enrollment_router
from routes.diploma_enrollment import router as diploma_enrollment_router
from routes.assessments import router as assessments_router
from routes.subscriptions import router as subscriptions_router
from routes.payments import router as payments_router
from routes.admin_payments import router as admin_payments_router
from routes.certificates import router as certificates_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sabipath API",
    description="Backend API for Sabipath application",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(admin_auth_router)
app.include_router(courses_router)
app.include_router(categories_router)
app.include_router(questions_router)
app.include_router(programs_router)
app.include_router(diplomas_router)
app.include_router(programs_public_router)
app.include_router(diplomas_public_router)
app.include_router(modules_router)
app.include_router(portfolio_router)
app.include_router(gamification_router)
app.include_router(admin_router)
app.include_router(enrollment_router)
app.include_router(program_enrollment_router)
app.include_router(diploma_enrollment_router)
app.include_router(assessments_router)
app.include_router(subscriptions_router)
app.include_router(payments_router)
app.include_router(admin_payments_router)
app.include_router(certificates_router)


@app.get("/")
async def root():
    return {"message": "Welcome to Sabipath API"}


@app.get("/health")
async def health():
    return {"status": "OK"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
