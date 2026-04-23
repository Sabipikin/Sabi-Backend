#!/usr/bin/env python3
"""
Script to populate analytics data for the last 30 days
This creates historical data for trend analysis in the admin dashboard
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, Analytics, User, Enrollment, Payment, Complaint
from sqlalchemy import func

def generate_historical_analytics():
    """Generate analytics data for the last 30 days"""
    db = SessionLocal()

    try:
        # Check if we already have analytics data
        existing_count = db.query(func.count(Analytics.id)).scalar()
        if existing_count > 0:
            print(f"✓ Analytics data already exists ({existing_count} records). Skipping generation.")
            return

        print("📊 Generating historical analytics data for the last 30 days...")

        # Generate data for each of the last 30 days
        for days_ago in range(30, 0, -1):
            date = datetime.utcnow() - timedelta(days=days_ago)

            # Calculate analytics up to that date
            date_filter = date + timedelta(days=1)  # Include the full day

            # Total users registered up to this date
            total_users = db.query(func.count(User.id)).filter(
                User.created_at <= date_filter
            ).scalar()

            # Active users (simplified - all users created before this date)
            active_users = total_users

            # New enrollments on this specific date
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            new_enrollments = db.query(func.count(Enrollment.id)).filter(
                Enrollment.enrolled_at >= day_start,
                Enrollment.enrolled_at < day_end
            ).scalar()

            # Completed courses on this specific date
            completed_courses = db.query(func.count(Enrollment.id)).filter(
                Enrollment.completed_at.isnot(None),
                Enrollment.completed_at >= day_start,
                Enrollment.completed_at < day_end
            ).scalar()

            # Revenue from payments completed on this date
            total_revenue = db.query(func.sum(Payment.amount)).filter(
                Payment.status == "completed",
                Payment.created_at >= day_start,
                Payment.created_at < day_end
            ).scalar() or 0

            # Complaints created on this date
            total_complaints = db.query(func.count(Complaint.id)).filter(
                Complaint.created_at >= day_start,
                Complaint.created_at < day_end
            ).scalar()

            # Resolved complaints on this date
            resolved_complaints = db.query(func.count(Complaint.id)).filter(
                Complaint.status == "resolved",
                Complaint.resolved_at.isnot(None),
                Complaint.resolved_at >= day_start,
                Complaint.resolved_at < day_end
            ).scalar()

            # Create analytics record
            analytics_record = Analytics(
                date=date,
                total_users=total_users,
                active_users=active_users,
                new_enrollments=new_enrollments,
                completed_courses=completed_courses,
                total_revenue=total_revenue,
                total_complaints=total_complaints,
                resolved_complaints=resolved_complaints
            )

            db.add(analytics_record)

        db.commit()
        print("✅ Successfully generated 30 days of historical analytics data!")

    except Exception as e:
        print(f"❌ Error generating analytics data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_historical_analytics()