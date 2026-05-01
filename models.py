from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    region = Column(String, default="uk")  # uk, ie, eu
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Category(Base):
    """Course categories"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String, default="#3B82F6")  # Hex color for UI
    icon = Column(String, nullable=True)  # Icon name/class
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)  # Display order
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    bio = Column(Text, nullable=True)
    target_role = Column(String, nullable=True)
    current_program = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Program(Base):
    """Educational programs that group multiple courses"""
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    short_description = Column(String, nullable=True)  # Brief summary for cards
    diploma_id = Column(Integer, ForeignKey("diplomas.id"), nullable=True)  # Can be standalone or part of diploma

    # Program details
    duration_months = Column(Integer, default=6)  # Expected completion time
    difficulty = Column(String, default="beginner")  # beginner, intermediate, advanced
    prerequisites = Column(Text, nullable=True)

    # Visual elements
    color = Column(String, default="#10B981")  # Hex color for UI
    icon = Column(String, nullable=True)  # Icon name/class
    image_url = Column(String, nullable=True)  # Program banner image

    # Status and ordering
    status = Column(String, default="draft")  # draft, published, archived
    order = Column(Integer, default=0)  # Display order within diploma
    is_featured = Column(Boolean, default=False)  # Featured program

    # Pricing (optional - programs can be free or paid)
    fee = Column(Integer, default=0)  # In cents, 0 = free program
    promo_amount = Column(Integer, default=0)  # Promo discount in cents
    is_on_promo = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Diploma(Base):
    """Diploma programs that group multiple programs"""
    __tablename__ = "diplomas"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    short_description = Column(String, nullable=True)  # Brief summary for cards

    # Diploma details
    duration_years = Column(Integer, default=1)  # Expected completion time
    level = Column(String, default="certificate")  # certificate, diploma, degree
    field = Column(String, nullable=True)  # e.g., "Computer Science", "Business"

    # Visual elements
    color = Column(String, default="#8B5CF6")  # Hex color for UI
    icon = Column(String, nullable=True)  # Icon name/class
    image_url = Column(String, nullable=True)  # Diploma banner image

    # Status and ordering
    status = Column(String, default="draft")  # draft, published, archived
    is_featured = Column(Boolean, default=False)  # Featured diploma

    # Pricing (optional - diplomas can be free or paid)
    fee = Column(Integer, default=0)  # In cents, 0 = free diploma
    promo_amount = Column(Integer, default=0)  # Promo discount in cents
    is_on_promo = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True)  # Courses can be standalone or part of program
    difficulty = Column(String, default="beginner")  # beginner, intermediate, advanced
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    duration_hours = Column(Integer, default=0)
    prerequisites = Column(Text, nullable=True)
    status = Column(String, default="draft")  # draft, published, archived
    
    # Pricing
    fee = Column(Integer, default=0)  # In cents, 0 = free course
    promo_amount = Column(Integer, default=0)  # Promo discount in cents
    is_on_promo = Column(Boolean, default=False)  # Is currently on promotion
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    video_url = Column(String, nullable=True)
    order = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Module(Base):
    """Course modules/classes that contain lessons"""
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class LessonContent(Base):
    """Different types of content within a lesson"""
    __tablename__ = "lesson_contents"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    content_type = Column(String, nullable=False)  # video, notes, slides, assessment, project
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, nullable=False)
    
    # Video fields
    video_url = Column(String, nullable=True)  # YouTube URL
    video_duration_minutes = Column(Integer, nullable=True)
    
    # Notes fields
    notes_content = Column(Text, nullable=True)
    
    # Slides fields
    slides_url = Column(String, nullable=True)  # URL to slides (PDF, Google Slides, etc.)
    
    # Assessment/Test fields
    assessment_type = Column(String, nullable=True)  # quiz, exam, practical
    total_questions = Column(Integer, nullable=True)
    passing_score = Column(Integer, nullable=True)  # percentage
    time_limit_minutes = Column(Integer, nullable=True)
    
    # Project fields
    project_description = Column(Text, nullable=True)
    project_requirements = Column(Text, nullable=True)
    project_rubric = Column(Text, nullable=True)  # JSON with scoring criteria
    submission_type = Column(String, nullable=True)  # code, document, link, file
    
    is_required = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    status = Column(String, default="enrolled")  # enrolled, active, completed
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)  # When student clicked "Start Learning"
    completed_at = Column(DateTime(timezone=True), nullable=True)
    progress_percentage = Column(Integer, default=0)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)  # For paid courses


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    completed = Column(Boolean, default=False)
    time_spent_minutes = Column(Integer, default=0)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    view_progress_percentage = Column(Integer, default=0)  # 0-100% for video/reading progress
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    headline = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    status = Column(String, default="draft")  # draft, published
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    github_url = Column(String, nullable=True)
    project_url = Column(String, nullable=True)
    technologies = Column(String, nullable=True)  # comma-separated
    status = Column(String, default="draft")  # draft, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CV(Base):
    __tablename__ = "cvs"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    title = Column(String, nullable=True)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    linkedin_url = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    status = Column(String, default="draft")  # draft, published
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Experience(Base):
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    cv_id = Column(Integer, ForeignKey("cvs.id"), nullable=False)
    company = Column(String, nullable=False)
    position = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(String, nullable=False)  # YYYY-MM
    end_date = Column(String, nullable=True)  # YYYY-MM or "Present"
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Education(Base):
    __tablename__ = "educations"

    id = Column(Integer, primary_key=True, index=True)
    cv_id = Column(Integer, ForeignKey("cvs.id"), nullable=False)
    institution = Column(String, nullable=False)
    degree = Column(String, nullable=False)
    field = Column(String, nullable=False)
    graduation_date = Column(String, nullable=False)  # YYYY-MM
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    cv_id = Column(Integer, ForeignKey("cvs.id"), nullable=False)
    name = Column(String, nullable=False)
    level = Column(String, nullable=True)  # beginner, intermediate, advanced, expert
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    cv_id = Column(Integer, ForeignKey("cvs.id"), nullable=False)
    name = Column(String, nullable=False)
    issuer = Column(String, nullable=False)
    issue_date = Column(String, nullable=False)  # YYYY-MM
    expiration_date = Column(String, nullable=True)  # YYYY-MM or "None"
    credential_url = Column(String, nullable=True)
    credential_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Gamification Models
class Points(Base):
    __tablename__ = "points"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_points = Column(Integer, default=0)
    weekly_points = Column(Integer, default=0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Streak(Base):
    __tablename__ = "streaks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_streak = Column(Integer, default=0)  # Days
    longest_streak = Column(Integer, default=0)  # Days
    last_activity_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_name = Column(String, nullable=False)  # "first_lesson", "week_warrior", "100_points", etc
    badge_icon = Column(String, nullable=True)  # emoji or icon name
    description = Column(String, nullable=True)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())


# Admin Models
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # super_admin, teacher, admin_staff, accounts, support
    description = Column(String, nullable=True)
    permissions = Column(Text, nullable=True)  # JSON string of permissions
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    username = Column(String, unique=True, nullable=False)  # Display name for admin
    department = Column(String, nullable=True)  # For organizing staff
    theme_preference = Column(String, default="dark")  # dark or white
    is_verified = Column(Boolean, default=False)  # SuperAdmin must verify new admin
    created_by = Column(Integer, ForeignKey("admin_users.id"), nullable=True)  # Who created this admin
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="open")  # open, in_progress, resolved, closed
    priority = Column(String, default="medium")  # low, medium, high, urgent
    assigned_to = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    response = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # In cents
    currency = Column(String, default="gbp")  # gbp, eur, usd
    status = Column(String, default="pending")  # pending, completed, failed, refunded, expired
    payment_method = Column(String, default="payoneer")  # payoneer, card, etc
    transaction_id = Column(String, nullable=True, unique=True)
    payoneer_order_id = Column(String, nullable=True, unique=True)  # Payoneer order ID
    checkout_url = Column(String, nullable=True)  # Payoneer checkout URL
    
    # Item type and ID (could be course, program, diploma, subscription)
    item_type = Column(String, nullable=True)  # 'course', 'program', 'diploma', 'subscription'
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True)
    diploma_id = Column(Integer, ForeignKey("diplomas.id"), nullable=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    processed_by = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    
    # Webhook data
    payoneer_webhook_response = Column(Text, nullable=True)  # Store webhook response
    webhook_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    total_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    new_enrollments = Column(Integer, default=0)
    completed_courses = Column(Integer, default=0)
    total_revenue = Column(Integer, default=0)  # In cents
    total_complaints = Column(Integer, default=0)
    resolved_complaints = Column(Integer, default=0)


# Progress Tracking for New LessonContent Model
class ContentProgress(Base):
    """Track user progress on individual lesson content items"""
    __tablename__ = "content_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("lesson_contents.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    view_progress_percentage = Column(Integer, default=0)  # 0-100% for video/reading
    time_spent_minutes = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AssessmentScore(Base):
    """Track assessment/quiz scores"""
    __tablename__ = "assessment_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("lesson_contents.id"), nullable=False)  # Must be assessment type
    score = Column(Integer, nullable=False)  # Points earned
    total_points = Column(Integer, nullable=False)  # Total possible points
    percentage = Column(Integer, nullable=False)  # Score percentage (0-100)
    is_passing = Column(Boolean, nullable=False)  # Based on passing_score
    attempts = Column(Integer, default=1)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    answers = Column(Text, nullable=True)  # JSON with user answers
    feedback = Column(Text, nullable=True)  # Feedback from assessment
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ProjectSubmission(Base):
    """Track project submissions"""
    __tablename__ = "project_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("lesson_contents.id"), nullable=False)  # Must be project type
    submission_url = Column(String, nullable=False)  # Link to code/document/submission
    submission_type = Column(String, nullable=False)  # code, document, link, file
    status = Column(String, default="submitted")  # submitted, grading, graded, rejected
    score = Column(Integer, nullable=True)  # Rubric score
    total_points = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)
    graded_by = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    graded_at = Column(DateTime(timezone=True), nullable=True)


# Assessment Questions Model
class Question(Base):
    """Assessment questions within lesson content"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("lesson_contents.id"), nullable=False)  # Assessment content
    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=False)  # "objective", "theory", "essay"
    order = Column(Integer, nullable=False)  # Question order within assessment
    
    # For objective questions (MCQ)
    options = Column(Text, nullable=True)  # JSON array of options
    correct_answer = Column(String, nullable=True)  # Correct option/answer
    
    # For theory/essay questions
    sample_answer = Column(Text, nullable=True)  # Sample model answer
    
    # Scoring
    points = Column(Integer, default=1)  # Points for this question
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class StudentAnswer(Base):
    """Track student answers to assessment questions"""
    __tablename__ = "student_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    assessment_attempt_id = Column(Integer, nullable=False)  # Link to AssessmentScore
    
    answer_text = Column(Text, nullable=True)  # Student's answer
    is_correct = Column(Boolean, nullable=True)  # True/False/None (for essay)
    points_earned = Column(Integer, default=0)  # Points earned for this answer
    
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())


class SubscriptionPlan(Base):
    """Monthly/yearly subscription plans"""
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # e.g., "Monthly", "Yearly"
    description = Column(Text, nullable=True)
    duration_days = Column(Integer, nullable=False)  # 30 for monthly, 365 for yearly
    price = Column(Integer, nullable=False)  # In cents
    stripe_price_id = Column(String, nullable=True)  # For payment processing
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Subscription(Base):
    """User subscriptions to access all paid courses"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    
    status = Column(String, default="active")  # active, cancelled, expired, paused
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    
    # Subscription period
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=False)
    auto_renew = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ProgramEnrollment(Base):
    """Track student enrollment in programs"""
    __tablename__ = "program_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False, index=True)
    
    status = Column(String, default="enrolled")  # enrolled, active, completed
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)  # When student clicked "Start Learning"
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    progress_percentage = Column(Integer, default=0)  # Overall program progress
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)  # For paid programs
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DiplomaEnrollment(Base):
    """Track student enrollment in diplomas"""
    __tablename__ = "diploma_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    diploma_id = Column(Integer, ForeignKey("diplomas.id"), nullable=False, index=True)
    
    status = Column(String, default="enrolled")  # enrolled, active, completed
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)  # When student clicked "Start Learning"
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    progress_percentage = Column(Integer, default=0)  # Overall diploma progress
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)  # For paid diplomas
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CompletionCertificate(Base):
    """Certificates issued upon completion of courses, programs, or diplomas"""
    __tablename__ = "completion_certificates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Enrollment reference (one-to-one depending on item_type)
    item_type = Column(String, nullable=False)  # 'course', 'program', 'diploma'
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True)
    diploma_id = Column(Integer, ForeignKey("diplomas.id"), nullable=True)
    enrollment_id = Column(Integer, nullable=True)  # Enrollment record ID for reference
    
    # Certificate metadata
    certificate_number = Column(String, unique=True, nullable=False)  # e.g., SABIKIN-CERT-2024-00001
    verification_code = Column(String, unique=True, nullable=False)  # QR code data / verification
    
    # Completion and issuance
    completed_at = Column(DateTime(timezone=True), nullable=False)  # When course/program/diploma was completed
    issued_at = Column(DateTime(timezone=True), server_default=func.now())  # When certificate was generated
    
    # File storage
    pdf_path = Column(String, nullable=True)  # Local storage path or S3 URL for PDF
    
    # Status
    status = Column(String, default="issued")  # issued, revoked, expired, reissue_requested
    
    # For certificate change requests (name correction, physical copy, etc.)
    change_request = Column(Text, nullable=True)  # JSON: {request_type, old_value, new_value, reason, status}
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
