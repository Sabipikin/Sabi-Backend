from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, Portfolio, Project, CV, Experience, Education, Skill, Certificate
from schemas import (
    PortfolioResponse, ProjectResponse, ProjectCreate, CVResponse, CVCreate,
    ExperienceResponse, ExperienceCreate, EducationResponse, EducationCreate,
    SkillResponse, SkillCreate, CertificateResponse, CertificateCreate
)
from routes.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


# Portfolio endpoints
@router.get("/", response_model=PortfolioResponse)
async def get_or_create_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    
    if not portfolio:
        portfolio = Portfolio(user_id=current_user.id)
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    
    # Load relationships
    portfolio.projects = db.query(Project).filter(Project.portfolio_id == portfolio.id).all()
    portfolio.cv = db.query(CV).filter(CV.portfolio_id == portfolio.id).first()
    
    return portfolio


@router.put("/", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    if "headline" in portfolio_data:
        portfolio.headline = portfolio_data["headline"]
    if "bio" in portfolio_data:
        portfolio.bio = portfolio_data["bio"]
    if "status" in portfolio_data:
        portfolio.status = portfolio_data["status"]
    
    portfolio.updated_at = datetime.now()
    db.commit()
    db.refresh(portfolio)
    
    return portfolio


# Project endpoints
@router.get("/projects", response_model=list[ProjectResponse])
async def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        return []
    
    projects = db.query(Project).filter(Project.portfolio_id == portfolio.id).all()
    return projects


@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        portfolio = Portfolio(user_id=current_user.id)
        db.add(portfolio)
        db.flush()
    
    project = Project(
        portfolio_id=portfolio.id,
        **project_data.dict()
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return project


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify ownership
    portfolio = db.query(Portfolio).filter(Portfolio.id == project.portfolio_id).first()
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return project


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify ownership
    portfolio = db.query(Portfolio).filter(Portfolio.id == project.portfolio_id).first()
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    for key, value in project_data.dict().items():
        setattr(project, key, value)
    
    project.updated_at = datetime.now()
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify ownership
    portfolio = db.query(Portfolio).filter(Portfolio.id == project.portfolio_id).first()
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}


# CV endpoints
@router.get("/cv", response_model=CVResponse)
async def get_or_create_cv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        portfolio = Portfolio(user_id=current_user.id)
        db.add(portfolio)
        db.flush()
    
    cv = db.query(CV).filter(CV.portfolio_id == portfolio.id).first()
    
    if not cv:
        cv = CV(
            portfolio_id=portfolio.id,
            email=current_user.email
        )
        db.add(cv)
        db.commit()
        db.flush()
    
    # Load relationships
    cv.experiences = db.query(Experience).filter(Experience.cv_id == cv.id).all()
    cv.educations = db.query(Education).filter(Education.cv_id == cv.id).all()
    cv.skills = db.query(Skill).filter(Skill.cv_id == cv.id).all()
    cv.certificates = db.query(Certificate).filter(Certificate.cv_id == cv.id).all()
    
    return cv


@router.put("/cv", response_model=CVResponse)
async def update_cv(
    cv_data: CVCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    cv = db.query(CV).filter(CV.portfolio_id == portfolio.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    
    for key, value in cv_data.dict().items():
        setattr(cv, key, value)
    
    cv.updated_at = datetime.now()
    db.commit()
    db.refresh(cv)
    
    # Load relationships
    cv.experiences = db.query(Experience).filter(Experience.cv_id == cv.id).all()
    cv.educations = db.query(Education).filter(Education.cv_id == cv.id).all()
    cv.skills = db.query(Skill).filter(Skill.cv_id == cv.id).all()
    cv.certificates = db.query(Certificate).filter(Certificate.cv_id == cv.id).all()
    
    return cv
    
    # Load relationships
    cv.experiences = db.query(Experience).filter(Experience.cv_id == cv.id).all()
    cv.educations = db.query(Education).filter(Education.cv_id == cv.id).all()
    cv.skills = db.query(Skill).filter(Skill.cv_id == cv.id).all()
    
    return cv


# Experience endpoints
@router.post("/cv/experiences", response_model=ExperienceResponse)
async def add_experience(
    experience_data: ExperienceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    cv = db.query(CV).filter(CV.portfolio_id == portfolio.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    
    experience = Experience(
        cv_id=cv.id,
        **experience_data.dict()
    )
    db.add(experience)
    db.commit()
    db.refresh(experience)
    
    return experience


@router.put("/cv/experiences/{experience_id}", response_model=ExperienceResponse)
async def update_experience(
    experience_id: int,
    experience_data: ExperienceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    experience = db.query(Experience).filter(Experience.id == experience_id).first()
    if not experience:
        raise HTTPException(status_code=404, detail="Experience not found")
    
    cv = db.query(CV).filter(CV.id == experience.cv_id).first()
    portfolio = db.query(Portfolio).filter(Portfolio.id == cv.portfolio_id).first()
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    for key, value in experience_data.dict().items():
        setattr(experience, key, value)
    
    db.commit()
    db.refresh(experience)
    
    return experience


@router.delete("/cv/experiences/{experience_id}")
async def delete_experience(
    experience_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    experience = db.query(Experience).filter(Experience.id == experience_id).first()
    if not experience:
        raise HTTPException(status_code=404, detail="Experience not found")
    
    cv = db.query(CV).filter(CV.id == experience.cv_id).first()
    portfolio = db.query(Portfolio).filter(Portfolio.id == cv.portfolio_id).first()
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    db.delete(experience)
    db.commit()
    
    return {"message": "Experience deleted successfully"}


# Education endpoints
@router.post("/cv/educations", response_model=EducationResponse)
async def add_education(
    education_data: EducationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    cv = db.query(CV).filter(CV.portfolio_id == portfolio.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    
    education = Education(
        cv_id=cv.id,
        **education_data.dict()
    )
    db.add(education)
    db.commit()
    db.refresh(education)
    
    return education


@router.put("/cv/educations/{education_id}", response_model=EducationResponse)
async def update_education(
    education_id: int,
    education_data: EducationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    education = db.query(Education).filter(Education.id == education_id).first()
    if not education:
        raise HTTPException(status_code=404, detail="Education not found")
    
    cv = db.query(CV).filter(CV.id == education.cv_id).first()
    portfolio = db.query(Portfolio).filter(Portfolio.id == cv.portfolio_id).first()
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    for key, value in education_data.dict().items():
        setattr(education, key, value)
    
    db.commit()
    db.refresh(education)
    
    return education


@router.delete("/cv/educations/{education_id}")
async def delete_education(
    education_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    education = db.query(Education).filter(Education.id == education_id).first()
    if not education:
        raise HTTPException(status_code=404, detail="Education not found")
    
    cv = db.query(CV).filter(CV.id == education.cv_id).first()
    portfolio = db.query(Portfolio).filter(Portfolio.id == cv.portfolio_id).first()
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    db.delete(education)
    db.commit()
    
    return {"message": "Education deleted successfully"}


# Skills endpoints
@router.post("/cv/skills", response_model=SkillResponse)
async def add_skill(
    skill_data: SkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    cv = db.query(CV).filter(CV.portfolio_id == portfolio.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    
    skill = Skill(
        cv_id=cv.id,
        **skill_data.dict()
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    
    return skill


@router.put("/cv/skills/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: int,
    skill_data: SkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    cv = db.query(CV).filter(CV.id == skill.cv_id).first()
    portfolio = db.query(Portfolio).filter(Portfolio.id == cv.portfolio_id).first()
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    for key, value in skill_data.dict().items():
        setattr(skill, key, value)
    
    db.commit()
    db.refresh(skill)
    
    return skill


@router.delete("/cv/skills/{skill_id}")
async def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    cv = db.query(CV).filter(CV.id == skill.cv_id).first()
    portfolio = db.query(Portfolio).filter(Portfolio.id == cv.portfolio_id).first()
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    db.delete(skill)
    db.commit()
    
    return {"message": "Skill deleted successfully"}


# Certificates endpoints
@router.post("/cv/certificates", response_model=CertificateResponse)
async def add_certificate(
    certificate_data: CertificateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    cv = db.query(CV).filter(CV.portfolio_id == portfolio.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    
    certificate = Certificate(
        cv_id=cv.id,
        **certificate_data.dict()
    )
    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    
    return certificate


@router.put("/cv/certificates/{certificate_id}", response_model=CertificateResponse)
async def update_certificate(
    certificate_id: int,
    certificate_data: CertificateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    cv = db.query(CV).filter(CV.id == certificate.cv_id).first()
    portfolio = db.query(Portfolio).filter(Portfolio.id == cv.portfolio_id).first()
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    for key, value in certificate_data.dict().items():
        setattr(certificate, key, value)
    
    db.commit()
    db.refresh(certificate)
    
    return certificate


@router.delete("/cv/certificates/{certificate_id}")
async def delete_certificate(
    certificate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    cv = db.query(CV).filter(CV.id == certificate.cv_id).first()
    portfolio = db.query(Portfolio).filter(Portfolio.id == cv.portfolio_id).first()
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    db.delete(certificate)
    db.commit()
    
    return {"message": "Certificate deleted successfully"}
