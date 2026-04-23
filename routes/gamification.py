from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Points, Streak, Badge, Progress
from schemas import PointsResponse, StreakResponse, BadgeResponse, GamificationStatsResponse
from routes.auth import get_current_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/gamification", tags=["gamification"])

# Points: +10 for completing a lesson, +5 for weekly streak
LESSON_COMPLETION_POINTS = 10
DAILY_ACTIVITY_BONUS = 5
BADGE_THRESHOLDS = {
    "first_lesson": 1,
    "dedicated_learner": 50,
    "point_master": 100,
    "week_warrior": 5,  # 5 day streak
}


@router.post("/points/award")
async def award_points(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Award points for completing a lesson"""
    user_id = current_user.id

    # Get or create points record
    points = db.query(Points).filter(Points.user_id == user_id).first()
    if not points:
        points = Points(user_id=user_id, total_points=0, weekly_points=0)
        db.add(points)

    # Award points
    points.total_points += LESSON_COMPLETION_POINTS
    points.weekly_points += LESSON_COMPLETION_POINTS
    points.last_updated = datetime.utcnow()

    # Update streak
    streak = db.query(Streak).filter(Streak.user_id == user_id).first()
    if not streak:
        streak = Streak(user_id=user_id, current_streak=1, longest_streak=1)
        db.add(streak)
    else:
        today = datetime.utcnow().date()
        last_activity = (
            streak.last_activity_date.date()
            if streak.last_activity_date
            else today - timedelta(days=2)
        )

        if last_activity == today:
            # Already active today
            pass
        elif last_activity == today - timedelta(days=1):
            # Consecutive day, increase streak
            streak.current_streak += 1
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
            points.total_points += DAILY_ACTIVITY_BONUS
            points.weekly_points += DAILY_ACTIVITY_BONUS
        else:
            # Streak broken, reset
            streak.current_streak = 1

    streak.last_activity_date = datetime.utcnow()

    # Check for badges
    _check_and_award_badges(user_id, points, streak, db)

    db.commit()
    db.refresh(points)

    return PointsResponse.from_orm(points)


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's gamification stats"""
    try:
        user_id = current_user.id

        # Get or create points
        points = db.query(Points).filter(Points.user_id == user_id).first()
        if not points:
            points = Points(user_id=user_id, total_points=0, weekly_points=0)
            db.add(points)
            db.flush()  # Use flush instead of commit to keep transaction open
            db.refresh(points)

        # Get or create streak
        streak = db.query(Streak).filter(Streak.user_id == user_id).first()
        if not streak:
            streak = Streak(user_id=user_id, current_streak=0, longest_streak=0)
            db.add(streak)
            db.flush()  # Use flush instead of commit
            db.refresh(streak)

        # Get badges
        badges = db.query(Badge).filter(Badge.user_id == user_id).all()

        db.commit()

        return GamificationStatsResponse(
            points=PointsResponse.from_orm(points),
            streak=StreakResponse.from_orm(streak),
            badges=[BadgeResponse.from_orm(b) for b in badges],
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error fetching gamification stats: {str(e)}")


@router.get("/leaderboard")
async def get_leaderboard(db: Session = Depends(get_db)):
    """Get top 10 users by points (public)"""
    top_users = (
        db.query(User.id, User.full_name, Points.total_points)
        .join(Points, User.id == Points.user_id)
        .order_by(Points.total_points.desc())
        .limit(10)
        .all()
    )

    return [
        {"user_id": u[0], "full_name": u[1] or "Anonymous", "points": u[2]}
        for u in top_users
    ]


@router.post("/badges/check")
async def check_badges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually check and award any pending badges"""
    user_id = current_user.id

    points = db.query(Points).filter(Points.user_id == user_id).first()
    streak = db.query(Streak).filter(Streak.user_id == user_id).first()

    if points and streak:
        _check_and_award_badges(user_id, points, streak, db)
        db.commit()

    badges = db.query(Badge).filter(Badge.user_id == user_id).all()
    return [BadgeResponse.from_orm(b) for b in badges]


# Helper function to check and award badges
def _check_and_award_badges(user_id: int, points: Points, streak: Streak, db: Session):
    """Check if user qualifies for any new badges"""
    existing_badges = db.query(Badge.badge_name).filter(Badge.user_id == user_id).all()
    existing_badge_names = {b[0] for b in existing_badges}

    # First Lesson badge
    if "first_lesson" not in existing_badge_names and points.total_points >= LESSON_COMPLETION_POINTS:
        badge = Badge(
            user_id=user_id,
            badge_name="first_lesson",
            badge_icon="🎓",
            description="Completed your first lesson!",
        )
        db.add(badge)

    # Dedicated Learner (50 points)
    if (
        "dedicated_learner" not in existing_badge_names
        and points.total_points >= BADGE_THRESHOLDS["dedicated_learner"]
    ):
        badge = Badge(
            user_id=user_id,
            badge_name="dedicated_learner",
            badge_icon="📚",
            description="Earned 50 points!",
        )
        db.add(badge)

    # Point Master (100 points)
    if (
        "point_master" not in existing_badge_names
        and points.total_points >= BADGE_THRESHOLDS["point_master"]
    ):
        badge = Badge(
            user_id=user_id,
            badge_name="point_master",
            badge_icon="⭐",
            description="Earned 100 points!",
        )
        db.add(badge)

    # Week Warrior (5 day streak)
    if (
        "week_warrior" not in existing_badge_names
        and streak.current_streak >= BADGE_THRESHOLDS["week_warrior"]
    ):
        badge = Badge(
            user_id=user_id,
            badge_name="week_warrior",
            badge_icon="🔥",
            description="5 day learning streak!",
        )
        db.add(badge)


@router.get("/weekly-reset")
async def reset_weekly_points(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset weekly points (call this via cron job weekly)"""
    # For now, just reset a single user's weekly points (in production, call for all users)
    points = db.query(Points).filter(Points.user_id == current_user.id).first()
    if points:
        points.weekly_points = 0
        db.commit()
        db.refresh(points)
        return PointsResponse.from_orm(points)
    return {"error": "Points not found"}
