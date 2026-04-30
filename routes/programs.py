from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Program, Diploma, Course
from schemas import ProgramCreate, ProgramResponse, ProgramUpdate
from routes.admin_auth import get_current_admin

router = APIRouter(prefix="/api/admin/programs", tags=["admin-programs"])
public_router = APIRouter(prefix="/api/programs", tags=["programs"])


@router.post("/", response_model=ProgramResponse)
async def create_program(
    program: ProgramCreate,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new program (SuperAdmin only)"""
    # Check if program title already exists
    existing = db.query(Program).filter(Program.title == program.title).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Program with this title already exists"
        )

    # If diploma_id is provided, verify the diploma exists
    if program.diploma_id:
        diploma = db.query(Diploma).filter(Diploma.id == program.diploma_id).first()
        if not diploma:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diploma not found"
            )

    new_program = Program(**program.dict())
    db.add(new_program)
    db.commit()
    db.refresh(new_program)
    return ProgramResponse.from_orm(new_program)


@router.get("/", response_model=list[ProgramResponse])
async def get_programs(
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    diploma_id: int = None,
    status_filter: str = None
):
    """Get all programs with optional filtering"""
    query = db.query(Program)

    if diploma_id:
        query = query.filter(Program.diploma_id == diploma_id)

    if status_filter:
        query = query.filter(Program.status == status_filter)

    query = query.order_by(Program.order, Program.title)
    programs = query.offset(skip).limit(limit).all()
    return [ProgramResponse.from_orm(p) for p in programs]


@router.get("/{program_id}", response_model=ProgramResponse)
async def get_program(
    program_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get a specific program"""
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found"
        )
    return ProgramResponse.from_orm(program)


@router.put("/{program_id}", response_model=ProgramResponse)
async def update_program(
    program_id: int,
    program_update: ProgramUpdate,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update a program"""
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found"
        )

    # If diploma_id is being updated, verify the diploma exists
    if program_update.diploma_id is not None:
        if program_update.diploma_id:  # Not setting to None
            diploma = db.query(Diploma).filter(Diploma.id == program_update.diploma_id).first()
            if not diploma:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Diploma not found"
                )

    # Update fields
    for field, value in program_update.dict(exclude_unset=True).items():
        setattr(program, field, value)

    db.commit()
    db.refresh(program)
    return ProgramResponse.from_orm(program)


@router.delete("/{program_id}")
async def delete_program(
    program_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a program (only if no courses are assigned to it)"""
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found"
        )

    # Check if any courses are assigned to this program
    courses_using_program = db.query(Course).filter(Course.program_id == program_id).count()
    if courses_using_program > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete program: {courses_using_program} courses are assigned to it"
        )

    db.delete(program)
    db.commit()
    return {"message": "Program deleted successfully"}


@router.get("/{program_id}/courses", response_model=list[dict])
async def get_program_courses(
    program_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all courses in a program"""
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found"
        )

    courses = db.query(Course).filter(Course.program_id == program_id).order_by(Course.title).all()

    # Return courses with basic info
    return [{
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "difficulty": course.difficulty,
        "duration_hours": course.duration_hours,
        "status": course.status
    } for course in courses]


# PUBLIC ENDPOINTS - No authentication required

@public_router.get("/", response_model=list[dict])
async def get_published_programs(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    diploma_id: int = Query(None),
    search: str = Query(None),
    difficulty: str = Query(None)
):
    """Get all published programs (public view)"""
    try:
        query = db.query(Program).filter(Program.status == "published")

        if diploma_id:
            query = query.filter(Program.diploma_id == diploma_id)

        if search:
            query = query.filter(Program.title.ilike(f"%{search}%"))

        if difficulty and difficulty != "all":
            query = query.filter(Program.difficulty == difficulty)

        query = query.order_by(Program.order, Program.title)
        programs = query.offset(skip).limit(limit).all()
        
        result = []
        for p in programs:
            # Count courses in this program
            courses_count = db.query(Course).filter(Course.program_id == p.id).count()
            
            result.append({
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "short_description": p.short_description,
                "diploma_id": p.diploma_id,
                "duration_months": p.duration_months,
                "difficulty": p.difficulty,
                "prerequisites": p.prerequisites,
                "color": p.color,
                "icon": p.icon,
                "image_url": p.image_url,
                "status": p.status,
                "order": p.order,
                "is_featured": p.is_featured,
                "fee": p.fee,
                "promo_amount": p.promo_amount,
                "is_on_promo": p.is_on_promo,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
                "courses_count": courses_count
            })
        
        return result
    except Exception as e:
        print(f"Error in get_published_programs: {e}")
        raise


@public_router.get("/{program_id}", response_model=ProgramResponse)
async def get_published_program(
    program_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific published program with its courses"""
    program = db.query(Program).filter(
        Program.id == program_id,
        Program.status == "published"
    ).first()
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found"
        )
    return ProgramResponse.from_orm(program)


@public_router.get("/{program_id}/courses", response_model=list[dict])
async def get_published_program_courses(
    program_id: int,
    db: Session = Depends(get_db)
):
    """Get all published courses in a program"""
    program = db.query(Program).filter(
        Program.id == program_id,
        Program.status == "published"
    ).first()
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found"
        )

    courses = db.query(Course).filter(
        Course.program_id == program_id,
        Course.status == "published"
    ).order_by(Course.title).all()

    return [{
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "difficulty": course.difficulty,
        "duration_hours": course.duration_hours,
        "status": course.status,
        "fee": course.fee
    } for course in courses]