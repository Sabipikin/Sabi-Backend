"""Service to seed career pathway data"""

from database import SessionLocal
from models import (
    CareerRole, CareerPathway, SkillDefinition, CareerRoleSkill, CourseSkill
)
from sqlalchemy import func


def seed_skills(db):
    """Seed initial skills data"""
    skills_data = [
        {"name": "Python", "category": "Programming", "demand_score": 95, "popularity_score": 90},
        {"name": "JavaScript", "category": "Programming", "demand_score": 90, "popularity_score": 95},
        {"name": "React", "category": "Frontend", "demand_score": 85, "popularity_score": 88},
        {"name": "Node.js", "category": "Backend", "demand_score": 80, "popularity_score": 85},
        {"name": "FastAPI", "category": "Backend", "demand_score": 75, "popularity_score": 70},
        {"name": "SQL", "category": "Database", "demand_score": 88, "popularity_score": 92},
        {"name": "Docker", "category": "DevOps", "demand_score": 82, "popularity_score": 80},
        {"name": "Data Analysis", "category": "Data Science", "demand_score": 80, "popularity_score": 82},
        {"name": "Machine Learning", "category": "AI/ML", "demand_score": 85, "popularity_score": 87},
        {"name": "AWS", "category": "Cloud", "demand_score": 78, "popularity_score": 75},
    ]
    
    for skill_data in skills_data:
        existing = db.query(SkillDefinition).filter(SkillDefinition.name == skill_data["name"]).first()
        if not existing:
            skill = SkillDefinition(**skill_data)
            db.add(skill)
    
    db.commit()
    return db.query(SkillDefinition).all()


def seed_career_roles(db):
    """Seed initial career roles data"""
    roles_data = [
        {
            "title": "Full Stack Developer",
            "description": "Build complete web applications from frontend to backend",
            "category": "Technology",
            "salary_range": "£50k-£90k",
            "difficulty": "intermediate",
            "popularity_score": 92,
            "is_trending": True,
            "is_featured": True,
        },
        {
            "title": "Data Scientist",
            "description": "Analyze data and build machine learning models",
            "category": "Technology",
            "salary_range": "£60k-£120k",
            "difficulty": "advanced",
            "popularity_score": 88,
            "is_trending": True,
            "is_featured": True,
        },
        {
            "title": "DevOps Engineer",
            "description": "Manage infrastructure and deployment pipelines",
            "category": "Technology",
            "salary_range": "£55k-£95k",
            "difficulty": "advanced",
            "popularity_score": 85,
            "is_trending": False,
            "is_featured": True,
        },
        {
            "title": "Frontend Developer",
            "description": "Create beautiful user interfaces and web experiences",
            "category": "Technology",
            "salary_range": "£45k-£80k",
            "difficulty": "intermediate",
            "popularity_score": 90,
            "is_trending": True,
            "is_featured": True,
        },
        {
            "title": "Backend Developer",
            "description": "Build server-side logic and APIs",
            "category": "Technology",
            "salary_range": "£50k-£95k",
            "difficulty": "intermediate",
            "popularity_score": 87,
            "is_trending": False,
            "is_featured": True,
        },
    ]
    
    for role_data in roles_data:
        existing = db.query(CareerRole).filter(CareerRole.title == role_data["title"]).first()
        if not existing:
            role = CareerRole(**role_data)
            db.add(role)
    
    db.commit()
    return db.query(CareerRole).all()


def seed_career_role_skills(db):
    """Map skills to career roles"""
    skill_mappings = {
        "Full Stack Developer": [
            {"skill": "JavaScript", "proficiency": "advanced", "importance": 10},
            {"skill": "React", "proficiency": "advanced", "importance": 9},
            {"skill": "Python", "proficiency": "intermediate", "importance": 7},
            {"skill": "Node.js", "proficiency": "advanced", "importance": 9},
            {"skill": "SQL", "proficiency": "intermediate", "importance": 8},
            {"skill": "Docker", "proficiency": "intermediate", "importance": 6},
        ],
        "Data Scientist": [
            {"skill": "Python", "proficiency": "advanced", "importance": 10},
            {"skill": "Machine Learning", "proficiency": "advanced", "importance": 10},
            {"skill": "Data Analysis", "proficiency": "advanced", "importance": 9},
            {"skill": "SQL", "proficiency": "intermediate", "importance": 8},
        ],
        "DevOps Engineer": [
            {"skill": "Docker", "proficiency": "advanced", "importance": 10},
            {"skill": "AWS", "proficiency": "advanced", "importance": 9},
            {"skill": "Python", "proficiency": "intermediate", "importance": 6},
            {"skill": "SQL", "proficiency": "intermediate", "importance": 7},
        ],
        "Frontend Developer": [
            {"skill": "JavaScript", "proficiency": "advanced", "importance": 10},
            {"skill": "React", "proficiency": "advanced", "importance": 10},
            {"skill": "Node.js", "proficiency": "beginner", "importance": 3},
        ],
        "Backend Developer": [
            {"skill": "Python", "proficiency": "advanced", "importance": 10},
            {"skill": "Node.js", "proficiency": "intermediate", "importance": 8},
            {"skill": "SQL", "proficiency": "advanced", "importance": 9},
            {"skill": "FastAPI", "proficiency": "advanced", "importance": 9},
        ],
    }
    
    for role_title, skills in skill_mappings.items():
        role = db.query(CareerRole).filter(CareerRole.title == role_title).first()
        if not role:
            continue
        
        for skill_mapping in skills:
            skill = db.query(SkillDefinition).filter(SkillDefinition.name == skill_mapping["skill"]).first()
            if not skill:
                continue
            
            # Check if already mapped
            existing = db.query(CareerRoleSkill).filter(
                CareerRoleSkill.career_role_id == role.id,
                CareerRoleSkill.skill_id == skill.id
            ).first()
            
            if not existing:
                mapping = CareerRoleSkill(
                    career_role_id=role.id,
                    skill_id=skill.id,
                    proficiency_level=skill_mapping["proficiency"],
                    importance=skill_mapping["importance"]
                )
                db.add(mapping)
    
    db.commit()


def seed_career_pathways(db):
    """Seed initial career pathways"""
    pathways_data = [
        {
            "title": "Full Stack Developer Path",
            "description": "Learn full stack web development from frontend to backend",
            "duration_months": 12,
            "difficulty": "intermediate",
            "popularity_score": 95,
        },
        {
            "title": "Data Science Career Path",
            "description": "Master data science and machine learning fundamentals",
            "duration_months": 14,
            "difficulty": "advanced",
            "popularity_score": 88,
        },
        {
            "title": "DevOps Mastery Path",
            "description": "Become a DevOps engineer with cloud and containerization skills",
            "duration_months": 10,
            "difficulty": "advanced",
            "popularity_score": 80,
        },
        {
            "title": "React Developer Path",
            "description": "Master modern React and frontend development",
            "duration_months": 8,
            "difficulty": "intermediate",
            "popularity_score": 92,
        },
    ]
    
    roles = db.query(CareerRole).all()
    role_index = 0
    
    for pathway_data in pathways_data:
        existing = db.query(CareerPathway).filter(
            CareerPathway.title == pathway_data["title"]
        ).first()
        
        if not existing and roles:
            role = roles[role_index % len(roles)]
            pathway = CareerPathway(
                career_role_id=role.id,
                title=pathway_data["title"],
                description=pathway_data["description"],
                duration_months=pathway_data["duration_months"],
                difficulty=pathway_data["difficulty"],
                popularity_score=pathway_data["popularity_score"],
                is_active=True,
            )
            db.add(pathway)
            role_index += 1
    
    db.commit()


def seed_all():
    """Seed all data"""
    db = SessionLocal()
    try:
        print("Seeding skills...")
        seed_skills(db)
        
        print("Seeding career roles...")
        seed_career_roles(db)
        
        print("Seeding career role skills...")
        seed_career_role_skills(db)
        
        print("Seeding career pathways...")
        seed_career_pathways(db)
        
        print("✅ All seed data created successfully!")
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
