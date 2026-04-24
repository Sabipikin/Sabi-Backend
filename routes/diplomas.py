from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Diploma, Program, Course
from schemas import DiplomaCreate, DiplomaResponse, DiplomaUpdate
from routes.admin_auth import get_current_admin

router = APIRouter(prefix="/api/admin/diplomas", tags=["admin-diplomas"])
public_router = APIRouter(prefix="/api/diplomas", tags=["diplomas"])


@router.post("/", response_model=DiplomaResponse)
async def create_diploma(
    diploma: DiplomaCreate,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new diploma (SuperAdmin only)"""
    # Check if diploma title already exists
    existing = db.query(Diploma).filter(Diploma.title == diploma.title).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Diploma with this title already exists"
        )

    new_diploma = Diploma(**diploma.dict())
    db.add(new_diploma)
    db.commit()
    db.refresh(new_diploma)
    return DiplomaResponse.from_orm(new_diploma)


@router.get("/", response_model=list[DiplomaResponse])
async def get_diplomas(
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    level_filter: str = None
):
    """Get all diplomas with optional filtering"""
    query = db.query(Diploma)

    if status_filter:
        query = query.filter(Diploma.status == status_filter)

    if level_filter:
        query = query.filter(Diploma.level == level_filter)

    query = query.order_by(Diploma.title)
    diplomas = query.offset(skip).limit(limit).all()
    return [DiplomaResponse.from_orm(d) for d in diplomas]


@router.get("/{diploma_id}", response_model=DiplomaResponse)
async def get_diploma(
    diploma_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get a specific diploma"""
    diploma = db.query(Diploma).filter(Diploma.id == diploma_id).first()
    if not diploma:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diploma not found"
        )
    return DiplomaResponse.from_orm(diploma)


@router.put("/{diploma_id}", response_model=DiplomaResponse)
async def update_diploma(
    diploma_id: int,
    diploma_update: DiplomaUpdate,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update a diploma"""
    diploma = db.query(Diploma).filter(Diploma.id == diploma_id).first()
    if not diploma:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diploma not found"
        )

    # Update fields
    for field, value in diploma_update.dict(exclude_unset=True).items():
        setattr(diploma, field, value)

    db.commit()
    db.refresh(diploma)
    return DiplomaResponse.from_orm(diploma)


@router.delete("/{diploma_id}")
async def delete_diploma(
    diploma_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a diploma (only if no programs are assigned to it)"""
    diploma = db.query(Diploma).filter(Diploma.id == diploma_id).first()
    if not diploma:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diploma not found"
        )

    # Check if any programs are assigned to this diploma
    programs_using_diploma = db.query(Program).filter(Program.diploma_id == diploma_id).count()
    if programs_using_diploma > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete diploma: {programs_using_diploma} programs are assigned to it"
        )

    db.delete(diploma)
    db.commit()
    return {"message": "Diploma deleted successfully"}


@router.get("/{diploma_id}/programs", response_model=list[dict])
async def get_diploma_programs(
    diploma_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all programs in a diploma"""
    diploma = db.query(Diploma).filter(Diploma.id == diploma_id).first()
    if not diploma:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diploma not found"
        )

    programs = db.query(Program).filter(Program.diploma_id == diploma_id).order_by(Program.order, Program.title).all()

    # Return programs with basic info
    return [{
        "id": program.id,
        "title": program.title,
        "description": program.description,
        "short_description": program.short_description,
        "duration_months": program.duration_months,
        "difficulty": program.difficulty,
        "status": program.status,
        "order": program.order,
        "is_featured": program.is_featured
    } for program in programs]


@router.get("/{diploma_id}/structure", response_model=dict)
async def get_diploma_structure(
    diploma_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get complete diploma structure with programs and courses"""
    diploma = db.query(Diploma).filter(Diploma.id == diploma_id).first()
    if not diploma:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diploma not found"
        )

    programs = db.query(Program).filter(Program.diploma_id == diploma_id).order_by(Program.order, Program.title).all()

    structure = {
        "diploma": {
            "id": diploma.id,
            "title": diploma.title,
            "description": diploma.description,
            "duration_years": diploma.duration_years,
            "level": diploma.level,
            "field": diploma.field,
            "status": diploma.status
        },
        "programs": []
    }

    for program in programs:
        courses = db.query(Course).filter(Course.program_id == program.id).order_by(Course.title).all()

        program_data = {
            "id": program.id,
            "title": program.title,
            "description": program.description,
            "duration_months": program.duration_months,
            "difficulty": program.difficulty,
            "status": program.status,
            "order": program.order,
            "courses": [{
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "difficulty": course.difficulty,
                "duration_hours": course.duration_hours,
                "status": course.status
            } for course in courses]
        }

        structure["programs"].append(program_data)

    return structure


# PUBLIC ENDPOINTS - No authentication required

@public_router.get("/", response_model=list[DiplomaResponse])
async def get_published_diplomas(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    search: str = Query(None),
    level: str = Query(None)
):
    """Get all published diplomas (public view)"""
    query = db.query(Diploma).filter(Diploma.status == "published")

    if search:
        query = query.filter(Diploma.title.ilike(f"%{search}%"))

    if level:
        query = query.filter(Diploma.level == level)

    query = query.order_by(Diploma.title)
    diplomas = query.offset(skip).limit(limit).all()
    return [DiplomaResponse.from_orm(d) for d in diplomas]


@public_router.get("/{diploma_id}", response_model=DiplomaResponse)
async def get_published_diploma(
    diploma_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific published diploma"""
    diploma = db.query(Diploma).filter(
        Diploma.id == diploma_id,
        Diploma.status == "published"
    ).first()
    if not diploma:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diploma not found"
        )
    return DiplomaResponse.from_orm(diploma)


@public_router.get("/{diploma_id}/structure")
async def get_diploma_structure_public(
    diploma_id: int,
    db: Session = Depends(get_db)
):
    """Get the full structure of a diploma including programs and courses"""
    diploma = db.query(Diploma).filter(
        Diploma.id == diploma_id,
        Diploma.status == "published"
    ).first()
    if not diploma:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diploma not found"
        )

    structure = {
        "id": diploma.id,
        "title": diploma.title,
        "description": diploma.description,
        "level": diploma.level,
        "duration_years": diploma.duration_years,
        "programs": []
    }

    # Get all programs in this diploma
    programs = db.query(Program).filter(
        Program.diploma_id == diploma_id,
        Program.status == "published"
    ).order_by(Program.order).all()

    for program in programs:
        courses = db.query(Course).filter(
            Course.program_id == program.id,
            Course.status == "published"
        ).order_by(Course.title).all()

        program_data = {
            "id": program.id,
            "title": program.title,
            "description": program.description,
            "duration_months": program.duration_months,
            "difficulty": program.difficulty,
            "status": program.status,
            "order": program.order,
            "courses": [{
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "difficulty": course.difficulty,
                "duration_hours": course.duration_hours,
                "status": course.status
            } for course in courses]
        }

        structure["programs"].append(program_data)

    return structure