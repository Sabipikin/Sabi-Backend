"""Shopping cart endpoints for courses, programs, and diplomas"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Cart, Course, Program, Diploma, User, Subscription, SubscriptionPlan, Payment
from schemas import CartResponse
from routes.auth import get_current_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/cart", tags=["cart"])


from typing import Optional

@router.post("/add", response_model=dict)
async def add_to_cart(
    item_type: str = Query(...),  # 'course', 'program', 'diploma'
    item_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Add item to cart (works for authenticated and unauthenticated users)"""
    try:
        # Validate item type
        if item_type not in ['course', 'program', 'diploma']:
            raise HTTPException(status_code=400, detail="Invalid item type")
        
        # Get the item and validate it exists
        if item_type == 'course':
            item = db.query(Course).filter(Course.id == item_id, Course.status == "published").first()
            if not item:
                raise HTTPException(status_code=404, detail="Course not found")
            price = item.fee
            discount = item.promo_amount if item.is_on_promo else 0
        elif item_type == 'program':
            item = db.query(Program).filter(Program.id == item_id, Program.status == "published").first()
            if not item:
                raise HTTPException(status_code=404, detail="Program not found")
            price = item.fee
            discount = item.promo_amount if item.is_on_promo else 0
        elif item_type == 'diploma':
            item = db.query(Diploma).filter(Diploma.id == item_id, Diploma.status == "published").first()
            if not item:
                raise HTTPException(status_code=404, detail="Diploma not found")
            price = item.fee
            discount = item.promo_amount if item.is_on_promo else 0
        
        # Check if already in cart
        existing_cart_item = db.query(Cart).filter(
            Cart.item_type == item_type,
            ((Cart.course_id == item_id and item_type == 'course') or
             (Cart.program_id == item_id and item_type == 'program') or
             (Cart.diploma_id == item_id and item_type == 'diploma'))
        )
        
        if current_user:
            existing_cart_item = existing_cart_item.filter(Cart.user_id == current_user.id).first()
        else:
            session_id = None  # Could be extracted from request if needed
            existing_cart_item = existing_cart_item.filter(Cart.user_id.is_(None)).first()
        
        if existing_cart_item:
            existing_cart_item.quantity += 1
            db.commit()
            return {
                "success": True,
                "message": "Item quantity increased in cart",
                "cart_item_id": existing_cart_item.id
            }
        
        # Create new cart item
        kwargs = {
            "item_type": item_type,
            "price": price,
            "discount": discount,
            "quantity": 1
        }
        
        if current_user:
            kwargs["user_id"] = current_user.id
        
        if item_type == 'course':
            kwargs["course_id"] = item_id
        elif item_type == 'program':
            kwargs["program_id"] = item_id
        elif item_type == 'diploma':
            kwargs["diploma_id"] = item_id
        
        cart_item = Cart(**kwargs)
        db.add(cart_item)
        db.commit()
        db.refresh(cart_item)
        
        return {
            "success": True,
            "message": f"{item.title} added to cart",
            "cart_item_id": cart_item.id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding to cart: {str(e)}")


@router.get("/", response_model=list[CartResponse])
async def get_cart(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Get cart items (for authenticated user or session)"""
    try:
        if current_user:
            cart_items = db.query(Cart).filter(Cart.user_id == current_user.id).all()
        else:
            # For unauthenticated users, return empty for now (would use session_id in real app)
            cart_items = []
        
        return cart_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cart: {str(e)}")


@router.delete("/{cart_item_id}")
async def remove_from_cart(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Remove item from cart"""
    try:
        cart_item = db.query(Cart).filter(Cart.id == cart_item_id).first()
        
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")
        
        # Verify ownership
        if current_user and cart_item.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        db.delete(cart_item)
        db.commit()
        
        return {"message": "Item removed from cart"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error removing from cart: {str(e)}")


@router.post("/checkout")
async def checkout(
    checkout_data: dict,  # {subscribe: bool, plan_id: int (optional)}
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Process checkout - either subscribe or create individual enrollments"""
    try:
        user_id = current_user.id
        
        # Get cart items
        cart_items = db.query(Cart).filter(Cart.user_id == user_id).all()
        
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        # Calculate total
        total_amount = sum((item.price - item.discount) * item.quantity for item in cart_items)
        
        # If subscribing
        if checkout_data.get("subscribe"):
            plan_id = checkout_data.get("plan_id")
            if not plan_id:
                raise HTTPException(status_code=400, detail="Plan ID required for subscription")
            
            plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
            if not plan:
                raise HTTPException(status_code=404, detail="Subscription plan not found")
            
            # Create payment
            payment = Payment(
                user_id=user_id,
                amount=plan.price,
                currency="gbp",
                status="pending",
                payment_method="payoneer",
                item_type="subscription",
                description=f"Subscription: {plan.name}"
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)
            
            # TODO: Integrate with Payoneer to get checkout URL
            
            return {
                "success": True,
                "type": "subscription",
                "payment_id": payment.id,
                "amount": plan.price,
                "plan_name": plan.name
            }
        else:
            # Pay per course/program/diploma
            payment = Payment(
                user_id=user_id,
                amount=total_amount,
                currency="gbp",
                status="pending",
                payment_method="payoneer",
                description=f"Purchase of {len(cart_items)} item(s)"
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)
            
            # TODO: Integrate with Payoneer to get checkout URL
            
            return {
                "success": True,
                "type": "pay_per_item",
                "payment_id": payment.id,
                "amount": total_amount,
                "items_count": len(cart_items)
            }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error during checkout: {str(e)}")
