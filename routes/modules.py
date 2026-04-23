"""
API routes for course modules and lesson content
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Course, Module, LessonContent, User
from schemas import ModuleCreate, ModuleResponse, LessonContentCreate, LessonContentResponse
from routes.auth import get_current_user

router = APIRouter(prefix="/api/modules", tags=["modules"])


@router.post("/courses/{course_id}/modules", response_model=ModuleResponse)
async def create_module(
    course_id: int,
    module: ModuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new module/class within a course"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Only course instructor can create modules
    if course.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only course instructor can create modules")
    
    new_module = Module(
        course_id=course_id,
        **module.dict()
    )
    db.add(new_module)
    db.commit()
    db.refresh(new_module)
    return ModuleResponse.from_orm(new_module)


@router.get("/courses/{course_id}/modules", response_model=list[ModuleResponse])
async def get_course_modules(
    course_id: int,
    db: Session = Depends(get_db)
):
    """Get all modules for a course"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    modules = db.query(Module).filter(Module.course_id == course_id).order_by(Module.order).all()
    return [ModuleResponse.from_orm(m) for m in modules]


@router.get("/modules/{module_id}", response_model=ModuleResponse)
async def get_module(module_id: int, db: Session = Depends(get_db)):
    """Get a specific module"""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return ModuleResponse.from_orm(module)


@router.put("/modules/{module_id}", response_model=ModuleResponse)
async def update_module(
    module_id: int,
    module_data: ModuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a module"""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    course = db.query(Course).filter(Course.id == module.course_id).first()
    if course.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only course instructor can update modules")
    
    for key, value in module_data.dict().items():
        setattr(module, key, value)
    
    db.commit()
    db.refresh(module)
    return ModuleResponse.from_orm(module)


@router.delete("/modules/{module_id}")
async def delete_module(
    module_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a module"""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    course = db.query(Course).filter(Course.id == module.course_id).first()
    if course.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only course instructor can delete modules")
    
    db.delete(module)
    db.commit()
    return {"status": "deleted"}


# Lesson Content Endpoints
@router.post("/modules/{module_id}/content", response_model=LessonContentResponse)
async def create_lesson_content(
    module_id: int,
    content: LessonContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create lesson content (video, notes, slides, assessment, project)"""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    course = db.query(Course).filter(Course.id == module.course_id).first()
    if course.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only course instructor can create content")
    
    new_content = LessonContent(
        module_id=module_id,
        **content.dict()
    )
    db.add(new_content)
    db.commit()
    db.refresh(new_content)
    return LessonContentResponse.from_orm(new_content)


@router.get("/modules/{module_id}/content", response_model=list[LessonContentResponse])
async def get_module_content(
    module_id: int,
    db: Session = Depends(get_db)
):
    """Get all content for a module"""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    content_items = db.query(LessonContent).filter(LessonContent.module_id == module_id).order_by(LessonContent.order).all()
    return [LessonContentResponse.from_orm(item) for item in content_items]


@router.get("/content/{content_id}", response_model=LessonContentResponse)
async def get_lesson_content(content_id: int, db: Session = Depends(get_db)):
    """Get a specific lesson content item"""
    content = db.query(LessonContent).filter(LessonContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return LessonContentResponse.from_orm(content)


@router.put("/content/{content_id}", response_model=LessonContentResponse)
async def update_lesson_content(
    content_id: int,
    content_data: LessonContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update lesson content"""
    content = db.query(LessonContent).filter(LessonContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    module = db.query(Module).filter(Module.id == content.module_id).first()
    course = db.query(Course).filter(Course.id == module.course_id).first()
    
    if course.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only course instructor can update content")
    
    for key, value in content_data.dict(exclude_unset=True).items():
        setattr(content, key, value)
    
    db.commit()
    db.refresh(content)
    return LessonContentResponse.from_orm(content)


@router.delete("/content/{content_id}")
async def delete_lesson_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete lesson content"""
    content = db.query(LessonContent).filter(LessonContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    module = db.query(Module).filter(Module.id == content.module_id).first()
    course = db.query(Course).filter(Course.id == module.course_id).first()
    
    if course.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only course instructor can delete content")
    
    db.delete(content)
    db.commit()
    return {"status": "deleted"}
