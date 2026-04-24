"""
Program Enrollment Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
from database import get_db
from models import User, Program, ProgramEnrollment, Course, Enrollment, Payment
from schemas import ProgramEnrollmentResponse, ProgramEnrollmentDetailResponse
from auth import decode_access_token

router = APIRouter(prefix="/api/program-enrollments", tags=["program-enrollment"])


@router.post("/{program_id}/enroll", response_model=dict)
async def enroll_program(
    program_id: int,
    payment_id: int = None,
    token: str = None,
    db: Session = Depends(get_db)
):
    """
    Enroll user in a program
    For free programs: no payment needed
    For paid programs: payment_id required
    """
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get program
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    # Check if already enrolled
    existing_enrollment = db.query(ProgramEnrollment).filter(
        ProgramEnrollment.user_id == user.id,
        ProgramEnrollment.program_id == program_id
    ).first()
    
    if existing_enrollment:
        raise HTTPException(
            status_code=400,
            detail="Already enrolled in this program"
        )
    
    # For paid programs, verify payment
    if program.fee > 0:
        if not payment_id:
            raise HTTPException(
                status_code=400,
                detail="Payment required for this program"
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
    new_enrollment = ProgramEnrollment(
        user_id=user.id,
        program_id=program_id,
        status="enrolled",
        payment_id=payment_id
    )
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    
    return {
        "id": new_enrollment.id,
        "user_id": new_enrollment.user_id,
        "program_id": new_enrollment.program_id,
        "status": new_enrollment.status,
        "enrolled_at": new_enrollment.enrolled_at,
        "message": "Successfully enrolled in program"
    }


@router.post("/{program_id}/start-learning", response_model=dict)
async def start_program_learning(
    program_id: int,
    token: str = None,
    db: Session = Depends(get_db)
):
    """Start learning a program"""
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get enrollment
    enrollment = db.query(ProgramEnrollment).filter(
        ProgramEnrollment.user_id == user.id,
        ProgramEnrollment.program_id == program_id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="Not enrolled in this program")
    
    # Update enrollment
    enrollment.status = "active"
    enrollment.started_at = datetime.utcnow()
    db.commit()
    
    # Get first course in program
    first_course = db.query(Course).filter(
        Course.program_id == program_id
    ).order_by(Course.order).first()
    
    return {
        "message": "Program learning started",
        "enrollment_id": enrollment.id,
        "status": "active",
        "first_course_id": first_course.id if first_course else None,
        "started_at": enrollment.started_at
    }


@router.get("/{program_id}/my-enrollment", response_model=dict)
async def get_program_enrollment(
    program_id: int,
    token: str = None,
    db: Session = Depends(get_db)
):
    """Get current user's enrollment in a program"""
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    enrollment = db.query(ProgramEnrollment).filter(
        ProgramEnrollment.user_id == user.id,
        ProgramEnrollment.program_id == program_id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="Not enrolled in this program")
    
    program = db.query(Program).filter(Program.id == program_id).first()
    
    return {
        "id": enrollment.id,
        "user_id": enrollment.user_id,
        "program_id": enrollment.program_id,
        "program_title": program.title if program else None,
        "status": enrollment.status,
        "enrolled_at": enrollment.enrolled_at,
        "started_at": enrollment.started_at,
        "completed_at": enrollment.completed_at,
        "progress_percentage": enrollment.progress_percentage
    }


@router.get("/{program_id}/program-progress", response_model=dict)
async def get_program_progress(
    program_id: int,
    token: str = None,
    db: Session = Depends(get_db)
):
    """Get detailed program progress for the current enrollment"""
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    enrollment = db.query(ProgramEnrollment).filter(
        ProgramEnrollment.user_id == user.id,
        ProgramEnrollment.program_id == program_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Not enrolled in this program")

    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    # Get all courses in the program
    courses = db.query(Course).filter(Course.program_id == program_id).order_by(Course.order).all()
    course_data = []

    for course in courses:
        # Check if user is enrolled in this course
        user_enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user.id,
            Enrollment.course_id == course.id
        ).first()
        
        course_data.append({
            "course_id": course.id,
            "course_title": course.title,
            "is_enrolled": user_enrollment is not None,
            "progress_percentage": user_enrollment.progress_percentage if user_enrollment else 0,
            "status": user_enrollment.status if user_enrollment else "not_enrolled"
        })

    # Calculate overall program progress
    enrolled_courses = [c for c in course_data if c["is_enrolled"]]
    if enrolled_courses:
        avg_progress = sum(c["progress_percentage"] for c in enrolled_courses) / len(enrolled_courses)
        overall_progress = int(avg_progress)
    else:
        overall_progress = 0
    
    # Update enrollment progress
    enrollment.progress_percentage = overall_progress
    db.commit()

    return {
        "enrollment_id": enrollment.id,
        "program_id": program.id,
        "program_title": program.title,
        "progress_percentage": overall_progress,
        "enrolled_at": enrollment.enrolled_at,
        "completed_at": enrollment.completed_at,
        "courses": course_data,
        "total_courses": len(courses),
        "enrolled_courses": len(enrolled_courses)
    }


@router.get("/my-programs", response_model=list[dict])
async def get_my_program_enrollments(
    token: str = None,
    skip: int = 0,
    limit: int = 10,
    status_filter: str = None,
    db: Session = Depends(get_db)
):
    """Get all programs the user is enrolled in"""
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    query = db.query(ProgramEnrollment).filter(
        ProgramEnrollment.user_id == user.id
    )
    
    if status_filter:
        query = query.filter(ProgramEnrollment.status == status_filter)
    
    enrollments = query.offset(skip).limit(limit).all()
    
    result = []
    for enrollment in enrollments:
        program = db.query(Program).filter(Program.id == enrollment.program_id).first()
        if program:
            result.append({
                "enrollment_id": enrollment.id,
                "program_id": program.id,
                "program_title": program.title,
                "status": enrollment.status,
                "progress_percentage": enrollment.progress_percentage,
                "enrolled_at": enrollment.enrolled_at,
                "started_at": enrollment.started_at,
                "completed_at": enrollment.completed_at
            })
    
    return result
