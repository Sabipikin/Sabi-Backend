#!/usr/bin/env python3
"""Script to populate sample lessons for testing"""

import os
import sys

# Add backend to path
sys.path.insert(0, '/Users/sabipikin/Documents/Sabi Educate/sabipath/backend')

from database import SessionLocal, Base, engine
from models import Course, Lesson, User
from datetime import datetime

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

def populate_lessons():
    db = SessionLocal()
    try:
        # Get first few courses
        courses = db.query(Course).limit(5).all()
        print(f"Found {len(courses)} courses")
        
        for course in courses:
            # Check if lessons already exist
            existing_lessons = db.query(Lesson).filter(Lesson.course_id == course.id).count()
            if existing_lessons == 0:
                # Create sample lessons
                lessons_data = [
                    Lesson(
                        course_id=course.id,
                        title=f"Introduction to {course.title}",
                        content=f"Learn the fundamentals of {course.title.lower()}. This lesson covers the basic concepts and getting started.",
                        order=1,
                        duration_minutes=30,
                        created_at=datetime.now()
                    ),
                    Lesson(
                        course_id=course.id,
                        title=f"Core Concepts",
                        content="Deep dive into the core concepts and principles.",
                        order=2,
                        duration_minutes=45,
                        created_at=datetime.now()
                    ),
                    Lesson(
                        course_id=course.id,
                        title=f"Practical Applications",
                        content="Learn real-world applications and best practices.",
                        order=3,
                        duration_minutes=40,
                        created_at=datetime.now()
                    ),
                    Lesson(
                        course_id=course.id,
                        title=f"Advanced Topics",
                        content="Explore advanced topics and optimization techniques.",
                        order=4,
                        duration_minutes=50,
                        created_at=datetime.now()
                    ),
                    Lesson(
                        course_id=course.id,
                        title=f"Project & Assessment",
                        content="Complete a project to apply everything you've learned.",
                        order=5,
                        duration_minutes=60,
                        created_at=datetime.now()
                    ),
                ]
                
                for lesson in lessons_data:
                    db.add(lesson)
                
                db.commit()
                print(f"✓ Created 5 lessons for course '{course.title}' (ID: {course.id})")
            else:
                print(f"- Course '{course.title}' (ID: {course.id}) already has {existing_lessons} lessons")
        
        print("\n✓ Sample lessons populated successfully!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_lessons()
