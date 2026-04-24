"""
Diploma Enrollment Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
from database import get_db
from models import User, Diploma, DiplomaEnrollment, Program, ProgramEnrollment, Payment
from schemas import DiplomaEnrollmentResponse, DiplomaEnrollmentDetailResponse
from auth import decode_access_token

router = APIRouter(prefix="/api/diploma-enrollments", tags=["diploma-enrollment"])


@router.post("/{diploma_id}/enroll", response_model=dict)
async def enroll_diploma(
    diploma_id: int,
    payment_id: int = None,
    token: str = None,
    db: Session = Depends(get_db)
):
    """
    Enroll user in a diploma
    For free diplomas: no payment needed
    For paid diplomas: payment_id required
    """
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get diploma
    diploma = db.query(Diploma).filter(Diploma.id == diploma_id).first()
    if not diploma:
        raise HTTPException(status_code=404, detail="Diploma not found")
    
    # Check if already enrolled
    existing_enrollment = db.query(DiplomaEnrollment).filter(
        DiplomaEnrollment.user_id == user.id,
        DiplomaEnrollment.diploma_id == diploma_id
    ).first()
    
    if existing_enrollment:
        raise HTTPException(
            status_code=400,
            detail="Already enrolled in this diploma"
        )
    
    # For paid diplomas, verify payment
    if diploma.fee > 0:
        if not payment_id:
            raise HTTPException(
                status_code=400,
                detail="Payment required for this diploma"
            )
        else:
            # Verify payment
            payment = db.query(Payment).filter(
                Payment.id == payment_id,
                Payment.user_id == user.id,
                Payment.status == "completed"
            ).first()
            
            if not payment:
                raise HTTPException(
                    status_code=400,
                    detail="Payment not verified"
                )
    
    # Create enrollment
    new_enrollment = DiplomaEnrollment(
        user_id=user.id,
        diploma_id=diploma_id,
        status="enrolled",
        payment_id=payment_id
    )
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    
    return {
        "id": new_enrollment.id,
        "user_id": new_enrollment.user_id,
        "diploma_id": new_enrollment.diploma_id,
        "status": new_enrollment.status,
        "enrolled_at": new_enrollment.enrolled_at,
        "message": "Successfully enrolled in diploma"
    }


@router.post("/{diploma_id}/start-learning", response_model=dict)
async def start_diploma_learning(
    diploma_id: int,
    token: str = None,
    db: Session = Depends(get_db)
):
    """Start learning a diploma"""
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get enrollment
    enrollment = db.query(DiplomaEnrollment).filter(
        DiplomaEnrollment.user_id == user.id,
        DiplomaEnrollment.diploma_id == diploma_id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="Not enrolled in this diploma")
    
    # Update enrollment
    enrollment.status = "active"
    enrollment.started_at = datetime.utcnow()
    db.commit()
    
    # Get first program in diploma
    first_program = db.query(Program).filter(
        Program.diploma_id == diploma_id
    ).order_by(Program.order).first()
    
    return {
        "message": "Diploma learning started",
        "enrollment_id": enrollment.id,
        "status": "active",
        "first_program_id": first_program.id if first_program else None,
        "started_at": enrollment.started_at
    }


@router.get("/{diploma_id}/my-enrollment", response_model=dict)
async def get_diploma_enrollment(
    diploma_id: int,
    token: str = None,
    db: Session = Depends(get_db)
):
    """Get current user's enrollment in a diploma"""
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    enrollment = db.query(DiplomaEnrollment).filter(
        DiplomaEnrollment.user_id == user.id,
        DiplomaEnrollment.diploma_id == diploma_id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="Not enrolled in this diploma")
    
    diploma = db.query(Diploma).filter(Diploma.id == diploma_id).first()
    
    return {
        "id": enrollment.id,
        "user_id": enrollment.user_id,
        "diploma_id": enrollment.diploma_id,
        "diploma_title": diploma.title if diploma else None,
        "status": enrollment.status,
        "enrolled_at": enrollment.enrolled_at,
        "started_at": enrollment.started_at,
        "completed_at": enrollment.completed_at,
        "progress_percentage": enrollment.progress_percentage
    }


@router.get("/{diploma_id}/diploma-progress", response_model=dict)
async def get_diploma_progress(
    diploma_id: int,
    token: str = None,
    db: Session = Depends(get_db)
):
    """Get detailed diploma progress for the current enrollment"""
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    enrollment = db.query(DiplomaEnrollment).filter(
        DiplomaEnrollment.user_id == user.id,
        DiplomaEnrollment.diploma_id == diploma_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Not enrolled in this diploma")

    diploma = db.query(Diploma).filter(Diploma.id == diploma_id).first()
    if not diploma:
        raise HTTPException(status_code=404, detail="Diploma not found")

    # Get all programs in the diploma
    programs = db.query(Program).filter(Program.diploma_id == diploma_id).order_by(Program.order).all()
    program_data = []

    for program in programs:
        # Check if user is enrolled in this program
        user_enrollment = db.query(ProgramEnrollment).filter(
            ProgramEnrollment.user_id == user.id,
            ProgramEnrollment.program_id == program.id
        ).first()
        
        program_data.append({
            "program_id": program.id,
            "program_title": program.title,
            "is_enrolled": user_enrollment is not None,
            "progress_percentage": user_enrollment.progress_percentage if user_enrollment else 0,
            "status": user_enrollment.status if user_enrollment else "not_enrolled"
        })

    # Calculate overall diploma progress
    enrolled_programs = [p for p in program_data if p["is_enrolled"]]
    if enrolled_programs:
        avg_progress = sum(p["progress_percentage"] for p in enrolled_programs) / len(enrolled_programs)
        overall_progress = int(avg_progress)
    else:
        overall_progress = 0
    
    # Update enrollment progress
    enrollment.progress_percentage = overall_progress
    db.commit()

    return {
        "enrollment_id": enrollment.id,
        "diploma_id": diploma.id,
        "diploma_title": diploma.title,
        "progress_percentage": overall_progress,
        "enrolled_at": enrollment.enrolled_at,
        "completed_at": enrollment.completed_at,
        "programs": program_data,
        "total_programs": len(programs),
        "enrolled_programs": len(enrolled_programs)
    }


@router.get("/my-diplomas", response_model=list[dict])
async def get_my_diploma_enrollments(
    token: str = None,
    skip: int = 0,
    limit: int = 10,
    status_filter: str = None,
    db: Session = Depends(get_db)
):
    """Get all diplomas the user is enrolled in"""
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    query = db.query(DiplomaEnrollment).filter(
        DiplomaEnrollment.user_id == user.id
    )
    
    if status_filter:
        query = query.filter(DiplomaEnrollment.status == status_filter)
    
    enrollments = query.offset(skip).limit(limit).all()
    
    result = []
    for enrollment in enrollments:
        diploma = db.query(Diploma).filter(Diploma.id == enrollment.diploma_id).first()
        if diploma:
            result.append({
                "enrollment_id": enrollment.id,
                "diploma_id": diploma.id,
                "diploma_title": diploma.title,
                "status": enrollment.status,
                "progress_percentage": enrollment.progress_percentage,
                "enrolled_at": enrollment.enrolled_at,
                "started_at": enrollment.started_at,
                "completed_at": enrollment.completed_at
            })
    
    return result
