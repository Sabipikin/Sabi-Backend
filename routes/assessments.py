"""
Assessment and Question Management Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from database import get_db
from models import User, Question, StudentAnswer, AssessmentScore, LessonContent, ContentProgress, Module
from schemas import (
    QuestionCreate, QuestionResponse, QuestionUpdate,
    StudentAnswerCreate, StudentAnswerResponse
)
from .enrollment import aggregate_course_progress
from auth import decode_access_token
import json

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


def get_current_user(token: str, db: Session) -> User:
    """Get current user from token"""
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ============ Question Management Endpoints ============

@router.post("/content/{content_id}/questions", response_model=QuestionResponse)
async def create_question(
    content_id: int,
    question_data: QuestionCreate,
    token: str,
    db: Session = Depends(get_db)
):
    """Create a question for assessment content (Instructor only)"""
    # Verify content exists and is assessment type
    content = db.query(LessonContent).filter(LessonContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if content.content_type != "assessment":
        raise HTTPException(
            status_code=400,
            detail="Questions can only be added to assessment content"
        )
    
    # Create question
    new_question = Question(
        content_id=content_id,
        question_text=question_data.question_text,
        question_type=question_data.question_type,
        order=question_data.order,
        points=question_data.points,
        options=question_data.options,
        correct_answer=question_data.correct_answer,
        sample_answer=question_data.sample_answer
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return new_question


@router.get("/content/{content_id}/questions", response_model=list[QuestionResponse])
async def get_questions(
    content_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get all questions for assessment content"""
    questions = db.query(Question).filter(
        Question.content_id == content_id
    ).order_by(Question.order).offset(skip).limit(limit).all()
    return questions


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    question_data: QuestionUpdate,
    token: str,
    db: Session = Depends(get_db)
):
    """Update a question"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Update fields
    if question_data.question_text is not None:
        question.question_text = question_data.question_text
    if question_data.question_type is not None:
        question.question_type = question_data.question_type
    if question_data.order is not None:
        question.order = question_data.order
    if question_data.points is not None:
        question.points = question_data.points
    if question_data.options is not None:
        question.options = question_data.options
    if question_data.correct_answer is not None:
        question.correct_answer = question_data.correct_answer
    if question_data.sample_answer is not None:
        question.sample_answer = question_data.sample_answer
    
    db.commit()
    db.refresh(question)
    return question


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Delete a question"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    db.delete(question)
    db.commit()
    return {"message": "Question deleted successfully"}


# ============ Student Answer Submission ============

@router.post("/submit-answers")
async def submit_answers(
    content_id: int,
    answers: dict,  # { question_id: answer_text, ... }
    token: str,
    credentials_cookie: str = None,
    db: Session = Depends(get_db)
):
    """
    Submit answers for an assessment
    Validates answers and calculates score
    """
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify content exists
    content = db.query(LessonContent).filter(
        LessonContent.id == content_id
    ).first()
    if not content:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Get all questions for this assessment
    questions = db.query(Question).filter(
        Question.content_id == content_id
    ).all()
    
    if not questions:
        raise HTTPException(status_code=400, detail="No questions found for this assessment")
    
    # Create assessment attempt record
    total_points = sum(q.points for q in questions)
    score = 0
    student_answers = []
    
    # Process each answer
    for question in questions:
        question_id_str = str(question.id)
        answer_text = answers.get(question_id_str, "")
        
        is_correct = False
        points_earned = 0
        
        # Check if answer is correct
        if question.question_type == "objective":
            if answer_text == question.correct_answer:
                is_correct = True
                points_earned = question.points
                score += points_earned
        else:
            # Theory/essay - manual grading needed
            is_correct = None
            points_earned = 0
        
        # Create student answer record
        student_answer = StudentAnswer(
            user_id=user.id,
            question_id=question.id,
            assessment_attempt_id=0,  # Will update after creating AssessmentScore
            answer_text=answer_text,
            is_correct=is_correct,
            points_earned=points_earned
        )
        student_answers.append(student_answer)
    
    # Create assessment score record
    percentage = (score / total_points * 100) if total_points > 0 else 0
    is_passing = percentage >= (content.passing_score or 50)
    
    assessment_score = AssessmentScore(
        user_id=user.id,
        content_id=content_id,
        score=score,
        total_points=total_points,
        percentage=int(percentage),
        is_passing=is_passing
    )
    db.add(assessment_score)
    db.commit()
    db.refresh(assessment_score)
    
    # Update student answers with attempt ID
    for student_answer in student_answers:
        student_answer.assessment_attempt_id = assessment_score.id
        db.add(student_answer)
    db.commit()

    # Mark assessment content progress as complete
    content_progress = db.query(ContentProgress).filter(
        ContentProgress.user_id == user.id,
        ContentProgress.content_id == content_id
    ).first()

    if not content_progress:
        content_progress = ContentProgress(
            user_id=user.id,
            content_id=content_id,
            view_progress_percentage=100,
            time_spent_minutes=0,
            is_completed=True,
            completed_at=datetime.utcnow()
        )
        db.add(content_progress)
    else:
        content_progress.view_progress_percentage = 100
        content_progress.time_spent_minutes = content_progress.time_spent_minutes or 0
        content_progress.is_completed = True
        content_progress.completed_at = datetime.utcnow()
    db.commit()

    content_module = db.query(Module).filter(Module.id == content.module_id).first()
    if content_module:
        aggregate_course_progress(user.id, content_module.course_id, db)

    return {
        "status": "submitted",
        "assessment_id": assessment_score.id,
        "score": score,
        "total_points": total_points,
        "percentage": int(percentage),
        "is_passing": is_passing,
        "message": "Assessment submitted successfully"
    }


@router.get("/assessment/{assessment_id}/answers")
async def get_assessment_answers(
    assessment_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Get student answers for a specific assessment attempt"""
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get assessment score
    assessment = db.query(AssessmentScore).filter(
        AssessmentScore.id == assessment_id,
        AssessmentScore.user_id == user.id
    ).first()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Get all answers for this assessment
    answers = db.query(StudentAnswer).filter(
        StudentAnswer.assessment_attempt_id == assessment_id
    ).all()
    
    return {
        "assessment_id": assessment.id,
        "score": assessment.score,
        "total_points": assessment.total_points,
        "percentage": assessment.percentage,
        "is_passing": assessment.is_passing,
        "answers": [
            {
                "question_id": a.question_id,
                "answer_text": a.answer_text,
                "is_correct": a.is_correct,
                "points_earned": a.points_earned,
                "submitted_at": a.submitted_at
            }
            for a in answers
        ]
    }


@router.get("/content/{content_id}/user-score", response_model=dict)
async def get_user_assessment_score(
    content_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Get user's best score for an assessment"""
    # Get current user
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get best score
    best_score = db.query(AssessmentScore).filter(
        AssessmentScore.user_id == user.id,
        AssessmentScore.content_id == content_id
    ).order_by(AssessmentScore.percentage.desc()).first()
    
    if not best_score:
        return {
            "attempted": False,
            "score": None,
            "total_points": None,
            "percentage": None,
            "is_passing": None
        }
    
    return {
        "attempted": True,
        "score": best_score.score,
        "total_points": best_score.total_points,
        "percentage": best_score.percentage,
        "is_passing": best_score.is_passing,
        "completed_at": best_score.completed_at,
        "attempts": best_score.attempts
    }
