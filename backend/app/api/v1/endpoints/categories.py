from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.models.user import User
from app.models.transaction import Category, CategorizationRule
from app.core.cookie_auth import get_current_user_from_cookie
from app.schemas.category import CategoryCreate, CategoryResponse, RuleCreate, RuleResponse
from app.services.enhanced_categorization import EnhancedCategorizationService

router = APIRouter()
logger = logging.getLogger(__name__)

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
    """Create a new categorization rule with validation (legacy endpoint - use /categorization-rules for advanced features)"""
    try:
        # Use enhanced service for validation
        enhanced_service = EnhancedCategorizationService(db)
        
        # Validate the rule
        validation = enhanced_service.validate_rule(
            user_id=current_user.id,
            pattern=rule_data.pattern,
            pattern_type=rule_data.pattern_type,
            category=rule_data.category,
            subcategory=rule_data.subcategory
        )
        
        if not validation.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Rule validation failed",
                    "errors": validation.errors,
                    "warnings": validation.warnings
                }
            )
        
        rule = CategorizationRule(
            user_id=current_user.id,
            pattern=rule_data.pattern,
            pattern_type=rule_data.pattern_type,
            category=rule_data.category,
            subcategory=rule_data.subcategory,
            priority=rule_data.priority,
            is_active=rule_data.is_active
        )
        
        db.add(rule)
        db.commit()
        db.refresh(rule)
        
        logger.info(f"Created categorization rule {rule.id} for user {current_user.id} via legacy endpoint")
        return rule
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating categorization rule via legacy endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create categorization rule"
        )
