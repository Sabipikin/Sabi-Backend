#!/usr/bin/env python3
"""
Daily analytics update script
This script should be run daily (e.g., via cron) to update the analytics table with current data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, Analytics, User, Enrollment, Payment, Complaint
from sqlalchemy import func

def update_daily_analytics():
    """Update today's analytics record with current data"""
    db = SessionLocal()

    try:
        # Get today's date (start of day)
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Check if we already have analytics for today
        existing_analytics = db.query(Analytics).filter(
            func.date(Analytics.date) == today.date()
        ).first()

        # Generate current analytics
        from routes.admin import generate_current_analytics
        current_data = generate_current_analytics(db)

        if existing_analytics:
            # Update existing record
            existing_analytics.total_users = current_data.total_users
            existing_analytics.active_users = current_data.active_users
            existing_analytics.new_enrollments = current_data.new_enrollments
            existing_analytics.completed_courses = current_data.completed_courses
            existing_analytics.total_revenue = current_data.total_revenue
            existing_analytics.total_complaints = current_data.total_complaints
            existing_analytics.resolved_complaints = current_data.resolved_complaints
            print(f"✅ Updated analytics for {today.date()}")
        else:
            # Create new record
            new_analytics = Analytics(
                date=today,
                total_users=current_data.total_users,
                active_users=current_data.active_users,
                new_enrollments=current_data.new_enrollments,
                completed_courses=current_data.completed_courses,
                total_revenue=current_data.total_revenue,
                total_complaints=current_data.total_complaints,
                resolved_complaints=current_data.resolved_complaints
            )
            db.add(new_analytics)
            print(f"✅ Created new analytics record for {today.date()}")

        db.commit()

    except Exception as e:
        print(f"❌ Error updating daily analytics: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_daily_analytics()