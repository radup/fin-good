from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.user import User
from app.models.transaction import Category, CategorizationRule
from app.core.cookie_auth import get_current_user_from_cookie
from app.schemas.category import CategoryCreate, CategoryResponse, RuleCreate, RuleResponse

router = APIRouter()

@router.get("/", response_model=List[CategoryResponse])
async def get_categories(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get user's categories"""
    categories = db.query(Category).filter(Category.user_id == current_user.id).all()
    return categories

@router.post("/", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Create a new category"""
    category = Category(
        user_id=current_user.id,
        name=category_data.name,
        parent_category=category_data.parent_category,
        color=category_data.color
    )
    
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return category

@router.get("/rules", response_model=List[RuleResponse])
async def get_categorization_rules(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get user's categorization rules"""
    rules = db.query(CategorizationRule).filter(
        CategorizationRule.user_id == current_user.id
    ).all()
    return rules

@router.post("/rules", response_model=RuleResponse)
async def create_categorization_rule(
    rule_data: RuleCreate,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Create a new categorization rule"""
    rule = CategorizationRule(
        user_id=current_user.id,
        pattern=rule_data.pattern,
        pattern_type=rule_data.pattern_type,
        category=rule_data.category,
        subcategory=rule_data.subcategory,
        priority=rule_data.priority
    )
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return rule
