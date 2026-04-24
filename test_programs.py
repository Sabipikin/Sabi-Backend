#!/usr/bin/env python3
"""Test the programs endpoint logic"""

from database import SessionLocal
from models import Program

db = SessionLocal()

try:
    # Test basic query
    programs = db.query(Program).filter(Program.status == "published").all()
    print(f"Query successful, found {len(programs)} programs")
    
    # Test building the response
    result = []
    for p in programs:
        item = {
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
            "updated_at": p.updated_at
        }
        print(f"Item: {item}")
        result.append(item)
    
    print(f"Result: {result}")
    db.close()
    print("✓ Test successful")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
