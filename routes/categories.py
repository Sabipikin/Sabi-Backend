from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Category, Course
from schemas import CategoryCreate, CategoryResponse, CategoryUpdate
from routes.admin_auth import get_current_admin

router = APIRouter(prefix="/api/admin/categories", tags=["admin-categories"])


@router.post("/", response_model=CategoryResponse)
async def create_category(
    category: CategoryCreate,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new category (SuperAdmin only)"""
    # Check if category name already exists
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists"
        )

    new_category = Category(**category.dict())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return CategoryResponse.from_orm(new_category)


@router.get("/", response_model=list[CategoryResponse])
async def get_categories(
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True
):
    """Get all categories"""
    query = db.query(Category)
    if active_only:
        query = query.filter(Category.is_active == True)
    query = query.order_by(Category.order, Category.name)
    categories = query.offset(skip).limit(limit).all()
    return [CategoryResponse.from_orm(cat) for cat in categories]


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get a specific category"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return CategoryResponse.from_orm(category)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update a category"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Check if new name conflicts with existing category
    if category_update.name:
        existing = db.query(Category).filter(
            Category.name == category_update.name,
            Category.id != category_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists"
            )

    # Update fields
    for field, value in category_update.dict(exclude_unset=True).items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return CategoryResponse.from_orm(category)


@router.post("/delete/{category_id}")
async def delete_category(
    category_id: str,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a category (only if no courses use it)"""
    try:
        category_id_int = int(category_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category ID"
        )
    
    category = db.query(Category).filter(Category.id == category_id_int).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Check if any courses use this category
    courses_using_category = db.query(Course).filter(Course.category_id == category_id_int).count()
    if courses_using_category > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category: {courses_using_category} courses are using it"
        )

    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}