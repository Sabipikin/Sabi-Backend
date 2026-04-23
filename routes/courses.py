from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Course, Lesson, Enrollment, Progress, User, Points, Streak
from schemas import CourseCreate, CourseResponse, LessonCreate, LessonResponse, EnrollmentResponse, ProgressResponse
from routes.auth import get_current_user

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.post("/", response_model=CourseResponse)
async def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from datetime import datetime
    # Only allow instructors to create courses (for now, any authenticated user can create)
    new_course = Course(
        **course.dict(),
        instructor_id=current_user.id,
        status="published",  # Set status to published for new courses
        updated_at=datetime.now()  # Set manually
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return CourseResponse.from_orm(new_course)


@router.get("/enrolled", response_model=list[dict])
async def get_enrolled_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    enrollments = db.query(Enrollment).filter(Enrollment.user_id == current_user.id).all()
    result = []
    for enrollment in enrollments:
        course = db.query(Course).filter(Course.id == enrollment.course_id).first()
        if course:
            result.append({
                "enrollment": EnrollmentResponse.from_orm(enrollment),
                "course": CourseResponse.from_orm(course)
            })
    return result


@router.get("/", response_model=list[CourseResponse])
async def get_courses(
    skip: int = 0,
    limit: int = 10,
    category: str = None,
    difficulty: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Course).filter(Course.status == "published")
    if category:
        query = query.filter(Course.category == category)
    if difficulty:
        query = query.filter(Course.difficulty == difficulty)
    courses = query.offset(skip).limit(limit).all()
    return [CourseResponse.from_orm(course) for course in courses]


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return CourseResponse.from_orm(course)


@router.post("/{course_id}/enroll", response_model=EnrollmentResponse)
async def enroll_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if already enrolled
    existing_enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.course_id == course_id
    ).first()
    if existing_enrollment:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")
    
    # Create enrollment
    from datetime import datetime
    enrollment = Enrollment(
        user_id=current_user.id,
        course_id=course_id,
        enrolled_at=datetime.now(),
        progress_percentage=0
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return EnrollmentResponse.from_orm(enrollment)


@router.get("/{course_id}/lessons", response_model=list[LessonResponse])
async def get_course_lessons(
    course_id: int,
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    lessons = db.query(Lesson).filter(Lesson.course_id == course_id).order_by(Lesson.order).all()
    return [LessonResponse.from_orm(lesson) for lesson in lessons]


@router.post("/{course_id}/create-lessons", response_model=list[LessonResponse])
async def create_course_lessons(
    course_id: int,
    lessons_data: list[LessonCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Only allow course instructor to add lessons
    if course.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only course instructor can add lessons")
    
    created_lessons = []
    for lesson_data in lessons_data:
        new_lesson = Lesson(
            **lesson_data.dict(),
            course_id=course_id
        )
        db.add(new_lesson)
        db.flush()
        created_lessons.append(new_lesson)
    
    db.commit()
    return [LessonResponse.from_orm(lesson) for lesson in created_lessons]


@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
async def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return LessonResponse.from_orm(lesson)


@router.post("/lessons/{lesson_id}/complete", response_model=ProgressResponse)
async def complete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from datetime import datetime
    from models import Points, Streak, Badge
    
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Check if user is enrolled in the course
    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.course_id == lesson.course_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled in this course")
    
    # Get or create progress record
    progress = db.query(Progress).filter(
        Progress.user_id == current_user.id,
        Progress.lesson_id == lesson_id
    ).first()
    
    if not progress:
        progress = Progress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            completed=True,
            time_spent_minutes=lesson.duration_minutes,
            completed_at=datetime.now()
        )
        db.add(progress)
        
        # Award gamification points for first completion
        points = db.query(Points).filter(Points.user_id == current_user.id).first()
        if not points:
            points = Points(user_id=current_user.id, total_points=0, weekly_points=0)
            db.add(points)
        
        points.total_points += 10
        points.weekly_points += 10
        points.last_updated = datetime.utcnow()
        
        # Update streak
        from datetime import timedelta
        streak = db.query(Streak).filter(Streak.user_id == current_user.id).first()
        if not streak:
            streak = Streak(user_id=current_user.id, current_streak=1, longest_streak=1)
            db.add(streak)
        else:
            today = datetime.utcnow().date()
            last_activity = (
                streak.last_activity_date.date()
                if streak.last_activity_date
                else today - timedelta(days=2)
            )
            if last_activity == today:
                pass
            elif last_activity == today - timedelta(days=1):
                streak.current_streak += 1
                if streak.current_streak > streak.longest_streak:
                    streak.longest_streak = streak.current_streak
                points.total_points += 5
                points.weekly_points += 5
            else:
                streak.current_streak = 1
        
        streak.last_activity_date = datetime.utcnow()
        
        # Check for badges
        _check_and_award_badges(current_user.id, points, streak, db)
    else:
        progress.completed = True
        progress.completed_at = datetime.now()
    
    # Update enrollment progress
    total_lessons = db.query(Lesson).filter(Lesson.course_id == lesson.course_id).count()
    completed_lessons = db.query(Progress).filter(
        Progress.user_id == current_user.id,
        Progress.lesson_id.in_(
            db.query(Lesson.id).filter(Lesson.course_id == lesson.course_id)
        ),
        Progress.completed == True
    ).count()
    
    if total_lessons > 0:
        enrollment.progress_percentage = int((completed_lessons / total_lessons) * 100)
    
    db.commit()
    db.refresh(progress)
    return ProgressResponse.from_orm(progress)


@router.post("/lessons/{lesson_id}/progress")
async def update_lesson_progress(
    lesson_id: int,
    view_progress_percentage: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the view progress (0-100) of a lesson"""
    from datetime import datetime
    
    if not 0 <= view_progress_percentage <= 100:
        raise HTTPException(status_code=400, detail="Progress must be between 0 and 100")
    
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Check if user is enrolled in the course
    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.course_id == lesson.course_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled in this course")
    
    # Get or create progress record
    progress = db.query(Progress).filter(
        Progress.user_id == current_user.id,
        Progress.lesson_id == lesson_id
    ).first()
    
    if not progress:
        progress = Progress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            view_progress_percentage=view_progress_percentage,
            completed=False
        )
        db.add(progress)
    else:
        progress.view_progress_percentage = view_progress_percentage
    
    db.commit()
    db.refresh(progress)
    
    return {
        "lesson_id": lesson_id,
        "view_progress_percentage": progress.view_progress_percentage,
        "can_proceed": view_progress_percentage >= 80
    }


# Helper function to check and award badges
def _check_and_award_badges(user_id: int, points: Points, streak: Streak, db: Session):
    """Check if user qualifies for any new badges"""
    from models import Badge
    
    existing_badges = db.query(Badge.badge_name).filter(Badge.user_id == user_id).all()
    existing_badge_names = {b[0] for b in existing_badges}

    # First Lesson badge
    if "first_lesson" not in existing_badge_names and points.total_points >= 10:
        badge = Badge(
            user_id=user_id,
            badge_name="first_lesson",
            badge_icon="🎓",
            description="Completed your first lesson!",
        )
        db.add(badge)

    # Dedicated Learner (50 points)
    if "dedicated_learner" not in existing_badge_names and points.total_points >= 50:
        badge = Badge(
            user_id=user_id,
            badge_name="dedicated_learner",
            badge_icon="📚",
            description="Earned 50 points!",
        )
        db.add(badge)

    # Point Master (100 points)
    if "point_master" not in existing_badge_names and points.total_points >= 100:
        badge = Badge(
            user_id=user_id,
            badge_name="point_master",
            badge_icon="⭐",
            description="Earned 100 points!",
        )
        db.add(badge)

    # Week Warrior (5 day streak)
    if "week_warrior" not in existing_badge_names and streak.current_streak >= 5:
        badge = Badge(
            user_id=user_id,
            badge_name="week_warrior",
            badge_icon="🔥",
            description="5 day learning streak!",
        )
        db.add(badge)