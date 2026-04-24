from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Question, LessonContent
from schemas import QuestionCreate, QuestionResponse, QuestionUpdate
from routes.admin_auth import get_current_admin

router = APIRouter(prefix="/api/admin/questions", tags=["admin-questions"])


@router.post("/", response_model=QuestionResponse)
async def create_question(
    question: QuestionCreate,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new question for an assessment"""
    # Verify the content exists and is an assessment
    content = db.query(LessonContent).filter(LessonContent.id == question.content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson content not found"
        )

    if content.content_type != "assessment":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Questions can only be added to assessment content"
        )

    # Validate question type and required fields
    if question.question_type == "objective":
        if not question.options or not question.correct_answer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Objective questions require options and correct_answer"
            )
    elif question.question_type in ["theory", "essay"]:
        if not question.sample_answer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Theory/essay questions require a sample_answer"
            )

    new_question = Question(**question.dict())
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return QuestionResponse.from_orm(new_question)


@router.get("/content/{content_id}", response_model=list[QuestionResponse])
async def get_questions_for_content(
    content_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all questions for a specific assessment content"""
    # Verify the content exists and is an assessment
    content = db.query(LessonContent).filter(LessonContent.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson content not found"
        )

    if content.content_type != "assessment":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This content is not an assessment"
        )

    questions = db.query(Question).filter(
        Question.content_id == content_id
    ).order_by(Question.order).all()

    return [QuestionResponse.from_orm(q) for q in questions]


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get a specific question"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    return QuestionResponse.from_orm(question)


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    question_update: QuestionUpdate,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update a question"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    # Validate question type and required fields if updating type
    if question_update.question_type:
        if question_update.question_type == "objective":
            if (question_update.options is None and question.options is None) or \
               (question_update.correct_answer is None and question.correct_answer is None):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Objective questions require options and correct_answer"
                )
        elif question_update.question_type in ["theory", "essay"]:
            if question_update.sample_answer is None and question.sample_answer is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Theory/essay questions require a sample_answer"
                )

    # Update fields
    for field, value in question_update.dict(exclude_unset=True).items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)
    return QuestionResponse.from_orm(question)


@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a question"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    db.delete(question)
    db.commit()
    return {"message": "Question deleted successfully"}