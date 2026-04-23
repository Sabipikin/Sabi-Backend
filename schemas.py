from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    region: str = "uk"


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserPasswordUpdate(BaseModel):
    new_password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    difficulty: str = "beginner"
    duration_hours: int = 0
    prerequisites: Optional[str] = None
    fee: int = 0  # In cents
    promo_amount: int = 0  # In cents
    is_on_promo: bool = False


class CourseCreate(CourseBase):
    pass


class CourseResponse(CourseBase):
    id: int
    instructor_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    duration_hours: Optional[int] = None
    prerequisites: Optional[str] = None
    fee: Optional[int] = None
    promo_amount: Optional[int] = None
    is_on_promo: Optional[bool] = None
    status: Optional[str] = None


class LessonBase(BaseModel):
    title: str
    content: Optional[str] = None
    video_url: Optional[str] = None
    order: int
    duration_minutes: int = 0


class LessonCreate(LessonBase):
    pass


class LessonResponse(LessonBase):
    id: int
    course_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ModuleBase(BaseModel):
    title: str
    description: Optional[str] = None
    order: int


class ModuleCreate(ModuleBase):
    pass


class ModuleResponse(ModuleBase):
    id: int
    course_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LessonContentBase(BaseModel):
    content_type: str  # video, notes, slides, assessment, project
    title: str
    description: Optional[str] = None
    order: int
    is_required: bool = True


class LessonContentCreate(LessonContentBase):
    # Video fields
    video_url: Optional[str] = None
    video_duration_minutes: Optional[int] = None
    
    # Notes fields
    notes_content: Optional[str] = None
    
    # Slides fields
    slides_url: Optional[str] = None
    
    # Assessment fields
    assessment_type: Optional[str] = None
    total_questions: Optional[int] = None
    passing_score: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    
    # Project fields
    project_description: Optional[str] = None
    project_requirements: Optional[str] = None
    project_rubric: Optional[str] = None
    submission_type: Optional[str] = None


class LessonContentResponse(LessonContentBase):
    id: int
    module_id: int
    video_url: Optional[str] = None
    video_duration_minutes: Optional[int] = None
    notes_content: Optional[str] = None
    slides_url: Optional[str] = None
    assessment_type: Optional[str] = None
    total_questions: Optional[int] = None
    passing_score: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    project_description: Optional[str] = None
    project_requirements: Optional[str] = None
    project_rubric: Optional[str] = None
    submission_type: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EnrollmentBase(BaseModel):
    course_id: int


class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    progress_percentage: int

    class Config:
        from_attributes = True


class ProgressBase(BaseModel):
    lesson_id: int
    completed: bool = False
    time_spent_minutes: int = 0


class ProgressResponse(BaseModel):
    id: int
    user_id: int
    lesson_id: int
    completed: bool
    time_spent_minutes: int
    view_progress_percentage: int = 0
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Portfolio Schemas
class SkillCreate(BaseModel):
    name: str
    level: Optional[str] = None


class SkillResponse(SkillCreate):
    id: int
    cv_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CertificateCreate(BaseModel):
    name: str
    issuer: str
    issue_date: str  # YYYY-MM
    expiration_date: Optional[str] = None
    credential_url: Optional[str] = None
    credential_id: Optional[str] = None


class CertificateResponse(CertificateCreate):
    id: int
    cv_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ExperienceCreate(BaseModel):
    company: str
    position: str
    description: Optional[str] = None
    start_date: str  # YYYY-MM
    end_date: Optional[str] = None  # YYYY-MM or "Present"


class ExperienceResponse(ExperienceCreate):
    id: int
    cv_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class EducationCreate(BaseModel):
    institution: str
    degree: str
    field: str
    graduation_date: str  # YYYY-MM


class EducationResponse(EducationCreate):
    id: int
    cv_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CVBase(BaseModel):
    email: EmailStr
    title: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None


class CVCreate(CVBase):
    pass


class CVResponse(CVBase):
    id: int
    portfolio_id: int
    status: str
    experiences: list[ExperienceResponse] = []
    educations: list[EducationResponse] = []
    skills: list[SkillResponse] = []
    certificates: list[CertificateResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    github_url: Optional[str] = None
    project_url: Optional[str] = None
    technologies: Optional[str] = None


class ProjectResponse(ProjectCreate):
    id: int
    portfolio_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PortfolioBase(BaseModel):
    headline: Optional[str] = None
    bio: Optional[str] = None


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioResponse(PortfolioBase):
    id: int
    user_id: int
    status: str
    projects: list[ProjectResponse] = []
    cv: Optional[CVResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Gamification Schemas
class PointsResponse(BaseModel):
    user_id: int
    total_points: int
    weekly_points: int
    last_updated: datetime

    class Config:
        from_attributes = True


class StreakResponse(BaseModel):
    user_id: int
    current_streak: int
    longest_streak: int
    last_activity_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BadgeResponse(BaseModel):
    id: int
    user_id: int
    badge_name: str
    badge_icon: Optional[str] = None
    description: Optional[str] = None
    earned_at: datetime

    class Config:
        from_attributes = True


class GamificationStatsResponse(BaseModel):
    points: PointsResponse
    streak: StreakResponse
    badges: list[BadgeResponse] = []

    class Config:
        from_attributes = True


# Admin Schemas
class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AdminUserResponse(BaseModel):
    id: int
    user_id: int
    role_id: int
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    department: Optional[str] = None
    theme_preference: str = "dark"
    is_verified: bool
    role_name: str = "super_admin"  # Will be populated from Role table
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminUserCreate(BaseModel):
    email: EmailStr
    full_name: str
    username: str
    role_name: str  # "teacher", "admin_staff", "accounts", "support"
    department: Optional[str] = None
    password: str


class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    username: Optional[str] = None
    department: Optional[str] = None
    role_name: Optional[str] = None
    is_active: Optional[bool] = None


class AdminUserPasswordUpdate(BaseModel):
    new_password: str


class AdminSettingsUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    theme_preference: Optional[str] = None  # "dark" or "white"


class ComplaintResponse(BaseModel):
    id: int
    user_id: int
    subject: str
    description: str
    status: str
    priority: str
    assigned_to: Optional[int] = None
    response: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    id: int
    user_id: int
    amount: int
    currency: str
    status: str
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    course_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalyticsResponse(BaseModel):
    date: datetime
    total_users: int
    active_users: int
    new_enrollments: int
    completed_courses: int
    total_revenue: int
    total_complaints: int
    resolved_complaints: int

    class Config:
        from_attributes = True


# Progress Tracking Schemas
class ContentProgressCreate(BaseModel):
    view_progress_percentage: int = 0  # 0-100
    time_spent_minutes: int = 0
    is_completed: bool = False


class ContentProgressResponse(ContentProgressCreate):
    id: int
    user_id: int
    content_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class AssessmentScoreCreate(BaseModel):
    score: int
    total_points: int
    percentage: int
    is_passing: bool
    answers: Optional[str] = None  # JSON
    feedback: Optional[str] = None


class AssessmentScoreResponse(AssessmentScoreCreate):
    id: int
    user_id: int
    content_id: int
    attempts: int
    started_at: datetime
    completed_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectSubmissionCreate(BaseModel):
    submission_url: str
    submission_type: str  # code, document, link, file


class ProjectSubmissionResponse(ProjectSubmissionCreate):
    id: int
    user_id: int
    content_id: int
    status: str
    score: Optional[int] = None
    total_points: Optional[int] = None
    feedback: Optional[str] = None
    submitted_at: datetime
    graded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EnrollmentWithCourseResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    course: CourseResponse
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    progress_percentage: int
    modules_count: int = 0
    content_items_count: int = 0
    completed_items: int = 0

    class Config:
        from_attributes = True


class UserProgressResponse(BaseModel):
    user_id: int
    total_enrollments: int
    completed_courses: int
    in_progress_courses: int
    content_progress: list[ContentProgressResponse] = []
    assessment_scores: list[AssessmentScoreResponse] = []
    
    class Config:
        from_attributes = True


class CourseProgressDetailResponse(BaseModel):
    enrollment_id: int
    course_id: int
    course_title: str
    progress_percentage: int
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    modules: list[dict] = []  # Will contain module info with content progress
    
    class Config:
        from_attributes = True


class BulkActionRequest(BaseModel):
    course_ids: list[int]


class BulkActionResponse(BaseModel):
    status: str
    message: str
    success_count: int
    failed_count: int
    failed_ids: list[int] = []


# Assessment Questions Schemas
class QuestionBase(BaseModel):
    question_text: str
    question_type: str  # "objective", "theory", "essay"
    order: int
    points: int = 1
    options: Optional[str] = None  # JSON for objective questions
    correct_answer: Optional[str] = None  # For objective
    sample_answer: Optional[str] = None  # For theory/essay


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    question_type: Optional[str] = None
    order: Optional[int] = None
    points: Optional[int] = None
    options: Optional[str] = None
    correct_answer: Optional[str] = None
    sample_answer: Optional[str] = None


class QuestionResponse(QuestionBase):
    id: int
    content_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Student Answers Schemas
class StudentAnswerCreate(BaseModel):
    answer_text: Optional[str] = None
    is_correct: Optional[bool] = None
    points_earned: int = 0


class StudentAnswerResponse(StudentAnswerCreate):
    id: int
    user_id: int
    question_id: int
    assessment_attempt_id: int
    submitted_at: datetime

    class Config:
        from_attributes = True


# Subscription Plan Schemas
class SubscriptionPlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    duration_days: int
    price: int  # In cents


class SubscriptionPlanCreate(SubscriptionPlanBase):
    stripe_price_id: Optional[str] = None


class SubscriptionPlanResponse(SubscriptionPlanBase):
    id: int
    stripe_price_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Subscription Schemas
class SubscriptionBase(BaseModel):
    plan_id: int
    auto_renew: bool = True


class SubscriptionCreate(SubscriptionBase):
    payment_id: Optional[int] = None


class SubscriptionResponse(SubscriptionBase):
    id: int
    user_id: int
    status: str
    payment_id: Optional[int] = None
    start_date: datetime
    end_date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Enrollment Schemas
class EnrollmentUpdate(BaseModel):
    status: Optional[str] = None
    progress_percentage: Optional[int] = None
    payment_id: Optional[int] = None


class EnrollmentDetailResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    status: str
    enrolled_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percentage: int
    payment_id: Optional[int] = None

    class Config:
        from_attributes = True
