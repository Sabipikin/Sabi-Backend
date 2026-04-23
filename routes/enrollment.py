"""
Course Enrollment and Payment Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from database import get_db
from models import User, Course, Enrollment, Payment, Subscription, LessonContent, Module, ContentProgress
from schemas import (
    EnrollmentDetailResponse,
    ContentProgressCreate,
    ContentProgressResponse,
    CourseProgressDetailResponse,
)
from auth import decode_access_token

router = APIRouter(prefix="/api/enrollments", tags=["course-enrollment"])


# ============ Course Access Control ============

def check_course_access(user_id: int, course_id: int, db: Session) -> bool:
    """
    Check if user has access to a course
    Returns True if:
    - Course is free
    - User has valid enrollment with payment (for paid courses)
    - User has active subscription (for paid courses)
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        return False


def aggregate_course_progress(user_id: int, course_id: int, db: Session) -> Optional[Enrollment]:
    """Recalculate and persist the enrollment progress percentage for a course."""
    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.course_id == course_id
    ).first()

    if not enrollment:
        return None

    total_items = db.query(LessonContent).join(
        Module, LessonContent.module_id == Module.id
    ).filter(
        Module.course_id == course_id
    ).count()

    completed_items = db.query(ContentProgress).join(
        LessonContent, ContentProgress.content_id == LessonContent.id
    ).join(
        Module, LessonContent.module_id == Module.id
    ).filter(
        ContentProgress.user_id == user_id,
        Module.course_id == course_id,
        ContentProgress.is_completed == True
    ).count()

    enrollment.progress_percentage = int((completed_items / total_items) * 100) if total_items else 0

    if total_items > 0 and enrollment.progress_percentage >= 100:
        if enrollment.status != "completed":
            enrollment.status = "completed"
            enrollment.completed_at = datetime.utcnow()
    elif enrollment.status == "completed":
        enrollment.status = "active" if enrollment.started_at else "enrolled"
        enrollment.completed_at = None

    db.commit()
    db.refresh(enrollment)
    return enrollment
    
    # Free courses - everyone has access
    if course.fee == 0:
        return True
    
    # Check if user is enrolled with payment
    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.course_id == course_id,
        Enrollment.status.in_(["enrolled", "active", "completed"])
    ).first()
    
    if enrollment and enrollment.payment_id:
        # Verify payment was completed
        payment = db.query(Payment).filter(
            Payment.id == enrollment.payment_id,
            Payment.status == "completed"
        ).first()
        if payment:
            return True
    
    # Check if user has active subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status == "active",
        Subscription.end_date > datetime.utcnow()
    ).first()
    if subscription:
        return True
    
    return False


# ============ Enrollment Endpoints ============

@router.get("/{course_id}/can-enroll", response_model=dict)
async def can_enroll_course(
    course_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Check if user can enroll in a course"""
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if already enrolled
    existing_enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == user.id,
        Enrollment.course_id == course_id
    ).first()
    
    if existing_enrollment:
        return {
            "can_enroll": False,
            "reason": "already_enrolled",
            "enrollment_id": existing_enrollment.id,
            "status": existing_enrollment.status
        }
    
    # Check if course is free
    if course.fee == 0:
        return {
            "can_enroll": True,
            "reason": "free_course",
            "requires_payment": False
        }
    
    # Check if user has subscription
    has_subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active",
        Subscription.end_date > datetime.utcnow()
    ).first()
    
    if has_subscription:
        return {
            "can_enroll": True,
            "reason": "has_subscription",
            "requires_payment": False
        }
    
    # Need payment
    final_price = course.fee
    if course.is_on_promo:
        final_price = course.fee - course.promo_amount
    
    return {
        "can_enroll": True,
        "reason": "paid_course",
        "requires_payment": True,
        "price": course.fee,
        "promo_amount": course.promo_amount if course.is_on_promo else 0,
        "final_price": final_price
    }


@router.post("/{course_id}/enroll", response_model=dict)
async def enroll_course(
    course_id: int,
    payment_id: int = None,
    token: str = None,
    db: Session = Depends(get_db)
):
    """
    Enroll user in a course
    For free courses: no payment needed
    For paid courses: payment_id required or subscription required
    """
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get course
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if already enrolled
    existing_enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == user.id,
        Enrollment.course_id == course_id
    ).first()
    
    if existing_enrollment:
        raise HTTPException(
            status_code=400,
            detail="Already enrolled in this course"
        )
    
    # For paid courses, verify payment
    if course.fee > 0:
        if not payment_id:
            # Check if user has subscription
            has_subscription = db.query(Subscription).filter(
                Subscription.user_id == user.id,
                Subscription.status == "active",
                Subscription.end_date > datetime.utcnow()
            ).first()
            
            if not has_subscription:
                raise HTTPException(
                    status_code=400,
                    detail="Payment or subscription required for this course"
                )
            payment_id = None
        else:
            # Verify payment
            payment = db.query(Payment).filter(
                Payment.id == payment_id,
                Payment.user_id == user.id,
                Payment.status == "completed",
                Payment.course_id == course_id
            ).first()
            
            if not payment:
                raise HTTPException(
                    status_code=400,
                    detail="Payment not verified"
                )
    
    # Create enrollment
    new_enrollment = Enrollment(
        user_id=user.id,
        course_id=course_id,
        status="enrolled",  # Not started learning yet
        payment_id=payment_id
    )
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    
    return {
        "id": new_enrollment.id,
        "user_id": new_enrollment.user_id,
        "course_id": new_enrollment.course_id,
        "status": new_enrollment.status,
        "enrolled_at": new_enrollment.enrolled_at,
        "message": "Successfully enrolled in course"
    }


@router.post("/{course_id}/start-learning", response_model=dict)
async def start_learning(
    course_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """
    Start learning a course
    Changes enrollment status from 'enrolled' to 'active'
    """
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get enrollment
    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == user.id,
        Enrollment.course_id == course_id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="Not enrolled in this course")
    
    # Check if can access
    if not check_course_access(user.id, course_id, db):
        raise HTTPException(status_code=403, detail="Access denied to this course")
    
    # Update enrollment
    enrollment.status = "active"
    enrollment.started_at = datetime.utcnow()
    db.commit()
    
    # Get first module
    course = db.query(Course).filter(Course.id == course_id).first()
    first_module = db.query(Module).filter(
        Module.course_id == course_id
    ).order_by(Module.order).first()
    
    return {
        "message": "Learning started",
        "enrollment_id": enrollment.id,
        "status": "active",
        "first_module_id": first_module.id if first_module else None,
        "started_at": enrollment.started_at
    }


@router.get("/{course_id}/my-enrollment", response_model=dict)
async def get_my_enrollment(
    course_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Get current user's enrollment in a course"""
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == user.id,
        Enrollment.course_id == course_id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="Not enrolled in this course")
    
    return {
        "id": enrollment.id,
        "user_id": enrollment.user_id,
        "course_id": enrollment.course_id,
        "status": enrollment.status,
        "enrolled_at": enrollment.enrolled_at,
        "started_at": enrollment.started_at,
        "completed_at": enrollment.completed_at,
        "progress_percentage": enrollment.progress_percentage
    }


@router.get("/{course_id}/course-progress", response_model=CourseProgressDetailResponse)
async def get_course_progress(
    course_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Get detailed course progress for the current enrollment."""
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == user.id,
        Enrollment.course_id == course_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Not enrolled in this course")

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    modules = db.query(Module).filter(Module.course_id == course_id).order_by(Module.order).all()
    module_data = []

    for module in modules:
        total_items = db.query(LessonContent).filter(LessonContent.module_id == module.id).count()
        completed_items = db.query(ContentProgress).join(
            LessonContent, ContentProgress.content_id == LessonContent.id
        ).filter(
            ContentProgress.user_id == user.id,
            LessonContent.module_id == module.id,
            ContentProgress.is_completed == True
        ).count()

        module_data.append({
            "module_id": module.id,
            "module_title": module.title,
            "total_items": total_items,
            "completed_items": completed_items,
            "progress_percentage": int((completed_items / total_items) * 100) if total_items else 0
        })

    return {
        "enrollment_id": enrollment.id,
        "course_id": course.id,
        "course_title": course.title,
        "progress_percentage": enrollment.progress_percentage,
        "enrolled_at": enrollment.enrolled_at,
        "completed_at": enrollment.completed_at,
        "modules": module_data
    }


@router.get("/{course_id}/modules", response_model=list[dict])
async def get_course_modules(
    course_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Get modules for a course (with access control)"""
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check access
    if not check_course_access(user.id, course_id, db):
        raise HTTPException(status_code=403, detail="Access denied to this course")
    
    # Get modules
    modules = db.query(Module).filter(
        Module.course_id == course_id
    ).order_by(Module.order).all()
    
    return [
        {
            "id": m.id,
            "title": m.title,
            "description": m.description,
            "order": m.order
        }
        for m in modules
    ]


@router.get("/{course_id}/module/{module_id}/content", response_model=list[dict])
async def get_module_content(
    course_id: int,
    module_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Get content for a module (with access control)"""
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check access
    if not check_course_access(user.id, course_id, db):
        raise HTTPException(status_code=403, detail="Access denied to this course")
    
    # Get content
    content_items = db.query(LessonContent).filter(
        LessonContent.module_id == module_id
    ).order_by(LessonContent.order).all()
    
    result = []
    for content in content_items:
        item = {
            "id": content.id,
            "title": content.title,
            "description": content.description,
            "content_type": content.content_type,
            "order": content.order,
            "is_required": content.is_required
        }
        
        # Add type-specific fields
        if content.content_type == "video":
            item["video_url"] = content.video_url
            item["duration_minutes"] = content.video_duration_minutes
        elif content.content_type == "notes":
            item["notes_content"] = content.notes_content
        elif content.content_type == "slides":
            item["slides_url"] = content.slides_url
        elif content.content_type == "assessment":
            item["assessment_type"] = content.assessment_type
            item["total_questions"] = content.total_questions
            item["passing_score"] = content.passing_score
            item["time_limit_minutes"] = content.time_limit_minutes
        
        # Get user's progress on this content
        progress = db.query(ContentProgress).filter(
            ContentProgress.user_id == user.id,
            ContentProgress.content_id == content.id
        ).first()
        
        if progress:
            item["progress"] = {
                "view_progress_percentage": progress.view_progress_percentage,
                "is_completed": progress.is_completed,
                "time_spent_minutes": progress.time_spent_minutes
            }
        else:
            item["progress"] = {
                "view_progress_percentage": 0,
                "is_completed": False,
                "time_spent_minutes": 0
            }
        
        result.append(item)
    
    return result


@router.post("/content/{content_id}/progress", response_model=ContentProgressResponse)
async def update_content_progress(
    content_id: int,
    progress_data: ContentProgressCreate,
    token: str,
    db: Session = Depends(get_db)
):
    """Create or update progress for a module content item"""
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    content = db.query(LessonContent).filter(LessonContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    module = db.query(Module).filter(Module.id == content.module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    if not check_course_access(user.id, module.course_id, db):
        raise HTTPException(status_code=403, detail="Access denied to this course")
    
    if not 0 <= progress_data.view_progress_percentage <= 100:
        raise HTTPException(status_code=400, detail="Progress must be between 0 and 100")
    if progress_data.time_spent_minutes < 0:
        raise HTTPException(status_code=400, detail="Time spent must be non-negative")

    progress = db.query(ContentProgress).filter(
        ContentProgress.user_id == user.id,
        ContentProgress.content_id == content_id
    ).first()
    
    if not progress:
        progress = ContentProgress(
            user_id=user.id,
            content_id=content_id,
            view_progress_percentage=progress_data.view_progress_percentage,
            time_spent_minutes=progress_data.time_spent_minutes,
            is_completed=progress_data.is_completed,
            completed_at=datetime.utcnow() if progress_data.is_completed else None
        )
        db.add(progress)
    else:
        progress.view_progress_percentage = progress_data.view_progress_percentage
        progress.time_spent_minutes = progress_data.time_spent_minutes
        progress.is_completed = progress_data.is_completed
        if progress_data.is_completed:
            progress.completed_at = datetime.utcnow()
        elif progress_data.is_completed is False:
            progress.completed_at = None
    
    db.commit()
    db.refresh(progress)

    aggregate_course_progress(user.id, module.course_id, db)
    return progress
