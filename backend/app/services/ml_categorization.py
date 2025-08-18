import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import aiohttp
import hashlib
import re
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.transaction import Transaction, CategorizationRule
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class MLCategoryPrediction:
    """ML categorization prediction with confidence and alternatives."""
    category: str
    subcategory: Optional[str] = None
    confidence: float = 0.0
    reasoning: Optional[str] = None
    alternatives: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []

@dataclass
class MLModelPerformance:
    """ML model performance metrics."""
    total_predictions: int = 0
    correct_predictions: int = 0
    average_confidence: float = 0.0
    accuracy: float = 0.0
    response_time_avg: float = 0.0
    last_updated: datetime = None

class OllamaClient:
    """Async client for Ollama API interactions."""
    
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=30)
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate(self, prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        """Generate response from Ollama model."""
        if not self.session:
            raise RuntimeError("OllamaClient must be used as async context manager")
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": 256
            }
        }
        
        try:
            async with self.session.post(f"{self.base_url}/api/generate", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error {response.status}: {error_text}")
                
                result = await response.json()
                return result
                
        except aiohttp.ClientError as e:
            logger.error(f"Ollama client error: {str(e)}")
            raise Exception(f"Failed to connect to Ollama: {str(e)}")
        except asyncio.TimeoutError:
            logger.error("Ollama request timed out")
            raise Exception("Ollama request timed out")

class MLCategorizationService:
    """ML-powered transaction categorization using Ollama."""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 3600  # 1 hour
        self.performance_metrics = MLModelPerformance()
        
    async def categorize_transaction(self, transaction: Transaction) -> Optional[MLCategoryPrediction]:
        """Categorize a single transaction using ML."""
        start_time = datetime.now()
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(transaction)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for transaction {transaction.id}")
                return cached_result
            
            # Get user context for few-shot learning
            user_context = await self._get_user_context(transaction.user_id)
            
            # Build prompt for ML categorization
            prompt = self._build_categorization_prompt(transaction, user_context)
            
            # Get ML prediction
            async with OllamaClient() as client:
                response = await client.generate(prompt, temperature=0.1)
                
            # Parse ML response
            prediction = self._parse_ml_response(response.get('response', ''))
            
            if prediction:
                # Cache the result
                self._cache_result(cache_key, prediction)
                
                # Update performance metrics
                response_time = (datetime.now() - start_time).total_seconds()
                self._update_performance_metrics(response_time)
                
                logger.info(f"ML categorized transaction {transaction.id}: "
                          f"{prediction.category} (confidence: {prediction.confidence:.2f})")
                
                return prediction
            
        except Exception as e:
            logger.error(f"ML categorization failed for transaction {transaction.id}: {str(e)}")
            return None
        
        return None
    
    async def categorize_batch(self, transactions: List[Transaction]) -> Dict[int, MLCategoryPrediction]:
        """Categorize multiple transactions efficiently."""
        results = {}
        
        # Group similar transactions for batch processing
        transaction_groups = self._group_similar_transactions(transactions)
        
        for group_key, group_transactions in transaction_groups.items():
            try:
                # Use the first transaction as representative for the group
                representative = group_transactions[0]
                prediction = await self.categorize_transaction(representative)
                
                if prediction:
                    # Apply prediction to all transactions in the group
                    for transaction in group_transactions:
                        # Adjust confidence based on similarity to representative
                        adjusted_prediction = MLCategoryPrediction(
                            category=prediction.category,
                            subcategory=prediction.subcategory,
                            confidence=prediction.confidence * self._calculate_similarity(transaction, representative),
                            reasoning=prediction.reasoning,
                            alternatives=prediction.alternatives
                        )
                        results[transaction.id] = adjusted_prediction
                        
            except Exception as e:
                logger.error(f"Batch categorization failed for group {group_key}: {str(e)}")
        
        return results
    
    async def _get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Get user's transaction history for few-shot learning context."""
        # Get recent categorized transactions for context
        recent_transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_categorized == True,
            Transaction.confidence_score >= 0.8
        ).order_by(desc(Transaction.created_at)).limit(20).all()
        
        # Get user's categorization rules
        rules = self.db.query(CategorizationRule).filter(
            CategorizationRule.user_id == user_id,
            CategorizationRule.is_active == True
        ).order_by(desc(CategorizationRule.priority)).all()
        
        # Build category examples from transactions
        category_examples = {}
        for tx in recent_transactions:
            if tx.category:
                if tx.category not in category_examples:
                    category_examples[tx.category] = []
                
                example = {
                    "description": tx.description,
                    "vendor": tx.vendor,
                    "amount": tx.amount,
                    "subcategory": tx.subcategory
                }
                category_examples[tx.category].append(example)
        
        # Limit examples per category
        for category in category_examples:
            category_examples[category] = category_examples[category][:3]
        
        return {
            "category_examples": category_examples,
            "rules": [(rule.pattern, rule.category, rule.subcategory) for rule in rules[:10]],
            "total_transactions": len(recent_transactions)
        }
    
    def _build_categorization_prompt(self, transaction: Transaction, user_context: Dict[str, Any]) -> str:
        """Build comprehensive prompt for transaction categorization."""
        
        # Sanitize transaction data
        description = self._sanitize_text(transaction.description)
        vendor = self._sanitize_text(transaction.vendor) if transaction.vendor else "Unknown"
        amount = abs(transaction.amount)  # Use absolute value for security
        
        # Base prompt template
        prompt = f"""You are a financial transaction categorization expert. Analyze the following transaction and provide the most appropriate category.

Transaction Details:
- Description: {description}
- Vendor: {vendor}
- Amount: ${amount:.2f}
- Type: {'Income' if transaction.amount > 0 else 'Expense'}

"""
        
        # Add user context for few-shot learning
        if user_context.get("category_examples"):
            prompt += "Previous categorization examples from this user:\n"
            for category, examples in user_context["category_examples"].items():
                prompt += f"\n{category}:\n"
                for example in examples[:2]:  # Limit examples
                    prompt += f"  - {example['description']} ({example['vendor']}) - ${abs(example['amount']):.2f}\n"
        
        # Add categorization rules context
        if user_context.get("rules"):
            prompt += "\nUser's categorization rules:\n"
            for pattern, category, subcategory in user_context["rules"][:5]:
                subcategory_text = f" -> {subcategory}" if subcategory else ""
                prompt += f"  - Pattern: {pattern} -> {category}{subcategory_text}\n"
        
        # Add common financial categories
        prompt += """
Common financial categories:
- Food & Dining: restaurants, groceries, food delivery
- Transportation: gas, parking, rideshare, public transit
- Shopping: retail, clothing, electronics, online purchases
- Bills & Utilities: electricity, water, internet, phone
- Entertainment: movies, streaming, games, events
- Healthcare: medical, dental, pharmacy, insurance
- Business: office supplies, software, professional services
- Income: salary, freelance, investment returns
- Transfer: bank transfers, savings, investments

Provide your response in this exact JSON format:
{
    "category": "Primary Category Name",
    "subcategory": "Specific Subcategory (optional)",
    "confidence": 0.85,
    "reasoning": "Brief explanation of why this category was chosen",
    "alternatives": [
        {"category": "Alternative Category", "confidence": 0.65},
        {"category": "Another Alternative", "confidence": 0.45}
    ]
}

Important guidelines:
1. Confidence should be between 0.0 and 1.0
2. Use existing user categories when possible
3. Provide 1-2 alternative categories with lower confidence
4. Keep reasoning concise and relevant
5. Use title case for category names
"""
        
        return prompt
    
    def _parse_ml_response(self, response: str) -> Optional[MLCategoryPrediction]:
        """Parse ML model response into structured prediction."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', response, re.DOTALL | re.IGNORECASE)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON directly
                json_match = re.search(r'{.*}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    logger.warning(f"No JSON found in ML response: {response[:200]}")
                    return None
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Validate required fields
            if not data.get('category'):
                logger.warning("ML response missing category field")
                return None
            
            # Normalize confidence score
            confidence = float(data.get('confidence', 0.5))
            confidence = max(0.0, min(1.0, confidence))
            
            # Create prediction object
            prediction = MLCategoryPrediction(
                category=data['category'].strip(),
                subcategory=data.get('subcategory', '').strip() or None,
                confidence=confidence,
                reasoning=data.get('reasoning', '').strip() or None,
                alternatives=data.get('alternatives', [])
            )
            
            return prediction
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ML response JSON: {str(e)}")
            logger.debug(f"Raw response: {response}")
            return None
        except Exception as e:
            logger.error(f"Error parsing ML response: {str(e)}")
            return None
    
    def _get_cache_key(self, transaction: Transaction) -> str:
        """Generate cache key for transaction."""
        # Create key based on normalized transaction data
        key_data = f"{transaction.description}|{transaction.vendor}|{abs(transaction.amount):.2f}|{transaction.user_id}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[MLCategoryPrediction]:
        """Get cached categorization result."""
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < self.cache_ttl:
                return result
            else:
                # Remove expired entry
                del self.cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, prediction: MLCategoryPrediction):
        """Cache categorization result."""
        self.cache[cache_key] = (prediction, datetime.now())
        
        # Simple cache cleanup (remove oldest entries if cache is too large)
        if len(self.cache) > 1000:
            # Remove oldest 20% of entries
            sorted_items = sorted(self.cache.items(), key=lambda x: x[1][1])
            items_to_remove = len(sorted_items) // 5
            for key, _ in sorted_items[:items_to_remove]:
                del self.cache[key]
    
    def _group_similar_transactions(self, transactions: List[Transaction]) -> Dict[str, List[Transaction]]:
        """Group similar transactions for batch processing."""
        groups = {}
        
        for transaction in transactions:
            # Create grouping key based on vendor and description patterns
            vendor_key = transaction.vendor.lower() if transaction.vendor else "no_vendor"
            desc_words = transaction.description.lower().split()[:3]
            desc_key = "_".join(desc_words)
            group_key = f"{vendor_key}_{desc_key}"
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(transaction)
        
        return groups
    
    def _calculate_similarity(self, transaction1: Transaction, transaction2: Transaction) -> float:
        """Calculate similarity between two transactions."""
        similarity = 1.0
        
        # Vendor similarity
        if transaction1.vendor and transaction2.vendor:
            if transaction1.vendor.lower() != transaction2.vendor.lower():
                similarity *= 0.9
        
        # Description similarity
        words1 = set(transaction1.description.lower().split())
        words2 = set(transaction2.description.lower().split())
        if words1 and words2:
            common_words = words1.intersection(words2)
            similarity *= (len(common_words) / max(len(words1), len(words2))) * 0.5 + 0.5
        
        # Amount similarity (less important for categorization)
        amount_diff = abs(transaction1.amount - transaction2.amount)
        if amount_diff > 100:
            similarity *= 0.95
        
        return max(0.1, similarity)  # Minimum similarity threshold
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text data before sending to ML model."""
        if not text:
            return ""
        
        # Remove potential PII patterns
        sanitized = text
        
        # Remove email addresses
        sanitized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', sanitized)
        
        # Remove phone numbers
        sanitized = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', sanitized)
        
        # Remove SSN patterns
        sanitized = re.sub(r'\b\d{3}-?\d{2}-?\d{4}\b', '[SSN]', sanitized)
        
        # Remove credit card patterns
        sanitized = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', sanitized)
        
        # Limit length for security
        return sanitized[:500]
    
    def _update_performance_metrics(self, response_time: float):
        """Update ML model performance metrics."""
        self.performance_metrics.total_predictions += 1
        
        # Update average response time
        current_avg = self.performance_metrics.response_time_avg
        total = self.performance_metrics.total_predictions
        self.performance_metrics.response_time_avg = ((current_avg * (total - 1)) + response_time) / total
        
        self.performance_metrics.last_updated = datetime.now()
    
    async def track_prediction_accuracy(self, transaction_id: int, user_correction: bool):
        """Track accuracy of ML predictions based on user feedback."""
        if user_correction:
            # User made a correction, so prediction was incorrect
            pass
        else:
            # No correction needed, prediction was correct
            self.performance_metrics.correct_predictions += 1
        
        # Update accuracy
        if self.performance_metrics.total_predictions > 0:
            self.performance_metrics.accuracy = (
                self.performance_metrics.correct_predictions / 
                self.performance_metrics.total_predictions
            )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current ML model performance metrics."""
        return {
            "total_predictions": self.performance_metrics.total_predictions,
            "correct_predictions": self.performance_metrics.correct_predictions,
            "accuracy": round(self.performance_metrics.accuracy, 3),
            "average_response_time": round(self.performance_metrics.response_time_avg, 3),
            "cache_size": len(self.cache),
            "last_updated": self.performance_metrics.last_updated.isoformat() if self.performance_metrics.last_updated else None
        }
    
    async def generate_training_data(self, user_id: int) -> List[Dict[str, Any]]:
        """Generate training data from user's categorized transactions."""
        categorized_transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_categorized == True,
            Transaction.confidence_score >= 0.8
        ).order_by(desc(Transaction.updated_at)).limit(100).all()
        
        training_data = []
        for tx in categorized_transactions:
            training_example = {
                "description": self._sanitize_text(tx.description),
                "vendor": self._sanitize_text(tx.vendor) if tx.vendor else None,
                "amount": abs(tx.amount),
                "category": tx.category,
                "subcategory": tx.subcategory,
                "confidence": tx.confidence_score,
                "date": tx.date.isoformat()
            }
            training_data.append(training_example)
        
        return training_data
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of ML categorization service."""
        try:
            # Test Ollama connection
            async with OllamaClient() as client:
                test_response = await client.generate("Test connection", temperature=0.1)
                ollama_healthy = bool(test_response.get('response'))
        except Exception as e:
            ollama_healthy = False
            logger.error(f"Ollama health check failed: {str(e)}")
        
        return {
            "status": "healthy" if ollama_healthy else "degraded",
            "ollama_connected": ollama_healthy,
            "cache_entries": len(self.cache),
            "performance_metrics": self.get_performance_metrics(),
            "timestamp": datetime.now().isoformat()
        }