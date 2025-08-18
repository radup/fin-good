from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
import logging

from app.core.database import get_db
from app.models.user import User
from app.models.transaction import CategorizationRule, Transaction
from app.core.cookie_auth import get_current_user_from_cookie
from app.services.enhanced_categorization import EnhancedCategorizationService
from app.services.categorization import CategorizationService
from app.schemas.category import (
    RuleCreate, RuleUpdate, RuleResponse, RuleListResponse,
    RuleTestRequest, RuleTestResponse, BulkRuleCreate, BulkOperationResponse,
    PerformanceAnalytics, RuleValidationResult, RuleExportResponse,
    RuleImportRequest, RuleImportResponse, RuleTemplateResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=RuleListResponse)
async def get_categorization_rules(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of rules per page"),
    active_only: bool = Query(True, description="Show only active rules"),
    category: Optional[str] = Query(None, description="Filter by category"),
    pattern_type: Optional[str] = Query(None, description="Filter by pattern type"),
    search: Optional[str] = Query(None, description="Search in pattern or category"),
    sort_by: str = Query("priority", description="Sort by: priority, created_at, category, pattern"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get user's categorization rules with pagination and filtering"""
    try:
        # Base query
        query = db.query(CategorizationRule).filter(
            CategorizationRule.user_id == current_user.id
        )
        
        # Apply filters
        if active_only:
            query = query.filter(CategorizationRule.is_active == True)
        
        if category:
            query = query.filter(CategorizationRule.category.ilike(f"%{category}%"))
        
        if pattern_type:
            query = query.filter(CategorizationRule.pattern_type == pattern_type)
        
        if search:
            query = query.filter(
                or_(
                    CategorizationRule.pattern.ilike(f"%{search}%"),
                    CategorizationRule.category.ilike(f"%{search}%")
                )
            )
        
        # Apply sorting
        sort_column = getattr(CategorizationRule, sort_by, CategorizationRule.priority)
        if sort_desc:
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        rules = query.offset(offset).limit(page_size).all()
        
        has_next = offset + page_size < total
        has_prev = page > 1
        
        return RuleListResponse(
            rules=rules,
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        logger.error(f"Error fetching categorization rules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch categorization rules"
        )


@router.post("/", response_model=RuleResponse)
async def create_categorization_rule(
    rule_data: RuleCreate,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Create a new categorization rule with validation"""
    try:
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
        
        # Create the rule
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
        
        logger.info(f"Created categorization rule {rule.id} for user {current_user.id}")
        return rule
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating categorization rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create categorization rule"
        )


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_categorization_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get a specific categorization rule"""
    rule = db.query(CategorizationRule).filter(
        and_(
            CategorizationRule.id == rule_id,
            CategorizationRule.user_id == current_user.id
        )
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categorization rule not found"
        )
    
    return rule


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_categorization_rule(
    rule_id: int,
    rule_update: RuleUpdate,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Update a categorization rule"""
    try:
        # Get the existing rule
        rule = db.query(CategorizationRule).filter(
            and_(
                CategorizationRule.id == rule_id,
                CategorizationRule.user_id == current_user.id
            )
        ).first()
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categorization rule not found"
            )
        
        # Validate the updates if pattern or pattern_type is changing
        if rule_update.pattern or rule_update.pattern_type:
            enhanced_service = EnhancedCategorizationService(db)
            validation = enhanced_service.validate_rule(
                user_id=current_user.id,
                pattern=rule_update.pattern or rule.pattern,
                pattern_type=rule_update.pattern_type or rule.pattern_type,
                category=rule_update.category or rule.category,
                subcategory=rule_update.subcategory if rule_update.subcategory is not None else rule.subcategory,
                exclude_rule_id=rule_id
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
        
        # Update the rule
        update_data = rule_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rule, field, value)
        
        db.commit()
        db.refresh(rule)
        
        logger.info(f"Updated categorization rule {rule.id} for user {current_user.id}")
        return rule
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating categorization rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update categorization rule"
        )


@router.delete("/{rule_id}")
async def delete_categorization_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Delete a categorization rule"""
    try:
        rule = db.query(CategorizationRule).filter(
            and_(
                CategorizationRule.id == rule_id,
                CategorizationRule.user_id == current_user.id
            )
        ).first()
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categorization rule not found"
            )
        
        db.delete(rule)
        db.commit()
        
        logger.info(f"Deleted categorization rule {rule_id} for user {current_user.id}")
        return {"message": "Rule deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting categorization rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete categorization rule"
        )


@router.post("/test", response_model=RuleTestResponse)
async def test_categorization_rule(
    test_request: RuleTestRequest,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Test a rule against existing transactions"""
    try:
        enhanced_service = EnhancedCategorizationService(db)
        result = enhanced_service.test_rule(current_user.id, test_request)
        return result
        
    except Exception as e:
        logger.error(f"Error testing categorization rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test categorization rule"
        )


@router.post("/validate", response_model=RuleValidationResult)
async def validate_categorization_rule(
    pattern: str,
    pattern_type: str,
    category: str,
    subcategory: Optional[str] = None,
    rule_id: Optional[int] = None,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Validate a categorization rule before creation/update"""
    try:
        enhanced_service = EnhancedCategorizationService(db)
        result = enhanced_service.validate_rule(
            user_id=current_user.id,
            pattern=pattern,
            pattern_type=pattern_type,
            category=category,
            subcategory=subcategory,
            exclude_rule_id=rule_id
        )
        return result
        
    except Exception as e:
        logger.error(f"Error validating categorization rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate categorization rule"
        )


@router.post("/bulk", response_model=BulkOperationResponse)
async def bulk_create_rules(
    bulk_request: BulkRuleCreate,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Bulk create categorization rules"""
    try:
        enhanced_service = EnhancedCategorizationService(db)
        rules_data = [rule.dict() for rule in bulk_request.rules]
        result = enhanced_service.bulk_create_rules(current_user.id, rules_data)
        
        logger.info(f"Bulk created {result.successful} rules for user {current_user.id}")
        return result
        
    except Exception as e:
        logger.error(f"Error bulk creating rules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk create rules"
        )


@router.get("/performance/analytics", response_model=PerformanceAnalytics)
async def get_rule_performance_analytics(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get rule performance analytics"""
    try:
        enhanced_service = EnhancedCategorizationService(db)
        analytics = enhanced_service.get_rule_performance_analytics(current_user.id)
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting rule performance analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get rule performance analytics"
        )


@router.get("/duplicates", response_model=List[Dict[str, Any]])
async def detect_duplicate_rules(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Detect duplicate or similar rules"""
    try:
        enhanced_service = EnhancedCategorizationService(db)
        duplicates = enhanced_service.detect_duplicate_rules(current_user.id)
        return duplicates
        
    except Exception as e:
        logger.error(f"Error detecting duplicate rules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to detect duplicate rules"
        )


@router.post("/optimize-priorities")
async def optimize_rule_priorities(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Optimize rule priorities based on effectiveness"""
    try:
        enhanced_service = EnhancedCategorizationService(db)
        result = enhanced_service.optimize_rule_priorities(current_user.id)
        
        logger.info(f"Optimized {result['optimized_count']} rules for user {current_user.id}")
        return result
        
    except Exception as e:
        logger.error(f"Error optimizing rule priorities: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize rule priorities"
        )


@router.get("/export", response_model=RuleExportResponse)
async def export_rules(
    format: str = Query("json", description="Export format: json, csv"),
    active_only: bool = Query(False, description="Export only active rules"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Export user's categorization rules"""
    try:
        enhanced_service = EnhancedCategorizationService(db)
        export_data = enhanced_service.export_rules(current_user.id)
        
        if active_only:
            export_data['rules'] = [
                rule for rule in export_data['rules'] 
                if rule.get('is_active', True)
            ]
            export_data['total_rules'] = len(export_data['rules'])
        
        logger.info(f"Exported {export_data['total_rules']} rules for user {current_user.id}")
        return RuleExportResponse(**export_data)
        
    except Exception as e:
        logger.error(f"Error exporting rules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export rules"
        )


@router.post("/import", response_model=RuleImportResponse)
async def import_rules(
    import_request: RuleImportRequest,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Import categorization rules"""
    try:
        enhanced_service = EnhancedCategorizationService(db)
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        validation_results = []
        imported_rules = []
        
        for rule_data in import_request.rules:
            try:
                # Validate rule
                validation = enhanced_service.validate_rule(
                    user_id=current_user.id,
                    pattern=rule_data.get('pattern', ''),
                    pattern_type=rule_data.get('pattern_type', ''),
                    category=rule_data.get('category', ''),
                    subcategory=rule_data.get('subcategory')
                )
                validation_results.append(validation)
                
                if not validation.is_valid:
                    error_count += 1
                    continue
                
                if import_request.validate_only:
                    continue
                
                # Check if rule already exists
                existing_rule = db.query(CategorizationRule).filter(
                    and_(
                        CategorizationRule.user_id == current_user.id,
                        CategorizationRule.pattern == rule_data['pattern'],
                        CategorizationRule.pattern_type == rule_data['pattern_type']
                    )
                ).first()
                
                if existing_rule and not import_request.overwrite_existing:
                    skipped_count += 1
                    continue
                
                if existing_rule and import_request.overwrite_existing:
                    # Update existing rule
                    for field, value in rule_data.items():
                        if hasattr(existing_rule, field) and field != 'id':
                            setattr(existing_rule, field, value)
                    imported_rules.append(existing_rule)
                else:
                    # Create new rule
                    rule = CategorizationRule(
                        user_id=current_user.id,
                        pattern=rule_data['pattern'],
                        pattern_type=rule_data['pattern_type'],
                        category=rule_data['category'],
                        subcategory=rule_data.get('subcategory'),
                        priority=rule_data.get('priority', 1),
                        is_active=rule_data.get('is_active', True)
                    )
                    db.add(rule)
                    imported_rules.append(rule)
                
                imported_count += 1
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error importing rule: {str(e)}")
        
        if not import_request.validate_only:
            db.commit()
            # Refresh all imported rules
            for rule in imported_rules:
                db.refresh(rule)
        
        result = RuleImportResponse(
            imported_count=imported_count,
            skipped_count=skipped_count,
            error_count=error_count,
            validation_results=validation_results,
            imported_rules=imported_rules if not import_request.validate_only else []
        )
        
        logger.info(f"Imported {imported_count} rules for user {current_user.id}")
        return result
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error importing rules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import rules"
        )


@router.get("/templates", response_model=RuleTemplateResponse)
async def get_rule_templates(
    category: Optional[str] = Query(None, description="Filter templates by category"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get predefined rule templates"""
    try:
        # Define common rule templates
        templates = [
            {
                "name": "Restaurant & Dining",
                "description": "Common patterns for restaurant and dining expenses",
                "category": "Meals & Entertainment",
                "rules": [
                    {"pattern": "restaurant", "pattern_type": "keyword", "category": "Meals & Entertainment", "subcategory": "Restaurants", "priority": 5},
                    {"pattern": "mcdonald|burger|pizza|subway|starbucks", "pattern_type": "regex", "category": "Meals & Entertainment", "subcategory": "Fast Food", "priority": 6},
                    {"pattern": "bar|pub|brewery", "pattern_type": "regex", "category": "Meals & Entertainment", "subcategory": "Bars", "priority": 5}
                ],
                "tags": ["food", "dining", "entertainment"]
            },
            {
                "name": "Transportation",
                "description": "Common patterns for transportation expenses",
                "category": "Transportation",
                "rules": [
                    {"pattern": "uber|lyft|taxi", "pattern_type": "regex", "category": "Transportation", "subcategory": "Rideshare", "priority": 7},
                    {"pattern": "gas|fuel|gasoline", "pattern_type": "regex", "category": "Transportation", "subcategory": "Fuel", "priority": 6},
                    {"pattern": "parking", "pattern_type": "keyword", "category": "Transportation", "subcategory": "Parking", "priority": 5}
                ],
                "tags": ["transportation", "travel", "commute"]
            },
            {
                "name": "Office Supplies",
                "description": "Common patterns for office and business supplies",
                "category": "Office Expenses",
                "rules": [
                    {"pattern": "staples|office depot|amazon.*office", "pattern_type": "regex", "category": "Office Expenses", "subcategory": "Supplies", "priority": 6},
                    {"pattern": "paper|printer|ink|toner", "pattern_type": "regex", "category": "Office Expenses", "subcategory": "Supplies", "priority": 5},
                    {"pattern": "software|subscription", "pattern_type": "regex", "category": "Office Expenses", "subcategory": "Software", "priority": 5}
                ],
                "tags": ["office", "supplies", "business"]
            },
            {
                "name": "Utilities",
                "description": "Common patterns for utility expenses",
                "category": "Utilities",
                "rules": [
                    {"pattern": "electric|electricity|power", "pattern_type": "regex", "category": "Utilities", "subcategory": "Electric", "priority": 7},
                    {"pattern": "gas company|natural gas", "pattern_type": "regex", "category": "Utilities", "subcategory": "Gas", "priority": 7},
                    {"pattern": "water|sewer", "pattern_type": "regex", "category": "Utilities", "subcategory": "Water", "priority": 6},
                    {"pattern": "internet|phone|telecom", "pattern_type": "regex", "category": "Utilities", "subcategory": "Communications", "priority": 6}
                ],
                "tags": ["utilities", "bills", "recurring"]
            }
        ]
        
        # Filter by category if specified
        if category:
            templates = [t for t in templates if category.lower() in t["category"].lower()]
        
        # Get all categories from templates
        categories = list(set(t["category"] for t in templates))
        
        return RuleTemplateResponse(
            templates=templates,
            categories=categories
        )
        
    except Exception as e:
        logger.error(f"Error getting rule templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get rule templates"
        )


@router.post("/apply-template")
async def apply_rule_template(
    template_name: str,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Apply a rule template to user's account"""
    try:
        # Get templates (reuse the template definition from above)
        templates_response = await get_rule_templates(None, current_user, db)
        templates = templates_response.templates
        
        # Find the requested template
        template = next((t for t in templates if t["name"] == template_name), None)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Apply the template rules
        enhanced_service = EnhancedCategorizationService(db)
        rules_data = [rule for rule in template["rules"]]
        result = enhanced_service.bulk_create_rules(current_user.id, rules_data)
        
        logger.info(f"Applied template '{template_name}' for user {current_user.id}")
        return {
            "message": f"Template '{template_name}' applied successfully",
            "created_rules": result.successful,
            "failed_rules": result.failed,
            "errors": result.errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying rule template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply rule template"
        )


@router.post("/{rule_id}/apply")
async def apply_rule_to_transactions(
    rule_id: int,
    background_tasks: BackgroundTasks,
    force_recategorize: bool = Query(False, description="Force recategorization of already categorized transactions"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Apply a specific rule to user's transactions"""
    try:
        # Get the rule
        rule = db.query(CategorizationRule).filter(
            and_(
                CategorizationRule.id == rule_id,
                CategorizationRule.user_id == current_user.id,
                CategorizationRule.is_active == True
            )
        ).first()
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active categorization rule not found"
            )
        
        # Apply the rule to transactions
        def apply_rule_task():
            categorization_service = CategorizationService(db)
            
            # Get transactions to categorize
            query = db.query(Transaction).filter(
                Transaction.user_id == current_user.id
            )
            
            if not force_recategorize:
                query = query.filter(Transaction.is_categorized == False)
            
            transactions = query.all()
            categorized_count = 0
            
            enhanced_service = EnhancedCategorizationService(db)
            
            for transaction in transactions:
                if enhanced_service._pattern_matches(rule.pattern, rule.pattern_type, transaction):
                    transaction.category = rule.category
                    transaction.subcategory = rule.subcategory
                    transaction.is_categorized = True
                    transaction.confidence_score = 0.9
                    categorized_count += 1
            
            db.commit()
            logger.info(f"Applied rule {rule_id} to {categorized_count} transactions for user {current_user.id}")
        
        # Run in background
        background_tasks.add_task(apply_rule_task)
        
        return {
            "message": f"Rule '{rule.pattern}' is being applied to transactions",
            "rule_id": rule_id,
            "pattern": rule.pattern,
            "category": rule.category
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying rule to transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply rule to transactions"
        )