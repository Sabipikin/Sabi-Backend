"""AI-Powered Recommendations and Career Pathway Routes"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db
from models import (
    User, Course, Program, Diploma, Enrollment, ProgramEnrollment, DiplomaEnrollment,
    Category, CareerRole, CareerPathway, SkillDefinition, CourseSkill, CareerRoleSkill,
    UserCareerInterest, TrendingAnalytic, ContentProgress, AssessmentScore
)
from schemas import (
    RecommendationResponse, CareerRoleResponse, CareerRoleDetailResponse,
    CareerPathwayResponse, CareerPathwayDetailResponse, SkillResponse,
    TrendingCourseResponse, TrendingSkillResponse, UserCareerPathResponse
)
from routes.auth import get_current_user

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


# ==================== TRENDING & ANALYTICS ====================

@router.get("/trending/courses", response_model=List[TrendingCourseResponse])
async def get_trending_courses(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """Get trending courses based on recent enrollments and completion rates"""
    try:
        # Get last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Subquery to count enrollments in last 30 days
        recent_enrollments = db.query(
            Course.id,
            Course.title,
            Course.description,
            Course.difficulty,
            Category.name.label("category_name"),
            func.count(Enrollment.id).label("enrollment_count"),
            func.count(Enrollment.completed_at).label("completion_count")
        ).join(
            Category, Course.category_id == Category.id
        ).outerjoin(
            Enrollment, and_(
                Enrollment.course_id == Course.id,
                Enrollment.enrolled_at >= thirty_days_ago
            )
        ).group_by(
            Course.id, Course.title, Course.description, Course.difficulty, Category.name
        ).order_by(desc("enrollment_count")).limit(limit).all()
        
        results = []
        for course in recent_enrollments:
            enrollment_count = course.enrollment_count or 0
            completion_count = course.completion_count or 0
            completion_rate = (completion_count / enrollment_count * 100) if enrollment_count > 0 else 0
            trending_score = min(100, int((enrollment_count * 10) + (completion_rate / 2)))
            
            results.append(TrendingCourseResponse(
                id=course.id,
                title=course.title,
                description=course.description,
                difficulty=course.difficulty,
                category_name=course.category_name,
                enrollment_count=enrollment_count,
                completion_rate=round(completion_rate, 2),
                trending_score=trending_score,
                icon=None
            ))
        
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching trending courses: {str(e)}"
        )


@router.get("/trending/skills", response_model=List[TrendingSkillResponse])
async def get_trending_skills(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """Get trending skills based on course enrollments and job market demand"""
    try:
        # Get skills with most enrollments in their courses
        trending_skills = db.query(
            SkillDefinition.id,
            SkillDefinition.name,
            SkillDefinition.category,
            SkillDefinition.demand_score,
            SkillDefinition.popularity_score,
            func.count(func.distinct(CourseSkill.course_id)).label("courses_count")
        ).join(
            CourseSkill, SkillDefinition.id == CourseSkill.skill_id
        ).group_by(
            SkillDefinition.id
        ).order_by(
            desc(SkillDefinition.demand_score + SkillDefinition.popularity_score)
        ).limit(limit).all()
        
        results = []
        for skill in trending_skills:
            results.append(TrendingSkillResponse(
                id=skill.id,
                name=skill.name,
                category=skill.category,
                demand_score=skill.demand_score,
                popularity_score=skill.popularity_score,
                courses_count=skill.courses_count or 0,
                related_jobs=skill.demand_score  # Proxy for related jobs
            ))
        
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching trending skills: {str(e)}"
        )


# ==================== CAREER ROLES & PATHWAYS ====================

@router.get("/career-roles", response_model=List[CareerRoleResponse])
async def get_career_roles(
    featured_only: bool = False,
    trending_only: bool = False,
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """Get available career roles with optional filters"""
    try:
        query = db.query(CareerRole)
        
        if featured_only:
            query = query.filter(CareerRole.is_featured == True)
        if trending_only:
            query = query.filter(CareerRole.is_trending == True)
        
        roles = query.order_by(
            desc(CareerRole.popularity_score)
        ).limit(limit).all()
        
        return roles
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching career roles: {str(e)}"
        )


@router.get("/career-roles/{role_id}", response_model=CareerRoleDetailResponse)
async def get_career_role_details(
    role_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a career role including required skills"""
    try:
        role = db.query(CareerRole).filter(CareerRole.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Career role not found"
            )
        
        # Get required skills
        required_skills = db.query(SkillDefinition).join(
            CareerRoleSkill, SkillDefinition.id == CareerRoleSkill.skill_id
        ).filter(
            CareerRoleSkill.career_role_id == role_id
        ).all()
        
        return CareerRoleDetailResponse(
            id=role.id,
            title=role.title,
            description=role.description,
            category=role.category,
            salary_range=role.salary_range,
            difficulty=role.difficulty,
            popularity_score=role.popularity_score,
            is_trending=role.is_trending,
            is_featured=role.is_featured,
            required_skills=[SkillResponse.from_orm(s) for s in required_skills]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching career role details: {str(e)}"
        )


@router.get("/career-pathways", response_model=List[CareerPathwayResponse])
async def get_career_pathways(
    career_role_id: Optional[int] = None,
    difficulty: Optional[str] = None,
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """Get available career learning pathways"""
    try:
        query = db.query(CareerPathway).filter(CareerPathway.is_active == True)
        
        if career_role_id:
            query = query.filter(CareerPathway.career_role_id == career_role_id)
        if difficulty:
            query = query.filter(CareerPathway.difficulty == difficulty)
        
        pathways = query.order_by(
            desc(CareerPathway.popularity_score)
        ).limit(limit).all()
        
        return pathways
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching career pathways: {str(e)}"
        )


@router.get("/career-pathways/{pathway_id}", response_model=CareerPathwayDetailResponse)
async def get_career_pathway_details(
    pathway_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a career pathway"""
    try:
        pathway = db.query(CareerPathway).filter(CareerPathway.id == pathway_id).first()
        if not pathway:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Career pathway not found"
            )
        
        # Get career role
        role = db.query(CareerRole).filter(CareerRole.id == pathway.career_role_id).first()
        
        # Get required skills for the role
        required_skills = db.query(SkillDefinition).join(
            CareerRoleSkill, SkillDefinition.id == CareerRoleSkill.skill_id
        ).filter(
            CareerRoleSkill.career_role_id == pathway.career_role_id
        ).all()
        
        # Parse course IDs if stored as JSON
        course_ids = None
        program_ids = None
        if pathway.course_ids:
            import json
            try:
                course_ids = json.loads(pathway.course_ids)
            except:
                course_ids = None
        if pathway.program_ids:
            import json
            try:
                program_ids = json.loads(pathway.program_ids)
            except:
                program_ids = None
        
        return CareerPathwayDetailResponse(
            id=pathway.id,
            career_role_id=pathway.career_role_id,
            title=pathway.title,
            description=pathway.description,
            duration_months=pathway.duration_months,
            difficulty=pathway.difficulty,
            completion_percentage=pathway.completion_percentage,
            students_count=pathway.students_count,
            popularity_score=pathway.popularity_score,
            diploma_id=pathway.diploma_id,
            program_ids=program_ids,
            course_ids=course_ids,
            required_skills=[SkillResponse.from_orm(s) for s in required_skills],
            career_role=CareerRoleResponse.from_orm(role)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching pathway details: {str(e)}"
        )


# ==================== AI RECOMMENDATIONS ====================

@router.get("/for-user", response_model=List[RecommendationResponse])
async def get_personalized_recommendations(
    limit: int = Query(5, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI-powered personalized course recommendations based on user progress and interests"""
    try:
        recommendations = []
        
        # 1. Get user's enrolled courses to understand their current level
        user_enrollments = db.query(Enrollment).filter(
            Enrollment.user_id == current_user.id
        ).all()
        
        enrolled_course_ids = [e.course_id for e in user_enrollments]
        
        # 2. Get user's target role to find relevant pathways
        user_profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()
        
        # 3. Get skills from completed courses
        completed_enrollments = db.query(Enrollment).filter(
            Enrollment.user_id == current_user.id,
            Enrollment.status == "completed"
        ).all()
        
        user_skills = set()
        for enrollment in completed_enrollments:
            skills = db.query(SkillDefinition).join(
                CourseSkill, SkillDefinition.id == CourseSkill.skill_id
            ).filter(
                CourseSkill.course_id == enrollment.course_id
            ).all()
            user_skills.update([s.id for s in skills])
        
        # 4. Find courses with similar or next-level skills
        recommended_courses = db.query(Course).filter(
            Course.id.notin_(enrolled_course_ids),
            Course.status == "published"
        ).order_by(
            func.random()  # Random for variety
        ).limit(limit).all()
        
        for course in recommended_courses:
            # Calculate recommendation score
            score = 70 + (len(user_skills) * 3)  # Base score + skill match
            
            # Get course skills
            course_skills = db.query(SkillDefinition).join(
                CourseSkill, SkillDefinition.id == CourseSkill.skill_id
            ).filter(
                CourseSkill.course_id == course.id
            ).all()
            
            recommendations.append(RecommendationResponse(
                recommended_type="course",
                item_id=course.id,
                title=course.title,
                description=course.description,
                reason="Based on your learning progress and interests",
                score=min(100, score),
                skills_learned=[s.name for s in course_skills],
                duration=course.duration_hours
            ))
        
        return recommendations[:limit]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
        )


@router.get("/next-course", response_model=Optional[RecommendationResponse])
async def get_next_recommended_course(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the next recommended course based on user progress"""
    try:
        # Get user's progress
        user_enrollments = db.query(Enrollment).filter(
            Enrollment.user_id == current_user.id
        ).all()
        
        enrolled_course_ids = [e.course_id for e in user_enrollments]
        
        # Get most recent course they worked on
        recent_course = db.query(Enrollment).filter(
            Enrollment.user_id == current_user.id
        ).order_by(Enrollment.started_at.desc()).first()
        
        if not recent_course:
            return None
        
        recent = db.query(Course).filter(Course.id == recent_course.course_id).first()
        
        # Find next level course in same category
        next_course = db.query(Course).filter(
            Course.category_id == recent.category_id,
            Course.id.notin_(enrolled_course_ids),
            Course.status == "published"
        ).order_by(Course.difficulty).first()
        
        if not next_course:
            return None
        
        course_skills = db.query(SkillDefinition).join(
            CourseSkill, SkillDefinition.id == CourseSkill.skill_id
        ).filter(
            CourseSkill.course_id == next_course.id
        ).all()
        
        return RecommendationResponse(
            recommended_type="course",
            item_id=next_course.id,
            title=next_course.title,
            description=next_course.description,
            reason="Based on your current learning path",
            score=85,
            skills_learned=[s.name for s in course_skills],
            duration=next_course.duration_hours
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting next course: {str(e)}"
        )


# ==================== USER CAREER PATH ====================

@router.get("/user/career-progress", response_model=UserCareerPathResponse)
async def get_user_career_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's career progress and pathway status"""
    try:
        user_profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()
        
        # Get user's career interest
        career_interest = db.query(UserCareerInterest).filter(
            UserCareerInterest.user_id == current_user.id,
            UserCareerInterest.status.in_(["in_progress", "interested"])
        ).first()
        
        # Calculate progress
        completed_enrollments = db.query(Enrollment).filter(
            Enrollment.user_id == current_user.id,
            Enrollment.status == "completed"
        ).count()
        
        in_progress_enrollments = db.query(Enrollment).filter(
            Enrollment.user_id == current_user.id,
            Enrollment.status.in_(["enrolled", "active"])
        ).count()
        
        progress_percentage = 0
        if career_interest:
            progress_percentage = career_interest.progress_percentage
        
        # Get suggested skills
        suggested_skills = []
        if career_interest and career_interest.career_role_id:
            role_skills = db.query(SkillDefinition).join(
                CareerRoleSkill, SkillDefinition.id == CareerRoleSkill.skill_id
            ).filter(
                CareerRoleSkill.career_role_id == career_interest.career_role_id
            ).limit(5).all()
            suggested_skills = [SkillResponse.from_orm(s) for s in role_skills]
        
        # Get pathway if interested in one
        pathway = None
        if career_interest and career_interest.career_pathway_id:
            career_pathway = db.query(CareerPathway).filter(
                CareerPathway.id == career_interest.career_pathway_id
            ).first()
            if career_pathway:
                pathway = CareerPathwayResponse.from_orm(career_pathway)
        
        # Get next recommended course
        next_course = None
        recommendations = db.query(Enrollment).filter(
            Enrollment.user_id != current_user.id
        ).limit(1).all()  # Placeholder
        
        return UserCareerPathResponse(
            user_id=current_user.id,
            current_role=user_profile.current_program if user_profile else None,
            target_role=user_profile.target_role if user_profile else None,
            career_pathway=pathway,
            progress_percentage=progress_percentage,
            completed_courses=completed_enrollments,
            in_progress_courses=in_progress_enrollments,
            next_recommended_course=None,
            suggested_skills=suggested_skills
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting career progress: {str(e)}"
        )


@router.post("/user/career-pathway/{pathway_id}")
async def enroll_in_career_pathway(
    pathway_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enroll user in a career pathway"""
    try:
        pathway = db.query(CareerPathway).filter(CareerPathway.id == pathway_id).first()
        if not pathway:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Career pathway not found"
            )
        
        # Check if already enrolled
        existing = db.query(UserCareerInterest).filter(
            UserCareerInterest.user_id == current_user.id,
            UserCareerInterest.career_pathway_id == pathway_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already enrolled in this pathway"
            )
        
        # Create enrollment
        enrollment = UserCareerInterest(
            user_id=current_user.id,
            career_role_id=pathway.career_role_id,
            career_pathway_id=pathway_id,
            status="in_progress",
            started_at=datetime.utcnow()
        )
        
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        
        # Update pathway stats
        pathway.students_count += 1
        db.commit()
        
        return {
            "message": "Successfully enrolled in career pathway",
            "pathway_id": pathway_id,
            "status": "in_progress"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enrolling in pathway: {str(e)}"
        )
