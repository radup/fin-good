from sqlalchemy.orm import Session
from app.models.transaction import Transaction, CategorizationRule
import re
import logging

logger = logging.getLogger(__name__)

class CategorizationService:
    def __init__(self, db: Session):
        self.db = db
    
    async def categorize_user_transactions(self, user_id: int, batch_id: str = None) -> int:
        """Categorize all uncategorized transactions for a user"""
        query = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_categorized == False
        )
        
        if batch_id:
            query = query.filter(Transaction.import_batch == batch_id)
        
        transactions = query.all()
        categorized_count = 0
        
        for transaction in transactions:
            if await self._categorize_transaction(transaction):
                categorized_count += 1
        
        self.db.commit()
        return categorized_count
    
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
        """Update transaction category and auto-categorize similar transactions"""
        # Update the specific transaction
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        ).first()
        
        if not transaction:
            raise ValueError("Transaction not found")
        
        # Update transaction
        transaction.category = category
        transaction.subcategory = subcategory
        transaction.is_categorized = True
        transaction.confidence_score = 1.0  # Manual categorization has highest confidence
        
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
            "new_rule_created": True
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