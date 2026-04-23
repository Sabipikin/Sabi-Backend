from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from database import get_db
from models import User, AdminUser, Role, Complaint, Payment, Analytics, Course, Lesson, Enrollment, Module, LessonContent
from schemas import (
    AdminUserCreate, AdminUserResponse, RoleResponse,
    ComplaintResponse, PaymentResponse, AnalyticsResponse,
    AdminUserUpdate, AdminUserPasswordUpdate, AdminSettingsUpdate,
    UserCreate, UserResponse, UserUpdate, UserPasswordUpdate,
    CourseCreate, CourseResponse, ModuleCreate, ModuleResponse, LessonContentCreate, LessonContentResponse,
    BulkActionRequest, BulkActionResponse
)
from auth import hash_password, decode_access_token, verify_password
from routes.admin_auth import get_current_admin
import json

router = APIRouter(prefix="/api/admin", tags=["admin"])
security = HTTPBearer()


def format_admin_user(admin_user: AdminUser, db: Session) -> dict:
    role = db.query(Role).filter(Role.id == admin_user.role_id).first()
    user = db.query(User).filter(User.id == admin_user.user_id).first()
    admin_data = AdminUserResponse.from_orm(admin_user).dict()
    admin_data["role_name"] = role.name if role else "super_admin"
    admin_data["email"] = user.email if user else None
    admin_data["full_name"] = user.full_name if user else None
    admin_data["is_active"] = user.is_active if user else False
    return admin_data


def check_role(required_role: str):
    """Dependency to check if admin has required role"""
    async def verify_role(admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
        role = db.query(Role).filter(Role.id == admin.role_id).first()
        if not role or role.name != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires {required_role} role",
            )
        return admin
    return verify_role


def check_roles(*allowed_roles):
    """Dependency to check if admin has one of the allowed roles"""
    async def verify_roles(admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
        role = db.query(Role).filter(Role.id == admin.role_id).first()
        if not role or role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of these roles: {', '.join(allowed_roles)}",
            )
        return admin
    return verify_roles


# ============ Super Admin Only Endpoints ============

@router.post("/register", response_model=AdminUserResponse)
async def register_admin(
    admin_user_data: AdminUserCreate,
    creator: AdminUser = Depends(check_role("super_admin")),
    db: Session = Depends(get_db)
):
    """Register a new admin user (SuperAdmin only)"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == admin_user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )
    
    # Get or create role
    role = db.query(Role).filter(Role.name == admin_user_data.role_name).first()
    if not role:
        if admin_user_data.role_name not in ["teacher", "admin_staff", "accounts", "support"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role name",
            )
        role = Role(
            name=admin_user_data.role_name,
            description=f"{admin_user_data.role_name.replace('_', ' ').title()} role",
        )
        db.add(role)
        db.commit()
        db.refresh(role)
    
    # Create user
    hashed_password = hash_password(admin_user_data.password)
    new_user = User(
        email=admin_user_data.email,
        full_name=admin_user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create admin user
    admin_record = AdminUser(
        user_id=new_user.id,
        role_id=role.id,
        username=admin_user_data.username,
        department=admin_user_data.department,
        is_verified=True,  # SuperAdmin verified
        created_by=creator.id,
    )
    db.add(admin_record)
    db.commit()
    db.refresh(admin_record)
    
    return format_admin_user(admin_record, db)


@router.get("/users", response_model=list[AdminUserResponse])
async def get_admin_users(
    admin: AdminUser = Depends(check_role("super_admin")),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get all admin users (SuperAdmin only)"""
    admin_users = db.query(AdminUser).offset(skip).limit(limit).all()
    return [format_admin_user(admin_user, db) for admin_user in admin_users]


@router.get("/analytics", response_model=list[AnalyticsResponse])
async def get_analytics(
    admin: AdminUser = Depends(check_role("super_admin")),
    db: Session = Depends(get_db),
    days: int = 30
):
    """Get system analytics (SuperAdmin only)"""
    # First try to get historical data
    analytics = db.query(Analytics).order_by(Analytics.date.desc()).limit(days).all()

    # If no historical data, generate current analytics
    if not analytics:
        # Generate current real-time analytics
        current_analytics = generate_current_analytics(db)
        return [current_analytics]

    return analytics


@router.get("/analytics/current", response_model=AnalyticsResponse)
async def get_current_analytics(
    admin: AdminUser = Depends(check_role("super_admin")),
    db: Session = Depends(get_db)
):
    """Get current real-time analytics (SuperAdmin only)"""
    return generate_current_analytics(db)


def generate_current_analytics(db: Session) -> AnalyticsResponse:
    """Generate current analytics from database"""
    from datetime import datetime, timedelta

    # Calculate date range for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    # Total users
    total_users = db.query(func.count(User.id)).scalar()

    # Active users (users who have logged in within last 30 days)
    # Since we don't have last_login in User model, we'll count all active users
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()

    # New enrollments in last 30 days
    new_enrollments = db.query(func.count(Enrollment.id)).filter(
        Enrollment.enrolled_at >= thirty_days_ago
    ).scalar()

    # Completed courses in last 30 days
    completed_courses = db.query(func.count(Enrollment.id)).filter(
        Enrollment.completed_at.isnot(None),
        Enrollment.completed_at >= thirty_days_ago
    ).scalar()

    # Total revenue (from completed payments)
    total_revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.status == "completed"
    ).scalar() or 0

    # Total complaints
    total_complaints = db.query(func.count(Complaint.id)).scalar()

    # Resolved complaints
    resolved_complaints = db.query(func.count(Complaint.id)).filter(
        Complaint.status == "resolved"
    ).scalar()

    return AnalyticsResponse(
        date=datetime.utcnow(),
        total_users=total_users,
        active_users=active_users,
        new_enrollments=new_enrollments,
        completed_courses=completed_courses,
        total_revenue=total_revenue,
        total_complaints=total_complaints,
        resolved_complaints=resolved_complaints
    )


@router.get("/courses", response_model=list[dict])
async def get_all_courses(
    admin: AdminUser = Depends(check_role("super_admin")),
    db: Session = Depends(get_db)
):
    """Get all courses in system (SuperAdmin only)"""
    courses = db.query(Course).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "category": c.category,
            "status": c.status,
            "instructor_id": c.instructor_id,
            "created_at": c.created_at,
        }
        for c in courses
    ]


# ============ Shared Admin Endpoints ============

@router.get("/complaints", response_model=list[ComplaintResponse])
async def get_complaints(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
    status_filter: str = None,
    assigned_to_me: bool = False
):
    """Get complaints (Admin Staff and above can view)"""
    role = db.query(Role).filter(Role.id == admin.role_id).first()
    
    if role.name not in ["super_admin", "admin_staff", "support"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view complaints",
        )
    
    query = db.query(Complaint)
    
    if assigned_to_me:
        query = query.filter(Complaint.assigned_to == admin.id)
    
    if status_filter:
        query = query.filter(Complaint.status == status_filter)
    
    return query.all()


@router.post("/complaints", response_model=ComplaintResponse)
async def create_complaint(
    subject: str,
    description: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a complaint/support ticket"""
    complaint = Complaint(
        user_id=current_user.user_id,
        subject=subject,
        description=description,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


@router.put("/complaints/{complaint_id}")
async def update_complaint(
    complaint_id: int,
    status: str = None,
    response: str = None,
    priority: str = None,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update complaint status/response (Admin Staff and above)"""
    role = db.query(Role).filter(Role.id == admin.role_id).first()
    
    if role.name not in ["super_admin", "admin_staff", "support"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update complaints",
        )
    
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found",
        )
    
    if status:
        complaint.status = status
        if status == "resolved":
            complaint.resolved_at = datetime.utcnow()
    
    if response:
        complaint.response = response
    
    if priority:
        complaint.priority = priority
    
    complaint.assigned_to = admin.id
    
    db.commit()
    db.refresh(complaint)
    return complaint


# ============ Accounts Team Endpoints ============

@router.get("/payments", response_model=list[PaymentResponse])
async def get_payments(
    admin: AdminUser = Depends(check_role("accounts")),
    db: Session = Depends(get_db),
    status_filter: str = None,
    skip: int = 0,
    limit: int = 100
):
    """Get payments (Accounts team only)"""
    query = db.query(Payment)
    
    if status_filter:
        query = query.filter(Payment.status == status_filter)
    
    return query.offset(skip).limit(limit).all()


@router.put("/payments/{payment_id}")
async def update_payment(
    payment_id: int,
    status: str = None,
    notes: str = None,
    admin: AdminUser = Depends(check_role("accounts")),
    db: Session = Depends(get_db)
):
    """Update payment status (Accounts team only)"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    
    if status:
        payment.status = status
    
    if notes:
        payment.notes = notes
    
    payment.processed_by = admin.id
    
    db.commit()
    db.refresh(payment)
    return payment


# ============ Teacher & Super Admin Course Endpoints ============

@router.post("/courses", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    admin: AdminUser = Depends(check_roles("teacher", "super_admin")),
    db: Session = Depends(get_db)
):
    """Create a new course (Teachers and Super Admins only)"""
    new_course = Course(
        **course_data.dict(),
        instructor_id=admin.user_id,
        status="published",
        updated_at=datetime.now()
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course


@router.get("/my-courses", response_model=list[dict])
async def get_my_courses(
    admin: AdminUser = Depends(check_role("teacher")),
    db: Session = Depends(get_db)
):
    """Get courses created by this teacher"""
    courses = db.query(Course).filter(Course.instructor_id == admin.user_id).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "category": c.category,
            "status": c.status,
            "created_at": c.created_at,
        }
        for c in courses
    ]


@router.put("/courses/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_data: CourseCreate,
    admin: AdminUser = Depends(check_roles("teacher", "super_admin")),
    db: Session = Depends(get_db)
):
    """Update course (Admin only, must be owner or super_admin)"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )
    
    # Check if admin is the course owner or is super_admin
    role = db.query(Role).filter(Role.id == admin.role_id).first()
    if course.instructor_id != admin.user_id and role.name != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="Not authorized to edit this course",
        )
    
    # Update course fields
    course.title = course_data.title
    course.description = course_data.description
    course.category = course_data.category
    course.difficulty = course_data.difficulty
    course.duration_hours = course_data.duration_hours
    if course_data.prerequisites:
        course.prerequisites = course_data.prerequisites
    course.updated_at = datetime.now()
    
    db.commit()
    db.refresh(course)
    return course


@router.delete("/courses/{course_id}")
async def delete_course(
    course_id: int,
    admin: AdminUser = Depends(check_roles("teacher", "super_admin")),
    db: Session = Depends(get_db)
):
    """Delete a course (Admin only, must be owner or super_admin)"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )
    
    # Check if admin is the course owner or is super_admin
    role = db.query(Role).filter(Role.id == admin.role_id).first()
    if course.instructor_id != admin.user_id and role.name != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this course",
        )
    
    # Delete all modules and their content first
    modules = db.query(Module).filter(Module.course_id == course_id).all()
    for module in modules:
        # Delete content items
        db.query(LessonContent).filter(LessonContent.module_id == module.id).delete()
        # Delete module
        db.delete(module)
    
    # Delete all enrollments
    db.query(Enrollment).filter(Enrollment.course_id == course_id).delete()
    
    # Delete course
    db.delete(course)
    db.commit()
    
    return {"status": "deleted", "message": "Course and all associated data deleted successfully"}


@router.post("/courses/bulk-delete", response_model=dict)
async def bulk_delete_courses(
    request_data: dict,
    admin: AdminUser = Depends(check_role("super_admin")),
    db: Session = Depends(get_db)
):
    """Delete multiple courses (SuperAdmin only)"""
    course_ids = request_data.get("course_ids", [])
    
    if not course_ids or not isinstance(course_ids, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="course_ids must be a non-empty list of integers",
        )
    
    success_count = 0
    failed_ids = []
    
    for course_id in course_ids:
        try:
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                failed_ids.append(course_id)
                continue
            
            # Delete all modules and their content first
            modules = db.query(Module).filter(Module.course_id == course_id).all()
            for module in modules:
                # Delete content items
                db.query(LessonContent).filter(LessonContent.module_id == module.id).delete()
                # Delete module
                db.delete(module)
            
            # Delete all enrollments
            db.query(Enrollment).filter(Enrollment.course_id == course_id).delete()
            
            # Delete course
            db.delete(course)
            success_count += 1
        except Exception as e:
            failed_ids.append(course_id)
    
    db.commit()
    
    return {
        "status": "completed",
        "message": f"Deleted {success_count} courses successfully",
        "success_count": success_count,
        "failed_count": len(failed_ids),
        "failed_ids": failed_ids
    }


@router.post("/courses/bulk-publish", response_model=dict)
async def bulk_publish_courses(
    request_data: dict,
    admin: AdminUser = Depends(check_role("super_admin")),
    db: Session = Depends(get_db)
):
    """Publish multiple courses (SuperAdmin only)"""
    course_ids = request_data.get("course_ids", [])
    
    if not course_ids or not isinstance(course_ids, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="course_ids must be a non-empty list of integers",
        )
    
    success_count = 0
    failed_ids = []
    
    for course_id in course_ids:
        try:
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                failed_ids.append(course_id)
                continue
            
            # Update status to published
            course.status = "published"
            course.updated_at = datetime.now()
            success_count += 1
        except Exception as e:
            failed_ids.append(course_id)
    
    db.commit()
    
    return {
        "status": "completed",
        "message": f"Published {success_count} courses successfully",
        "success_count": success_count,
        "failed_count": len(failed_ids),
        "failed_ids": failed_ids
    }


@router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course_students(
    course_id: int,
    admin: AdminUser = Depends(check_role("teacher")),
    db: Session = Depends(get_db)
):
    """Get students enrolled in a course (Teacher can only see their own courses)"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    
    if course.instructor_id != admin.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own courses",
        )
    
    enrollments = db.query(Enrollment).filter(Enrollment.course_id == course_id).all()
    
    return [
        {
            "user_id": e.user_id,
            "progress_percentage": e.progress_percentage,
            "enrolled_at": e.enrolled_at,
            "completed_at": e.completed_at,
        }
        for e in enrollments
    ]


# ============ Dashboard Endpoints ============

@router.get("/dashboard-stats")
async def get_dashboard_stats(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get dashboard stats based on admin role"""
    role = db.query(Role).filter(Role.id == admin.role_id).first()
    
    if role.name == "super_admin":
        total_users = db.query(func.count(User.id)).scalar()
        total_courses = db.query(func.count(Course.id)).scalar()
        total_complaints = db.query(func.count(Complaint.id)).scalar()
        total_revenue = db.query(func.sum(Payment.amount)).filter(
            Payment.status == "completed"
        ).scalar() or 0
        
        return {
            "total_users": total_users,
            "total_courses": total_courses,
            "total_complaints": total_complaints,
            "total_revenue": total_revenue,
        }
    
    elif role.name == "teacher":
        my_courses = db.query(func.count(Course.id)).filter(
            Course.instructor_id == admin.user_id
        ).scalar()
        total_students = db.query(func.count(Enrollment.id)).join(
            Course
        ).filter(Course.instructor_id == admin.user_id).scalar()
        
        return {
            "my_courses": my_courses,
            "total_students": total_students,
        }
    
    elif role.name == "admin_staff":
        total_complaints = db.query(func.count(Complaint.id)).scalar()
        open_complaints = db.query(func.count(Complaint.id)).filter(
            Complaint.status == "open"
        ).scalar()
        
        return {
            "total_complaints": total_complaints,
            "open_complaints": open_complaints,
        }
    
    elif role.name == "accounts":
        total_payments = db.query(func.count(Payment.id)).scalar()
        pending_payments = db.query(func.count(Payment.id)).filter(
            Payment.status == "pending"
        ).scalar()
        total_revenue = db.query(func.sum(Payment.amount)).filter(
            Payment.status == "completed"
        ).scalar() or 0
        
        return {
            "total_payments": total_payments,
            "pending_payments": pending_payments,
            "total_revenue": total_revenue,
        }
    
    return {"message": "Dashboard stats not available for this role"}


# ============ Admin User Management Endpoints (SuperAdmin) ============

@router.put("/users/{user_id}", response_model=AdminUserResponse)
async def update_admin_user(
    user_id: int,
    update_data: AdminUserUpdate,
    admin: AdminUser = Depends(check_role("super_admin")),
    db: Session = Depends(get_db)
):
    """Update admin user details (SuperAdmin only)"""
    admin_user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found",
        )
    
    user = db.query(User).filter(User.id == admin_user.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update user fields
    if update_data.email and update_data.email != user.email:
        existing = db.query(User).filter(User.email == update_data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use",
            )
        user.email = update_data.email
    
    if update_data.full_name:
        user.full_name = update_data.full_name
    
    # Update admin user fields
    if update_data.username:
        existing = db.query(AdminUser).filter(
            AdminUser.username == update_data.username,
            AdminUser.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already in use",
            )
        admin_user.username = update_data.username
    
    if update_data.department is not None:
        admin_user.department = update_data.department
    
    if update_data.role_name:
        role = db.query(Role).filter(Role.name == update_data.role_name).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role",
            )
        admin_user.role_id = role.id
    
    admin_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(admin_user)
    
    return format_admin_user(admin_user, db)


@router.delete("/users/{user_id}")
async def delete_admin_user(
    user_id: int,
    admin: AdminUser = Depends(check_role("super_admin")),
    db: Session = Depends(get_db)
):
    """Delete an admin user (SuperAdmin only)"""
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own admin account",
        )
    
    admin_user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found",
        )
    
    user = db.query(User).filter(User.id == admin_user.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Delete admin user and associated user
    db.delete(admin_user)
    db.delete(user)
    db.commit()
    
    return {"message": "Admin user deleted successfully"}


@router.put("/users/{user_id}/password")
async def change_admin_password(
    user_id: int,
    password_data: AdminUserPasswordUpdate,
    admin: AdminUser = Depends(check_role("super_admin")),
    db: Session = Depends(get_db)
):
    """Change admin user password (SuperAdmin only)"""
    admin_user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found",
        )
    
    user = db.query(User).filter(User.id == admin_user.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update password
    user.hashed_password = hash_password(password_data.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}


@router.get("/frontend-users", response_model=list[UserResponse])
async def get_frontend_users(
    admin: AdminUser = Depends(check_roles("super_admin", "admin_staff")),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get all frontend users (SuperAdmin only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.post("/frontend-users", response_model=UserResponse)
async def create_frontend_user(
    user_data: UserCreate,
    admin: AdminUser = Depends(check_roles("super_admin", "admin_staff")),
    db: Session = Depends(get_db)
):
    """Create a new frontend user (SuperAdmin only)"""
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        region=user_data.region,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.put("/frontend-users/{user_id}", response_model=UserResponse)
async def update_frontend_user(
    user_id: int,
    user_data: UserUpdate,
    admin: AdminUser = Depends(check_roles("super_admin", "admin_staff")),
    db: Session = Depends(get_db)
):
    """Update frontend user details (SuperAdmin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user_data.email and user_data.email != user.email:
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use",
            )
        user.email = user_data.email

    if user_data.full_name is not None:
        user.full_name = user_data.full_name

    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


@router.delete("/frontend-users/{user_id}")
async def delete_frontend_user(
    user_id: int,
    admin: AdminUser = Depends(check_roles("super_admin", "admin_staff")),
    db: Session = Depends(get_db)
):
    """Delete a frontend user (SuperAdmin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    db.delete(user)
    db.commit()
    return {"message": "Frontend user deleted successfully"}


@router.put("/frontend-users/{user_id}/password")
async def change_frontend_user_password(
    user_id: int,
    password_data: UserPasswordUpdate,
    admin: AdminUser = Depends(check_roles("super_admin", "admin_staff")),
    db: Session = Depends(get_db)
):
    """Change frontend user password (SuperAdmin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    user.hashed_password = hash_password(password_data.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


# ============ Admin Personal Settings Endpoints ============

@router.get("/me", response_model=AdminUserResponse)
async def get_current_admin_info(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get current admin user information"""
    return admin


@router.put("/me/settings")
async def update_admin_settings(
    settings_data: AdminSettingsUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update current admin user settings (username, password, theme)"""
    user = db.query(User).filter(User.id == admin.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update username
    if settings_data.username:
        existing = db.query(AdminUser).filter(
            AdminUser.username == settings_data.username,
            AdminUser.id != admin.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already in use",
            )
        admin.username = settings_data.username
    
    # Update password
    if settings_data.password:
        user.hashed_password = hash_password(settings_data.password)
    
    # Update theme preference
    if settings_data.theme_preference:
        if settings_data.theme_preference not in ["dark", "white"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Theme must be 'dark' or 'white'",
            )
        admin.theme_preference = settings_data.theme_preference
    
    admin.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(admin)
    
    return {
        "message": "Settings updated successfully",
        "admin": admin,
        "theme": admin.theme_preference
    }


@router.put("/me/password")
async def change_own_password(
    password_data: AdminUserPasswordUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Change own password"""
    user = db.query(User).filter(User.id == admin.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Verify old password
    if not verify_password(password_data.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Old password is incorrect",
        )
    
    # Update password
    user.hashed_password = hash_password(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


# ============ Module Management Endpoints ============

@router.post("/courses/{course_id}/modules", response_model=ModuleResponse)
async def create_module_admin(
    course_id: int,
    module_data: ModuleCreate,
    admin: AdminUser = Depends(check_roles("teacher", "super_admin")),
    db: Session = Depends(get_db)
):
    """Create a module in a course (Admin only)"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if admin is the course owner or is super_admin
    role = db.query(Role).filter(Role.id == admin.role_id).first()
    if course.instructor_id != admin.user_id and role.name != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized to add modules to this course")
    
    new_module = Module(
        course_id=course_id,
        **module_data.dict()
    )
    db.add(new_module)
    db.commit()
    db.refresh(new_module)
    return new_module


@router.get("/courses/{course_id}/modules", response_model=list[ModuleResponse])
async def get_course_modules_admin(
    course_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all modules for a course (Admin only)"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    modules = db.query(Module).filter(Module.course_id == course_id).order_by(Module.order).all()
    return modules


@router.put("/modules/{module_id}", response_model=ModuleResponse)
async def update_module_admin(
    module_id: int,
    module_data: ModuleCreate,
    admin: AdminUser = Depends(check_roles("teacher", "super_admin")),
    db: Session = Depends(get_db)
):
    """Update a module (Admin only)"""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    course = db.query(Course).filter(Course.id == module.course_id).first()
    
    # Check if admin is the course owner or is super_admin
    role = db.query(Role).filter(Role.id == admin.role_id).first()
    if course.instructor_id != admin.user_id and role.name != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this module")
    
    for key, value in module_data.dict().items():
        setattr(module, key, value)
    
    db.commit()
    db.refresh(module)
    return module


@router.delete("/modules/{module_id}")
async def delete_module_admin(
    module_id: int,
    admin: AdminUser = Depends(check_roles("teacher", "super_admin")),
    db: Session = Depends(get_db)
):
    """Delete a module (Admin only)"""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    course = db.query(Course).filter(Course.id == module.course_id).first()
    
    # Check if admin is the course owner or is super_admin
    role = db.query(Role).filter(Role.id == admin.role_id).first()
    if course.instructor_id != admin.user_id and role.name != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this module")
    
    db.delete(module)
    db.commit()
    return {"status": "deleted"}


# ============ Lesson Content Management Endpoints ============

@router.post("/modules/{module_id}/content", response_model=LessonContentResponse)
async def create_lesson_content_admin(
    module_id: int,
    content: LessonContentCreate,
    admin: AdminUser = Depends(check_roles("teacher", "super_admin")),
    db: Session = Depends(get_db)
):
    """Create lesson content (video, notes, slides, assessment, project)"""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    course = db.query(Course).filter(Course.id == module.course_id).first()
    
    # Check if admin is the course owner or is super_admin
    role = db.query(Role).filter(Role.id == admin.role_id).first()
    if course.instructor_id != admin.user_id and role.name != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized to create content")
    
    new_content = LessonContent(
        module_id=module_id,
        **content.dict()
    )
    db.add(new_content)
    db.commit()
    db.refresh(new_content)
    return new_content


@router.get("/modules/{module_id}/content", response_model=list[LessonContentResponse])
async def get_module_content_admin(
    module_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all content for a module"""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    content_items = db.query(LessonContent).filter(
        LessonContent.module_id == module_id
    ).order_by(LessonContent.order).all()
    return content_items


@router.get("/content/{content_id}", response_model=LessonContentResponse)
async def get_lesson_content_admin(
    content_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get a specific lesson content item"""
    content = db.query(LessonContent).filter(LessonContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content


@router.put("/content/{content_id}", response_model=LessonContentResponse)
async def update_lesson_content_admin(
    content_id: int,
    content_data: LessonContentCreate,
    admin: AdminUser = Depends(check_roles("teacher", "super_admin")),
    db: Session = Depends(get_db)
):
    """Update lesson content"""
    content = db.query(LessonContent).filter(LessonContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    module = db.query(Module).filter(Module.id == content.module_id).first()
    course = db.query(Course).filter(Course.id == module.course_id).first()
    
    # Check if admin is the course owner or is super_admin
    role = db.query(Role).filter(Role.id == admin.role_id).first()
    if course.instructor_id != admin.user_id and role.name != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized to update content")
    
    for key, value in content_data.dict(exclude_unset=True).items():
        setattr(content, key, value)
    
    db.commit()
    db.refresh(content)
    return content


@router.delete("/content/{content_id}")
async def delete_lesson_content_admin(
    content_id: int,
    admin: AdminUser = Depends(check_roles("teacher", "super_admin")),
    db: Session = Depends(get_db)
):
    """Delete lesson content"""
    content = db.query(LessonContent).filter(LessonContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    module = db.query(Module).filter(Module.id == content.module_id).first()
    course = db.query(Course).filter(Course.id == module.course_id).first()
    
    # Check if admin is the course owner or is super_admin
    role = db.query(Role).filter(Role.id == admin.role_id).first()
    if course.instructor_id != admin.user_id and role.name != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete content")
    
    db.delete(content)
    db.commit()
    return {"status": "deleted"}
