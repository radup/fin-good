from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.models.transaction import Transaction, CategorizationRule, Category
from app.schemas.category import (
    RuleTestRequest, RuleTestResponse, TransactionMatch,
    RuleValidationResult, RuleConflictInfo, PerformanceAnalytics,
    RulePerformance, BulkOperationResponse
)
from typing import List, Dict, Any, Optional, Tuple
import re
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class EnhancedCategorizationService:
    """Enhanced service for advanced categorization rule management"""
    
    def __init__(self, db: Session):
        self.db = db
        self._compiled_patterns = {}  # Cache for compiled regex patterns
    
    def validate_rule(self, user_id: int, pattern: str, pattern_type: str, 
                     category: str, subcategory: Optional[str] = None,
                     exclude_rule_id: Optional[int] = None) -> RuleValidationResult:
        """Comprehensive rule validation with conflict detection"""
        errors = []
        warnings = []
        conflicts = []
        
        # Basic validation
        if not pattern.strip():
            errors.append("Pattern cannot be empty")
        
        if not category.strip():
            errors.append("Category cannot be empty")
        
        # Pattern-specific validation
        if pattern_type == 'regex':
            try:
                re.compile(pattern)
            except re.error as e:
                errors.append(f"Invalid regex pattern: {str(e)}")
        
        # Check for existing categories
        existing_categories = self._get_user_categories(user_id)
        if category not in existing_categories:
            warnings.append(f"Category '{category}' does not exist. It will be created.")
        
        if subcategory and subcategory not in existing_categories.get(category, []):
            warnings.append(f"Subcategory '{subcategory}' does not exist in category '{category}'")
        
        # Conflict detection
        conflicts = self._detect_rule_conflicts(
            user_id, pattern, pattern_type, exclude_rule_id
        )
        
        # Estimate potential matches
        estimated_matches = self._estimate_rule_matches(user_id, pattern, pattern_type)
        
        is_valid = len(errors) == 0
        
        return RuleValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            conflicts=conflicts,
            estimated_matches=estimated_matches
        )
    
    def test_rule(self, user_id: int, test_request: RuleTestRequest) -> RuleTestResponse:
        """Test a rule against existing transactions"""
        # Get user's transactions
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        
        # Apply specific test filters if provided
        if test_request.test_description:
            query = query.filter(
                Transaction.description.ilike(f"%{test_request.test_description}%")
            )
        
        if test_request.test_vendor:
            query = query.filter(
                Transaction.vendor.ilike(f"%{test_request.test_vendor}%")
            )
        
        all_transactions = query.all()
        total_transactions = len(all_transactions)
        
        # Find matches
        matches = []
        for transaction in all_transactions:
            if self._pattern_matches(
                test_request.pattern, 
                test_request.pattern_type, 
                transaction
            ):
                matches.append(transaction)
        
        # Prepare sample matches
        sample_matches = []
        for transaction in matches[:test_request.limit]:
            match = TransactionMatch(
                id=transaction.id,
                description=transaction.description,
                vendor=transaction.vendor,
                amount=transaction.amount,
                date=transaction.date,
                current_category=transaction.category,
                current_subcategory=transaction.subcategory,
                confidence=0.95 if test_request.pattern_type == 'exact' else 0.8
            )
            sample_matches.append(match)
        
        # Check for potential conflicts
        conflicts = self._detect_rule_conflicts(
            user_id, test_request.pattern, test_request.pattern_type
        )
        
        match_rate = len(matches) / total_transactions if total_transactions > 0 else 0
        
        return RuleTestResponse(
            pattern=test_request.pattern,
            pattern_type=test_request.pattern_type,
            matches_found=len(matches),
            total_transactions=total_transactions,
            match_rate=match_rate,
            sample_matches=sample_matches,
            potential_conflicts=[conflict.dict() for conflict in conflicts]
        )
    
    def get_rule_performance_analytics(self, user_id: int) -> PerformanceAnalytics:
        """Get comprehensive rule performance analytics"""
        # Get all rules for user
        rules = self.db.query(CategorizationRule).filter(
            CategorizationRule.user_id == user_id
        ).all()
        
        # Get categorized transactions
        categorized_transactions = self.db.query(Transaction).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.is_categorized == True,
                Transaction.category.isnot(None)
            )
        ).all()
        
        rule_performances = []
        category_distribution = defaultdict(int)
        total_matches = 0
        
        for rule in rules:
            matches = self._get_rule_matches(rule, categorized_transactions)
            accuracy_rate = self._calculate_rule_accuracy(rule, matches)
            
            last_match_date = None
            if matches:
                last_match_date = max(t.updated_at or t.created_at for t in matches)
            
            effectiveness_score = self._calculate_effectiveness_score(
                rule, len(matches), accuracy_rate
            )
            
            performance = RulePerformance(
                rule_id=rule.id,
                rule_pattern=rule.pattern,
                rule_category=rule.category,
                matches_count=len(matches),
                accuracy_rate=accuracy_rate,
                last_match_date=last_match_date,
                effectiveness_score=effectiveness_score
            )
            rule_performances.append(performance)
            
            category_distribution[rule.category] += len(matches)
            total_matches += len(matches)
        
        # Sort by effectiveness
        rule_performances.sort(key=lambda x: x.effectiveness_score, reverse=True)
        
        active_rules = len([r for r in rules if r.is_active])
        inactive_rules = len(rules) - active_rules
        average_accuracy = sum(p.accuracy_rate for p in rule_performances) / len(rule_performances) if rule_performances else 0
        
        return PerformanceAnalytics(
            total_rules=len(rules),
            active_rules=active_rules,
            inactive_rules=inactive_rules,
            total_matches=total_matches,
            average_accuracy=average_accuracy,
            top_performing_rules=rule_performances[:10],
            underperforming_rules=[p for p in rule_performances if p.effectiveness_score < 0.3][-5:],
            category_distribution=dict(category_distribution)
        )
    
    def bulk_create_rules(self, user_id: int, rules_data: List[Dict[str, Any]]) -> BulkOperationResponse:
        """Bulk create categorization rules with validation"""
        successful = 0
        failed = 0
        errors = []
        created_rules = []
        
        for i, rule_data in enumerate(rules_data):
            try:
                # Validate rule
                validation = self.validate_rule(
                    user_id=user_id,
                    pattern=rule_data.get('pattern', ''),
                    pattern_type=rule_data.get('pattern_type', ''),
                    category=rule_data.get('category', ''),
                    subcategory=rule_data.get('subcategory')
                )
                
                if not validation.is_valid:
                    failed += 1
                    errors.append({
                        'index': str(i),
                        'error': '; '.join(validation.errors)
                    })
                    continue
                
                # Create rule
                rule = CategorizationRule(
                    user_id=user_id,
                    pattern=rule_data['pattern'],
                    pattern_type=rule_data['pattern_type'],
                    category=rule_data['category'],
                    subcategory=rule_data.get('subcategory'),
                    priority=rule_data.get('priority', 1),
                    is_active=rule_data.get('is_active', True)
                )
                
                self.db.add(rule)
                self.db.flush()  # Get ID without committing
                created_rules.append(rule)
                successful += 1
                
            except Exception as e:
                failed += 1
                errors.append({
                    'index': str(i),
                    'error': str(e)
                })
                logger.error(f"Error creating rule {i}: {str(e)}")
        
        if created_rules:
            self.db.commit()
            # Refresh all created rules
            for rule in created_rules:
                self.db.refresh(rule)
        
        return BulkOperationResponse(
            successful=successful,
            failed=failed,
            errors=errors,
            created_rules=created_rules
        )
    
    def detect_duplicate_rules(self, user_id: int) -> List[Dict[str, Any]]:
        """Detect duplicate or highly similar rules"""
        rules = self.db.query(CategorizationRule).filter(
            CategorizationRule.user_id == user_id,
            CategorizationRule.is_active == True
        ).all()
        
        duplicates = []
        seen_patterns = {}
        
        for rule in rules:
            pattern_key = f"{rule.pattern_type}:{rule.pattern.lower()}"
            
            if pattern_key in seen_patterns:
                original_rule = seen_patterns[pattern_key]
                duplicates.append({
                    'original_rule_id': original_rule.id,
                    'original_pattern': original_rule.pattern,
                    'duplicate_rule_id': rule.id,
                    'duplicate_pattern': rule.pattern,
                    'type': 'exact_duplicate' if rule.pattern == original_rule.pattern else 'similar',
                    'same_category': rule.category == original_rule.category
                })
            else:
                seen_patterns[pattern_key] = rule
        
        return duplicates
    
    def optimize_rule_priorities(self, user_id: int) -> Dict[str, Any]:
        """Optimize rule priorities based on effectiveness and conflicts"""
        rules = self.db.query(CategorizationRule).filter(
            CategorizationRule.user_id == user_id,
            CategorizationRule.is_active == True
        ).order_by(CategorizationRule.priority.desc()).all()
        
        # Get performance data
        analytics = self.get_rule_performance_analytics(user_id)
        performance_map = {p.rule_id: p for p in analytics.top_performing_rules}
        
        optimized_count = 0
        changes = []
        
        # Sort rules by effectiveness score
        rules_by_effectiveness = sorted(
            rules, 
            key=lambda r: performance_map.get(r.id, type('obj', (object,), {'effectiveness_score': 0})()).effectiveness_score,
            reverse=True
        )
        
        # Reassign priorities
        for i, rule in enumerate(rules_by_effectiveness):
            new_priority = len(rules_by_effectiveness) - i
            if rule.priority != new_priority:
                old_priority = rule.priority
                rule.priority = new_priority
                optimized_count += 1
                changes.append({
                    'rule_id': rule.id,
                    'pattern': rule.pattern,
                    'old_priority': old_priority,
                    'new_priority': new_priority
                })
        
        self.db.commit()
        
        return {
            'optimized_count': optimized_count,
            'changes': changes,
            'total_rules': len(rules)
        }
    
    def export_rules(self, user_id: int) -> Dict[str, Any]:
        """Export user's categorization rules"""
        rules = self.db.query(CategorizationRule).filter(
            CategorizationRule.user_id == user_id
        ).all()
        
        exported_rules = []
        for rule in rules:
            exported_rules.append({
                'pattern': rule.pattern,
                'pattern_type': rule.pattern_type,
                'category': rule.category,
                'subcategory': rule.subcategory,
                'priority': rule.priority,
                'is_active': rule.is_active,
                'created_at': rule.created_at.isoformat(),
                'updated_at': rule.updated_at.isoformat() if rule.updated_at else None
            })
        
        return {
            'rules': exported_rules,
            'export_date': datetime.now(),
            'total_rules': len(exported_rules),
            'metadata': {
                'user_id': user_id,
                'export_version': '1.0',
                'active_rules': len([r for r in rules if r.is_active]),
                'inactive_rules': len([r for r in rules if not r.is_active])
            }
        }
    
    # Private helper methods
    
    def _pattern_matches(self, pattern: str, pattern_type: str, transaction: Transaction) -> bool:
        """Check if pattern matches transaction"""
        try:
            if pattern_type == 'keyword':
                return pattern.lower() in transaction.description.lower()
            elif pattern_type == 'vendor':
                if transaction.vendor:
                    return pattern.lower() in transaction.vendor.lower()
                return False
            elif pattern_type == 'regex':
                return bool(re.search(pattern, transaction.description, re.IGNORECASE))
            elif pattern_type == 'exact':
                return pattern.lower() == transaction.description.lower()
            elif pattern_type == 'contains':
                return pattern.lower() in transaction.description.lower()
        except Exception as e:
            logger.warning(f"Pattern matching error: {str(e)}")
            return False
        
        return False
    
    def _detect_rule_conflicts(self, user_id: int, pattern: str, pattern_type: str,
                             exclude_rule_id: Optional[int] = None) -> List[RuleConflictInfo]:
        """Detect conflicts with existing rules"""
        conflicts = []
        
        query = self.db.query(CategorizationRule).filter(
            CategorizationRule.user_id == user_id,
            CategorizationRule.is_active == True
        )
        
        if exclude_rule_id:
            query = query.filter(CategorizationRule.id != exclude_rule_id)
        
        existing_rules = query.all()
        
        for rule in existing_rules:
            # Check for exact duplicates
            if rule.pattern == pattern and rule.pattern_type == pattern_type:
                conflicts.append(RuleConflictInfo(
                    conflicting_rule_id=rule.id,
                    conflicting_pattern=rule.pattern,
                    conflict_type='duplicate',
                    severity='high',
                    description=f"Exact duplicate of existing rule with pattern '{rule.pattern}'"
                ))
            
            # Check for overlapping patterns
            elif self._patterns_overlap(pattern, pattern_type, rule.pattern, rule.pattern_type):
                conflicts.append(RuleConflictInfo(
                    conflicting_rule_id=rule.id,
                    conflicting_pattern=rule.pattern,
                    conflict_type='overlap',
                    severity='medium',
                    description=f"Pattern may overlap with existing rule '{rule.pattern}'"
                ))
        
        return conflicts
    
    def _patterns_overlap(self, pattern1: str, type1: str, pattern2: str, type2: str) -> bool:
        """Check if two patterns might overlap"""
        # Simple overlap detection - can be enhanced
        if type1 == 'keyword' and type2 == 'keyword':
            return pattern1.lower() in pattern2.lower() or pattern2.lower() in pattern1.lower()
        elif type1 == 'contains' and type2 == 'contains':
            return pattern1.lower() in pattern2.lower() or pattern2.lower() in pattern1.lower()
        
        return False
    
    def _estimate_rule_matches(self, user_id: int, pattern: str, pattern_type: str) -> int:
        """Estimate how many transactions would match this rule"""
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).limit(1000).all()  # Sample for estimation
        
        matches = 0
        for transaction in transactions:
            if self._pattern_matches(pattern, pattern_type, transaction):
                matches += 1
        
        return matches
    
    def _get_user_categories(self, user_id: int) -> Dict[str, List[str]]:
        """Get user's categories and subcategories"""
        transactions = self.db.query(Transaction).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.category.isnot(None)
            )
        ).all()
        
        categories = defaultdict(set)
        
        for transaction in transactions:
            if transaction.category:
                categories[transaction.category].add(transaction.subcategory or '')
        
        return {cat: list(subcats) for cat, subcats in categories.items()}
    
    def _get_rule_matches(self, rule: CategorizationRule, transactions: List[Transaction]) -> List[Transaction]:
        """Get transactions that match a specific rule"""
        matches = []
        for transaction in transactions:
            if (transaction.category == rule.category and 
                transaction.subcategory == rule.subcategory):
                if self._pattern_matches(rule.pattern, rule.pattern_type, transaction):
                    matches.append(transaction)
        
        return matches
    
    def _calculate_rule_accuracy(self, rule: CategorizationRule, matches: List[Transaction]) -> float:
        """Calculate accuracy rate for a rule"""
        if not matches:
            return 0.0
        
        correct_matches = len([
            t for t in matches 
            if t.category == rule.category and t.subcategory == rule.subcategory
        ])
        
        return correct_matches / len(matches)
    
    def _calculate_effectiveness_score(self, rule: CategorizationRule, matches_count: int, 
                                     accuracy_rate: float) -> float:
        """Calculate overall effectiveness score for a rule"""
        # Consider both match count and accuracy
        match_score = min(matches_count / 100, 1.0)  # Normalize to 0-1
        
        # Weight accuracy more heavily than match count
        effectiveness = (accuracy_rate * 0.7) + (match_score * 0.3)
        
        # Apply priority bonus
        priority_bonus = rule.priority / 100
        effectiveness += priority_bonus * 0.1
        
        return min(effectiveness, 1.0)