from sqlalchemy.orm import Session
from app.models.transaction import Transaction, CategorizationRule
from app.services.ml_categorization import MLCategorizationService, MLCategoryPrediction
from app.core.audit_logger import security_audit_logger
import re
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class CategorizationService:
    def __init__(self, db: Session):
        self.db = db
        self.ml_service = MLCategorizationService(db)
    
    async def categorize_user_transactions(self, user_id: int, batch_id: str = None, use_ml_fallback: bool = True) -> Dict[str, Any]:
        """Categorize all uncategorized transactions for a user with ML fallback"""
        query = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_categorized == False
        )
        
        if batch_id:
            query = query.filter(Transaction.import_batch == batch_id)
        
        transactions = query.all()
        rule_categorized = 0
        ml_categorized = 0
        failed_categorizations = []
        
        # First pass: Rule-based categorization
        for transaction in transactions:
            if await self._categorize_transaction(transaction):
                rule_categorized += 1
        
        # Second pass: ML fallback for uncategorized transactions
        if use_ml_fallback:
            uncategorized_transactions = [tx for tx in transactions if not tx.is_categorized]
            
            if uncategorized_transactions:
                logger.info(f"Applying ML categorization to {len(uncategorized_transactions)} transactions")
                
                try:
                    # Use batch ML categorization for efficiency
                    ml_predictions = await self.ml_service.categorize_batch(uncategorized_transactions)
                    
                    for transaction in uncategorized_transactions:
                        prediction = ml_predictions.get(transaction.id)
                        if prediction and prediction.confidence >= 0.6:  # Minimum confidence threshold
                            transaction.category = prediction.category
                            transaction.subcategory = prediction.subcategory
                            transaction.is_categorized = True
                            transaction.confidence_score = prediction.confidence
                            
                            # Store ML reasoning in metadata
                            if not transaction.meta_data:
                                transaction.meta_data = {}
                            transaction.meta_data.update({
                                'ml_reasoning': prediction.reasoning,
                                'ml_alternatives': prediction.alternatives,
                                'categorization_method': 'ml'
                            })
                            
                            ml_categorized += 1
                        else:
                            failed_categorizations.append({
                                'transaction_id': transaction.id,
                                'description': transaction.description[:100],
                                'reason': 'Low ML confidence' if prediction else 'No ML prediction'
                            })
                
                except Exception as e:
                    logger.error(f"ML categorization failed: {str(e)}")
                    failed_categorizations.extend([
                        {'transaction_id': tx.id, 'reason': f'ML error: {str(e)}'} 
                        for tx in uncategorized_transactions
                    ])
        
        self.db.commit()
        
        return {
            'total_transactions': len(transactions),
            'rule_categorized': rule_categorized,
            'ml_categorized': ml_categorized,
            'failed_categorizations': len(failed_categorizations),
            'success_rate': (rule_categorized + ml_categorized) / len(transactions) if transactions else 0,
            'failed_details': failed_categorizations[:10]  # Limit details for performance
        }
    
    async def _categorize_transaction(self, transaction: Transaction) -> bool:
        """Apply categorization rules to a single transaction"""
        rules = self.db.query(CategorizationRule).filter(
            CategorizationRule.user_id == transaction.user_id,
            CategorizationRule.is_active == True
        ).order_by(CategorizationRule.priority.desc()).all()
        
        for rule in rules:
            if self._rule_matches(rule, transaction):
                transaction.category = rule.category
                transaction.subcategory = rule.subcategory
                transaction.is_categorized = True
                transaction.confidence_score = 0.9  # High confidence for rule-based
                return True
        
        return False
    
    def _rule_matches(self, rule: CategorizationRule, transaction: Transaction) -> bool:
        """Check if a rule matches a transaction"""
        if rule.pattern_type == 'keyword':
            return rule.pattern.lower() in transaction.description.lower()
        elif rule.pattern_type == 'vendor':
            if transaction.vendor:
                return rule.pattern.lower() in transaction.vendor.lower()
        elif rule.pattern_type == 'regex':
            try:
                return bool(re.search(rule.pattern, transaction.description, re.IGNORECASE))
            except re.error:
                logger.warning(f"Invalid regex pattern: {rule.pattern}")
                return False
        
        return False
    
    async def categorize_single_transaction(self, transaction: Transaction, use_ml_fallback: bool = True) -> Dict[str, Any]:
        """Categorize a single transaction with ML fallback for real-time processing"""
        result = {
            'categorized': False,
            'method': None,
            'confidence': 0.0,
            'category': None,
            'subcategory': None,
            'reasoning': None,
            'alternatives': []
        }
        
        # First try rule-based categorization
        if await self._categorize_transaction(transaction):
            result.update({
                'categorized': True,
                'method': 'rule_based',
                'confidence': transaction.confidence_score or 0.9,
                'category': transaction.category,
                'subcategory': transaction.subcategory
            })
            return result
        
        # Fallback to ML categorization
        if use_ml_fallback:
            try:
                prediction = await self.ml_service.categorize_transaction(transaction)
                
                if prediction and prediction.confidence >= 0.6:
                    transaction.category = prediction.category
                    transaction.subcategory = prediction.subcategory
                    transaction.is_categorized = True
                    transaction.confidence_score = prediction.confidence
                    
                    # Store ML reasoning in metadata
                    if not transaction.meta_data:
                        transaction.meta_data = {}
                    transaction.meta_data.update({
                        'ml_reasoning': prediction.reasoning,
                        'ml_alternatives': prediction.alternatives,
                        'categorization_method': 'ml'
                    })
                    
                    result.update({
                        'categorized': True,
                        'method': 'ml',
                        'confidence': prediction.confidence,
                        'category': prediction.category,
                        'subcategory': prediction.subcategory,
                        'reasoning': prediction.reasoning,
                        'alternatives': prediction.alternatives
                    })
                    
                    self.db.commit()
                    return result
                    
            except Exception as e:
                logger.error(f"ML categorization failed for transaction {transaction.id}: {str(e)}")
                result['error'] = str(e)
        
        return result
    
    async def create_rule_from_correction(self, user_id: int, transaction_id: int, 
                                        category: str, subcategory: str = None) -> CategorizationRule:
        """Create a new rule from user correction"""
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        ).first()
        
        if not transaction:
            raise ValueError("Transaction not found")
        
        # Create rule based on vendor name
        pattern = transaction.vendor or transaction.description.split()[0]
        pattern_type = 'vendor' if transaction.vendor else 'keyword'
        
        rule = CategorizationRule(
            user_id=user_id,
            pattern=pattern,
            pattern_type=pattern_type,
            category=category,
            subcategory=subcategory,
            priority=1
        )
        
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        
        return rule
    
    def get_available_categories(self, user_id: int) -> dict:
        """Get all available categories and subcategories for a user"""
        # Get categories from existing transactions
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.category.isnot(None)
        ).all()
        
        # Get categories from categorization rules
        rules = self.db.query(CategorizationRule).filter(
            CategorizationRule.user_id == user_id,
            CategorizationRule.is_active == True
        ).all()
        
        categories = {}
        
        # Add categories from transactions
        for transaction in transactions:
            if transaction.category:
                if transaction.category not in categories:
                    categories[transaction.category] = set()
                if transaction.subcategory:
                    categories[transaction.category].add(transaction.subcategory)
        
        # Add categories from rules
        for rule in rules:
            if rule.category not in categories:
                categories[rule.category] = set()
            if rule.subcategory:
                categories[rule.category].add(rule.subcategory)
        
        # Convert sets to lists for JSON serialization
        return {
            category: list(subcategories) 
            for category, subcategories in categories.items()
        }
    
    async def update_transaction_category(self, user_id: int, transaction_id: int, 
                                        category: str, subcategory: str = None) -> dict:
        """Update transaction category and auto-categorize similar transactions with ML feedback"""
        # Update the specific transaction
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        ).first()
        
        if not transaction:
            raise ValueError("Transaction not found")
        
        # Track ML prediction accuracy if this is a correction
        was_ml_categorized = (
            transaction.meta_data and 
            transaction.meta_data.get('categorization_method') == 'ml'
        )
        
        is_correction = (
            transaction.is_categorized and 
            (transaction.category != category or transaction.subcategory != subcategory)
        )
        
        if was_ml_categorized and is_correction:
            # This is a correction to ML categorization - track as incorrect prediction
            await self.ml_service.track_prediction_accuracy(transaction_id, user_correction=True)
            logger.info(f"ML prediction corrected for transaction {transaction_id}: "
                       f"{transaction.category} -> {category}")
        elif was_ml_categorized and not is_correction:
            # User confirmed ML categorization - track as correct prediction
            await self.ml_service.track_prediction_accuracy(transaction_id, user_correction=False)
        
        # Update transaction
        original_category = transaction.category
        transaction.category = category
        transaction.subcategory = subcategory
        transaction.is_categorized = True
        transaction.confidence_score = 1.0  # Manual categorization has highest confidence
        
        # Update metadata to reflect manual categorization
        if not transaction.meta_data:
            transaction.meta_data = {}
        
        transaction.meta_data.update({
            'categorization_method': 'manual',
            'manual_correction': is_correction,
            'original_ml_category': original_category if was_ml_categorized else None,
            'corrected_at': transaction.updated_at.isoformat() if transaction.updated_at else None
        })
        
        # Create or update categorization rule
        await self._create_or_update_rule(user_id, transaction, category, subcategory)
        
        # Auto-categorize similar transactions
        auto_categorized_count = await self._auto_categorize_similar_transactions(
            user_id, transaction, category, subcategory
        )
        
        self.db.commit()
        
        return {
            "transaction_updated": True,
            "auto_categorized_count": auto_categorized_count,
            "new_rule_created": True,
            "was_ml_correction": is_correction and was_ml_categorized,
            "original_category": original_category
        }
    
    async def _create_or_update_rule(self, user_id: int, transaction: Transaction, 
                                   category: str, subcategory: str = None):
        """Create or update categorization rule based on transaction"""
        # Check if rule already exists
        existing_rule = self.db.query(CategorizationRule).filter(
            CategorizationRule.user_id == user_id,
            CategorizationRule.pattern == (transaction.vendor or transaction.description.split()[0]),
            CategorizationRule.pattern_type == ('vendor' if transaction.vendor else 'keyword')
        ).first()
        
        if existing_rule:
            # Update existing rule
            existing_rule.category = category
            existing_rule.subcategory = subcategory
            existing_rule.priority = 10  # High priority for user-created rules
        else:
            # Create new rule
            pattern = transaction.vendor or transaction.description.split()[0]
            pattern_type = 'vendor' if transaction.vendor else 'keyword'
            
            rule = CategorizationRule(
                user_id=user_id,
                pattern=pattern,
                pattern_type=pattern_type,
                category=category,
                subcategory=subcategory,
                priority=10  # High priority for user-created rules
            )
            self.db.add(rule)
    
    async def _auto_categorize_similar_transactions(self, user_id: int, reference_transaction: Transaction,
                                                  category: str, subcategory: str = None) -> int:
        """Auto-categorize transactions similar to the reference transaction"""
        # Find uncategorized transactions with similar patterns
        uncategorized_transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_categorized == False
        ).all()
        
        categorized_count = 0
        
        for transaction in uncategorized_transactions:
            if self._is_similar_to_reference(transaction, reference_transaction):
                transaction.category = category
                transaction.subcategory = subcategory
                transaction.is_categorized = True
                transaction.confidence_score = 0.8  # High confidence for auto-categorization
                categorized_count += 1
        
        return categorized_count
    
    def _is_similar_to_reference(self, transaction: Transaction, reference: Transaction) -> bool:
        """Check if transaction is similar to reference transaction"""
        # Check vendor similarity
        if reference.vendor and transaction.vendor:
            if reference.vendor.lower() == transaction.vendor.lower():
                return True
        
        # Check description similarity (first few words)
        ref_words = reference.description.lower().split()[:3]
        trans_words = transaction.description.lower().split()[:3]
        
        # If at least 2 words match, consider them similar
        common_words = set(ref_words) & set(trans_words)
        if len(common_words) >= 2:
            return True
        
        # Check if description contains the same key terms
        ref_key_terms = [word for word in ref_words if len(word) > 3]
        trans_key_terms = [word for word in trans_words if len(word) > 3]
        
        common_key_terms = set(ref_key_terms) & set(trans_key_terms)
        if len(common_key_terms) >= 1:
            return True
        
        return False
    
    async def apply_rule_to_existing_transactions(self, rule_id: int, force_recategorize: bool = False) -> dict:
        """Apply a specific rule to existing transactions"""
        rule = self.db.query(CategorizationRule).filter(
            CategorizationRule.id == rule_id,
            CategorizationRule.is_active == True
        ).first()
        
        if not rule:
            raise ValueError("Active rule not found")
        
        # Get transactions to categorize
        query = self.db.query(Transaction).filter(
            Transaction.user_id == rule.user_id
        )
        
        if not force_recategorize:
            query = query.filter(Transaction.is_categorized == False)
        
        transactions = query.all()
        categorized_count = 0
        
        for transaction in transactions:
            if self._rule_matches(rule, transaction):
                transaction.category = rule.category
                transaction.subcategory = rule.subcategory
                transaction.is_categorized = True
                transaction.confidence_score = 0.9  # High confidence for rule-based
                categorized_count += 1
        
        self.db.commit()
        
        return {
            "rule_id": rule_id,
            "pattern": rule.pattern,
            "categorized_count": categorized_count,
            "total_processed": len(transactions)
        }
    
    async def get_ml_performance_metrics(self) -> Dict[str, Any]:
        """Get ML categorization performance metrics"""
        return self.ml_service.get_performance_metrics()
    
    async def get_ml_health_status(self) -> Dict[str, Any]:
        """Get ML service health status"""
        return await self.ml_service.health_check()
    
    async def generate_training_data(self, user_id: int) -> List[Dict[str, Any]]:
        """Generate training data from user's categorized transactions"""
        return await self.ml_service.generate_training_data(user_id)
    
    async def suggest_categories_for_transaction(self, transaction: Transaction) -> Dict[str, Any]:
        """Get category suggestions for a transaction"""
        suggestions = []
        
        # Get rule-based suggestions
        rules = self.db.query(CategorizationRule).filter(
            CategorizationRule.user_id == transaction.user_id,
            CategorizationRule.is_active == True
        ).all()
        
        for rule in rules:
            if self._rule_matches(rule, transaction):
                suggestions.append({
                    'category': rule.category,
                    'subcategory': rule.subcategory,
                    'confidence': 0.9,  # High confidence for rule matches
                    'method': 'rule',
                    'rule_id': rule.id,
                    'rule_name': rule.name
                })
        
        # Get ML-based suggestions
        try:
            ml_prediction = await self.ml_service.categorize_single(transaction)
            if ml_prediction and ml_prediction.confidence >= 0.3:  # Lower threshold for suggestions
                suggestions.append({
                    'category': ml_prediction.category,
                    'subcategory': ml_prediction.subcategory,
                    'confidence': ml_prediction.confidence,
                    'method': 'ml',
                    'reasoning': ml_prediction.reasoning,
                    'alternatives': ml_prediction.alternatives
                })
        except Exception as e:
            logger.warning(f"ML suggestion failed for transaction {transaction.id}: {e}")
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'suggestions': suggestions[:5],  # Top 5 suggestions
            'total_suggestions': len(suggestions)
        }

    async def categorize_transactions_by_ids(self, user_id: int, transaction_ids: List[int], use_ml_fallback: bool = True) -> Dict[str, Any]:
        """Categorize specific transactions by their IDs"""
        import time
        start_time = time.time()
        
        transactions = self.db.query(Transaction).filter(
            Transaction.id.in_(transaction_ids),
            Transaction.user_id == user_id
        ).all()
        
        if not transactions:
            return {
                'total_transactions': 0,
                'rule_categorized': 0,
                'ml_categorized': 0,
                'failed_categorizations': 0,
                'success_rate': 0.0,
                'processing_time': 0
            }
        
        rule_categorized = 0
        ml_categorized = 0
        failed_categorizations = []
        
        # First pass: Rule-based categorization
        for transaction in transactions:
            if await self._categorize_transaction(transaction):
                rule_categorized += 1
        
        # Second pass: ML fallback for uncategorized transactions
        if use_ml_fallback:
            uncategorized_transactions = [tx for tx in transactions if not tx.is_categorized]
            
            if uncategorized_transactions:
                logger.info(f"Applying ML categorization to {len(uncategorized_transactions)} transactions")
                
                try:
                    # Use batch ML categorization for efficiency
                    ml_predictions = await self.ml_service.categorize_batch(uncategorized_transactions)
                    
                    for transaction in uncategorized_transactions:
                        prediction = ml_predictions.get(transaction.id)
                        if prediction and prediction.confidence >= 0.6:
                            transaction.category = prediction.category
                            transaction.subcategory = prediction.subcategory
                            transaction.is_categorized = True
                            transaction.confidence_score = prediction.confidence
                            
                            if not transaction.meta_data:
                                transaction.meta_data = {}
                            transaction.meta_data.update({
                                'ml_reasoning': prediction.reasoning,
                                'ml_alternatives': prediction.alternatives,
                                'categorization_method': 'ml'
                            })
                            
                            ml_categorized += 1
                        else:
                            failed_categorizations.append({
                                'transaction_id': transaction.id,
                                'description': transaction.description[:100],
                                'reason': 'Low ML confidence' if prediction else 'No ML prediction'
                            })
                
                except Exception as e:
                    logger.error(f"ML categorization failed: {str(e)}")
                    failed_categorizations.extend([
                        {'transaction_id': tx.id, 'reason': f'ML error: {str(e)}'} 
                        for tx in uncategorized_transactions
                    ])
        
        self.db.commit()
        processing_time = time.time() - start_time
        
        return {
            'total_transactions': len(transactions),
            'rule_categorized': rule_categorized,
            'ml_categorized': ml_categorized,
            'failed_categorizations': len(failed_categorizations),
            'success_rate': (rule_categorized + ml_categorized) / len(transactions) if transactions else 0,
            'processing_time': processing_time,
            'failed_details': failed_categorizations[:10]
        }

    async def get_categorization_confidence(self, transaction: Transaction) -> Dict[str, Any]:
        """Get detailed confidence information for a transaction's categorization"""
        confidence_data = {
            'confidence_breakdown': {},
            'alternatives': [],
            'rule_applied': None
        }
        
        # Check if a rule was applied
        if transaction.meta_data and transaction.meta_data.get('categorization_method') == 'rule':
            rule_id = transaction.meta_data.get('rule_id')
            if rule_id:
                rule = self.db.query(CategorizationRule).filter(CategorizationRule.id == rule_id).first()
                if rule:
                    confidence_data['rule_applied'] = {
                        'rule_id': rule.id,
                        'rule_name': rule.name,
                        'priority': rule.priority,
                        'pattern': rule.pattern
                    }
                    confidence_data['confidence_breakdown']['rule_confidence'] = 0.9
        
        # Get ML confidence if applicable
        if transaction.meta_data and transaction.meta_data.get('categorization_method') == 'ml':
            confidence_data['confidence_breakdown']['ml_confidence'] = transaction.confidence_score or 0.0
            confidence_data['confidence_breakdown']['ml_reasoning'] = transaction.meta_data.get('ml_reasoning')
        
        # Get alternative categories
        try:
            ml_prediction = await self.ml_service.categorize_single(transaction)
            if ml_prediction and ml_prediction.alternatives:
                confidence_data['alternatives'] = [
                    {
                        'category': alt.category,
                        'subcategory': alt.subcategory,
                        'confidence': alt.confidence
                    }
                    for alt in ml_prediction.alternatives[:3]  # Top 3 alternatives
                ]
        except Exception as e:
            logger.warning(f"Failed to get ML alternatives for transaction {transaction.id}: {e}")
        
        return confidence_data

    async def submit_categorization_feedback(self, transaction_id: int, user_id: int, feedback_type: str,
                                           suggested_category: Optional[str] = None,
                                           suggested_subcategory: Optional[str] = None,
                                           feedback_comment: Optional[str] = None) -> Dict[str, Any]:
        """Submit and process categorization feedback"""
        import uuid
        from datetime import datetime
        
        # Create feedback record
        feedback_id = str(uuid.uuid4())
        feedback_data = {
            'feedback_id': feedback_id,
            'transaction_id': transaction_id,
            'user_id': user_id,
            'feedback_type': feedback_type,
            'suggested_category': suggested_category,
            'suggested_subcategory': suggested_subcategory,
            'feedback_comment': feedback_comment,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Store feedback in transaction metadata
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        ).first()
        
        if not transaction:
            raise ValueError("Transaction not found")
        
        if not transaction.meta_data:
            transaction.meta_data = {}
        
        if 'feedback_history' not in transaction.meta_data:
            transaction.meta_data['feedback_history'] = []
        
        transaction.meta_data['feedback_history'].append(feedback_data)
        
        # Process feedback based on type
        impact = 'feedback_recorded'
        ml_learning = False
        
        if feedback_type == 'correct':
            # Mark as verified correct
            transaction.meta_data['verified_correct'] = True
            impact = 'marked_verified'
            
        elif feedback_type == 'incorrect':
            # Mark as incorrect and potentially recategorize
            transaction.meta_data['verified_incorrect'] = True
            impact = 'marked_incorrect'
            
        elif feedback_type == 'suggest_alternative':
            # Store old category for audit logging
            old_category = transaction.category
            
            # Apply suggested category and create rule
            transaction.category = suggested_category
            transaction.subcategory = suggested_subcategory
            transaction.is_categorized = True
            transaction.meta_data['user_corrected'] = True
            
            # Create rule from correction
            await self.create_rule_from_correction(
                user_id=user_id,
                transaction_id=transaction_id,
                new_category=suggested_category,
                new_subcategory=suggested_subcategory,
                create_rule=True
            )
            
            # Audit logging for categorization change
            security_audit_logger.log_categorization_change(
                user_id=user_id,
                transaction_id=transaction_id,
                old_category=old_category,
                new_category=suggested_category,
                method="feedback_correction",
                confidence_score=transaction.confidence_score
            )
            
            impact = 'category_applied_and_rule_created'
            ml_learning = True
        
        self.db.commit()
        
        return {
            'feedback_id': feedback_id,
            'impact': impact,
            'ml_learning': ml_learning
        }

    async def get_category_suggestions(self, transaction: Transaction, include_ml: bool = True, include_rules: bool = True) -> Dict[str, Any]:
        """Get comprehensive category suggestions for a transaction"""
        suggestions = []
        rule_matches = []
        ml_predictions = []
        
        # Get rule-based suggestions
        if include_rules:
            rules = self.db.query(CategorizationRule).filter(
                CategorizationRule.user_id == transaction.user_id,
                CategorizationRule.is_active == True
            ).all()
            
            for rule in rules:
                if self._rule_matches(rule, transaction):
                    rule_match = {
                        'category': rule.category,
                        'subcategory': rule.subcategory,
                        'confidence': 0.9,
                        'method': 'rule',
                        'rule_id': rule.id,
                        'rule_name': rule.name,
                        'pattern': rule.pattern
                    }
                    rule_matches.append(rule_match)
                    suggestions.append(rule_match)
        
        # Get ML-based suggestions
        if include_ml:
            try:
                ml_prediction = await self.ml_service.categorize_single(transaction)
                if ml_prediction:
                    ml_pred = {
                        'category': ml_prediction.category,
                        'subcategory': ml_prediction.subcategory,
                        'confidence': ml_prediction.confidence,
                        'method': 'ml',
                        'reasoning': ml_prediction.reasoning
                    }
                    ml_predictions.append(ml_pred)
                    suggestions.append(ml_pred)
                    
                    # Add alternatives
                    if ml_prediction.alternatives:
                        for alt in ml_prediction.alternatives[:3]:
                            alt_suggestion = {
                                'category': alt.category,
                                'subcategory': alt.subcategory,
                                'confidence': alt.confidence,
                                'method': 'ml_alternative',
                                'reasoning': alt.reasoning
                            }
                            suggestions.append(alt_suggestion)
                            ml_predictions.append(alt_suggestion)
            except Exception as e:
                logger.warning(f"ML suggestions failed for transaction {transaction.id}: {e}")
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'suggestions': suggestions[:10],  # Top 10 suggestions
            'rule_matches': rule_matches,
            'ml_predictions': ml_predictions,
            'confidence_threshold': 0.6,
            'total_suggestions': len(suggestions)
        }

    async def auto_improve_categorization(self, user_id: int, batch_id: Optional[str] = None, min_confidence_threshold: float = 0.5, max_transactions: int = 1000) -> Dict[str, Any]:
        """Automatically improve categorization based on feedback and patterns"""
        import time
        start_time = time.time()
        
        # Get transactions with feedback (with limit)
        query = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.meta_data.isnot(None)
        )
        
        if batch_id:
            query = query.filter(Transaction.import_batch == batch_id)
        
        transactions = query.limit(max_transactions).all()
        
        rules_created = 0
        rules_updated = 0
        ml_improvements = 0
        transactions_reprocessed = 0
        
        # Analyze feedback patterns
        feedback_patterns = {}
        for transaction in transactions:
            if transaction.meta_data and 'feedback_history' in transaction.meta_data:
                for feedback in transaction.meta_data['feedback_history']:
                    if feedback['feedback_type'] == 'suggest_alternative':
                        pattern_key = f"{transaction.description.lower()}_{transaction.amount}"
                        if pattern_key not in feedback_patterns:
                            feedback_patterns[pattern_key] = []
                        feedback_patterns[pattern_key].append({
                            'suggested_category': feedback['suggested_category'],
                            'suggested_subcategory': feedback['suggested_subcategory'],
                            'transaction_id': transaction.id
                        })
        
        # Create rules from patterns
        for pattern_key, suggestions in feedback_patterns.items():
            if len(suggestions) >= 2:  # At least 2 similar corrections
                # Find most common suggestion
                category_counts = {}
                for suggestion in suggestions:
                    cat_key = f"{suggestion['suggested_category']}_{suggestion['suggested_subcategory']}"
                    category_counts[cat_key] = category_counts.get(cat_key, 0) + 1
                
                most_common = max(category_counts.items(), key=lambda x: x[1])
                if most_common[1] >= 2:  # At least 2 corrections for same category
                    category, subcategory = most_common[0].split('_', 1)
                    
                    # Create rule
                    transaction = self.db.query(Transaction).filter(
                        Transaction.id == suggestions[0]['transaction_id']
                    ).first()
                    
                    if transaction:
                        # Create pattern from description
                        pattern = self._create_pattern_from_description(transaction.description)
                        
                        # Check if rule already exists
                        existing_rule = self.db.query(CategorizationRule).filter(
                            CategorizationRule.user_id == user_id,
                            CategorizationRule.pattern == pattern,
                            CategorizationRule.category == category
                        ).first()
                        
                        if existing_rule:
                            # Update existing rule
                            existing_rule.priority = min(existing_rule.priority + 1, 10)
                            rules_updated += 1
                        else:
                            # Create new rule
                            new_rule = CategorizationRule(
                                user_id=user_id,
                                name=f"Auto-generated from feedback ({len(suggestions)} corrections)",
                                pattern=pattern,
                                category=category,
                                subcategory=subcategory,
                                priority=5,
                                is_active=True
                            )
                            self.db.add(new_rule)
                            rules_created += 1
        
        # Reprocess transactions with new rules (with limit)
        if rules_created > 0 or rules_updated > 0:
            uncategorized = self.db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.is_categorized == False
            )
            
            if batch_id:
                uncategorized = uncategorized.filter(Transaction.import_batch == batch_id)
            
            uncategorized_transactions = uncategorized.limit(max_transactions).all()
            
            for transaction in uncategorized_transactions:
                if await self._categorize_transaction(transaction):
                    transactions_reprocessed += 1
        
        self.db.commit()
        processing_time = time.time() - start_time
        
        # Calculate improvement score
        improvement_score = (rules_created * 0.3 + rules_updated * 0.2 + transactions_reprocessed * 0.1) / max(len(transactions), 1)
        
        return {
            'rules_created': rules_created,
            'rules_updated': rules_updated,
            'ml_improvements': ml_improvements,
            'transactions_reprocessed': transactions_reprocessed,
            'improvement_score': min(improvement_score, 1.0),
            'processing_time': processing_time
        }

    async def get_categorization_performance(self, user_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get comprehensive categorization performance metrics"""
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        transactions = query.all()
        
        if not transactions:
            return {
                'overall': {},
                'methods': {},
                'confidence_distribution': {},
                'categories': {},
                'trends': {},
                'feedback': {}
            }
        
        # Overall metrics
        total_transactions = len(transactions)
        categorized_transactions = [t for t in transactions if t.is_categorized]
        uncategorized_transactions = [t for t in transactions if not t.is_categorized]
        
        overall_metrics = {
            'total_transactions': total_transactions,
            'categorized_count': len(categorized_transactions),
            'uncategorized_count': len(uncategorized_transactions),
            'categorization_rate': len(categorized_transactions) / total_transactions if total_transactions > 0 else 0,
            'average_confidence': sum(t.confidence_score or 0 for t in categorized_transactions) / len(categorized_transactions) if categorized_transactions else 0
        }
        
        # Method breakdown
        method_counts = {}
        for transaction in categorized_transactions:
            method = transaction.meta_data.get('categorization_method', 'unknown') if transaction.meta_data else 'unknown'
            method_counts[method] = method_counts.get(method, 0) + 1
        
        methods = {
            'rule_based': method_counts.get('rule', 0),
            'ml_based': method_counts.get('ml', 0),
            'user_corrected': method_counts.get('user', 0),
            'unknown': method_counts.get('unknown', 0)
        }
        
        # Confidence distribution
        confidence_ranges = {
            'high': 0,      # 0.8-1.0
            'medium': 0,    # 0.6-0.79
            'low': 0        # 0.0-0.59
        }
        
        for transaction in categorized_transactions:
            confidence = transaction.confidence_score or 0
            if confidence >= 0.8:
                confidence_ranges['high'] += 1
            elif confidence >= 0.6:
                confidence_ranges['medium'] += 1
            else:
                confidence_ranges['low'] += 1
        
        # Category performance
        category_performance = {}
        for transaction in categorized_transactions:
            category = transaction.category or 'uncategorized'
            if category not in category_performance:
                category_performance[category] = {
                    'count': 0,
                    'total_amount': 0,
                    'average_confidence': 0,
                    'confidence_scores': []
                }
            
            category_performance[category]['count'] += 1
            category_performance[category]['total_amount'] += abs(transaction.amount)
            category_performance[category]['confidence_scores'].append(transaction.confidence_score or 0)
        
        # Calculate average confidence for each category
        for category, data in category_performance.items():
            if data['confidence_scores']:
                data['average_confidence'] = sum(data['confidence_scores']) / len(data['confidence_scores'])
            data.pop('confidence_scores', None)  # Remove raw scores from response
        
        # Feedback analysis
        feedback_analysis = {
            'total_feedback': 0,
            'correct_feedback': 0,
            'incorrect_feedback': 0,
            'suggestions_feedback': 0
        }
        
        for transaction in transactions:
            if transaction.meta_data and 'feedback_history' in transaction.meta_data:
                feedback_analysis['total_feedback'] += len(transaction.meta_data['feedback_history'])
                for feedback in transaction.meta_data['feedback_history']:
                    if feedback['feedback_type'] == 'correct':
                        feedback_analysis['correct_feedback'] += 1
                    elif feedback['feedback_type'] == 'incorrect':
                        feedback_analysis['incorrect_feedback'] += 1
                    elif feedback['feedback_type'] == 'suggest_alternative':
                        feedback_analysis['suggestions_feedback'] += 1
        
        return {
            'overall': overall_metrics,
            'methods': methods,
            'confidence_distribution': confidence_ranges,
            'categories': category_performance,
            'trends': {},  # Would need time-series data for trends
            'feedback': feedback_analysis
        }

    def _create_pattern_from_description(self, description: str) -> str:
        """Create a categorization pattern from transaction description"""
        # Simple pattern creation - can be enhanced with more sophisticated NLP
        words = description.lower().split()
        # Take first 3 significant words (skip common words)
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        significant_words = [word for word in words if word not in common_words][:3]
        return ' '.join(significant_words)