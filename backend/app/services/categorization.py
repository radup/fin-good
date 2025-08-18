from sqlalchemy.orm import Session
from app.models.transaction import Transaction, CategorizationRule
from app.services.ml_categorization import MLCategorizationService, MLCategoryPrediction
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
        """Get ML category suggestions without applying categorization"""
        try:
            prediction = await self.ml_service.categorize_transaction(transaction)
            
            if prediction:
                return {
                    'primary_suggestion': {
                        'category': prediction.category,
                        'subcategory': prediction.subcategory,
                        'confidence': prediction.confidence,
                        'reasoning': prediction.reasoning
                    },
                    'alternatives': prediction.alternatives,
                    'has_suggestions': True
                }
            else:
                return {
                    'has_suggestions': False,
                    'error': 'No ML suggestions available'
                }
                
        except Exception as e:
            logger.error(f"Failed to get ML suggestions for transaction {transaction.id}: {str(e)}")
            return {
                'has_suggestions': False,
                'error': str(e)
            }