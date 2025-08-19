"""
Pattern Recognition Engine for Intelligent Categorization

Advanced machine learning-powered pattern recognition system that learns from
user behavior, identifies categorization patterns, and automatically generates
optimized categorization rules for improved accuracy and efficiency.
"""

import asyncio
import json
import logging
import re
import hashlib
from typing import List, Dict, Any, Optional, Set, Tuple, Union
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, text
from sqlalchemy.exc import SQLAlchemyError
import statistics
import math

from app.models.transaction import Transaction, CategorizationRule
from app.models.user import User
from app.core.exceptions import ValidationException, BusinessLogicException
from app.core.audit_logger import security_audit_logger
from app.services.ml_categorization import MLCategorizationService, MLCategoryPrediction
from app.core.security_utils import input_sanitizer
import uuid

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of categorization patterns"""
    VENDOR_PATTERN = "vendor_pattern"
    DESCRIPTION_PATTERN = "description_pattern"
    AMOUNT_PATTERN = "amount_pattern"
    DATE_PATTERN = "date_pattern"
    FREQUENCY_PATTERN = "frequency_pattern"
    BEHAVIORAL_PATTERN = "behavioral_pattern"
    CORRECTION_PATTERN = "correction_pattern"


class PatternConfidenceLevel(Enum):
    """Confidence levels for pattern recognition"""
    VERY_HIGH = 0.95
    HIGH = 0.85
    MEDIUM = 0.70
    LOW = 0.55
    VERY_LOW = 0.40


class RuleGenerationStrategy(Enum):
    """Strategies for automatic rule generation"""
    CONSERVATIVE = "conservative"  # High confidence, fewer rules
    BALANCED = "balanced"         # Moderate confidence, balanced approach
    AGGRESSIVE = "aggressive"     # Lower confidence, more rules
    LEARNING = "learning"         # Adapt based on user feedback


@dataclass
class RecognizedPattern:
    """A recognized pattern from transaction analysis"""
    pattern_id: str
    pattern_type: PatternType
    pattern_value: str
    confidence_score: float
    frequency: int
    category: str
    subcategory: Optional[str]
    supporting_transactions: List[int]
    pattern_metadata: Dict[str, Any]
    created_at: datetime
    last_seen: datetime


@dataclass
class PatternRule:
    """Generated rule from pattern recognition"""
    rule_id: str
    pattern_id: str
    pattern_type: PatternType
    rule_pattern: str
    rule_type: str  # regex, keyword, vendor
    category: str
    subcategory: Optional[str]
    confidence: float
    priority: int
    estimated_accuracy: float
    supporting_evidence: Dict[str, Any]
    creation_reason: str


@dataclass
class PatternAnalysisResult:
    """Result of pattern analysis on transactions"""
    analysis_id: str
    user_id: int
    total_transactions_analyzed: int
    patterns_discovered: int
    rules_suggested: int
    high_confidence_patterns: int
    accuracy_improvements: Dict[str, float]
    analysis_duration_ms: int
    started_at: datetime
    completed_at: datetime
    discovered_patterns: List[RecognizedPattern]
    suggested_rules: List[PatternRule]


@dataclass
class UserBehaviorProfile:
    """Profile of user's categorization behavior and preferences"""
    user_id: int
    total_manual_corrections: int
    correction_patterns: Dict[str, int]
    preferred_categories: Dict[str, int]
    categorization_style: str  # detailed, simple, mixed
    consistency_score: float
    learning_rate: float
    last_updated: datetime


class PatternRecognitionLimits:
    """Performance and safety limits for pattern recognition"""
    MAX_TRANSACTIONS_ANALYZE = 5000
    MAX_PATTERNS_PER_ANALYSIS = 1000
    MAX_RULES_GENERATE = 100
    MIN_PATTERN_FREQUENCY = 3
    MIN_PATTERN_CONFIDENCE = 0.6
    MAX_ANALYSIS_TIME_MINUTES = 30
    CACHE_TTL_HOURS = 6


class PatternRecognitionEngine:
    """
    Advanced pattern recognition engine for intelligent categorization rule generation.
    
    Analyzes user transaction history, identifies patterns in categorization behavior,
    and automatically generates optimized rules to improve categorization accuracy.
    """
    
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.audit_logger = security_audit_logger
        self.ml_service = MLCategorizationService(db)
        
        # Pattern caches for performance
        self._pattern_cache: Dict[str, RecognizedPattern] = {}
        self._user_profile_cache: Optional[UserBehaviorProfile] = None
        self._cache_timestamp = datetime.utcnow()
        
        # Analysis configuration
        self.analysis_config = {
            "min_pattern_frequency": PatternRecognitionLimits.MIN_PATTERN_FREQUENCY,
            "min_confidence": PatternRecognitionLimits.MIN_PATTERN_CONFIDENCE,
            "max_patterns": PatternRecognitionLimits.MAX_PATTERNS_PER_ANALYSIS,
            "generation_strategy": RuleGenerationStrategy.BALANCED
        }
    
    async def analyze_user_patterns(
        self, 
        date_range_days: int = 90,
        include_uncategorized: bool = True,
        focus_corrections: bool = True
    ) -> PatternAnalysisResult:
        """
        Comprehensive analysis of user's transaction patterns for rule generation.
        
        Args:
            date_range_days: Days of history to analyze
            include_uncategorized: Whether to analyze uncategorized transactions
            focus_corrections: Whether to prioritize correction patterns
            
        Returns:
            PatternAnalysisResult with discovered patterns and rule suggestions
        """
        analysis_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        self.audit_logger.info(
            f"Starting pattern analysis for user {self.user.id}",
            extra={
                "analysis_id": analysis_id,
                "user_id": self.user.id,
                "date_range_days": date_range_days,
                "include_uncategorized": include_uncategorized,
                "focus_corrections": focus_corrections
            }
        )
        
        try:
            # Get transactions for analysis
            transactions = await self._get_transactions_for_pattern_analysis(
                date_range_days, include_uncategorized
            )
            
            if len(transactions) < 10:
                raise ValidationException("Insufficient transaction history for pattern analysis")
            
            # Build or update user behavior profile
            user_profile = await self._build_user_behavior_profile(transactions)
            
            # Discover patterns using multiple algorithms
            discovered_patterns = await self._discover_patterns(transactions, focus_corrections)
            
            # Generate rules from high-confidence patterns
            suggested_rules = await self._generate_rules_from_patterns(
                discovered_patterns, user_profile
            )
            
            # Calculate accuracy improvements
            accuracy_improvements = await self._estimate_accuracy_improvements(
                suggested_rules, transactions
            )
            
            end_time = datetime.utcnow()
            analysis_duration = int((end_time - start_time).total_seconds() * 1000)
            
            result = PatternAnalysisResult(
                analysis_id=analysis_id,
                user_id=self.user.id,
                total_transactions_analyzed=len(transactions),
                patterns_discovered=len(discovered_patterns),
                rules_suggested=len(suggested_rules),
                high_confidence_patterns=len([p for p in discovered_patterns if p.confidence_score >= 0.8]),
                accuracy_improvements=accuracy_improvements,
                analysis_duration_ms=analysis_duration,
                started_at=start_time,
                completed_at=end_time,
                discovered_patterns=discovered_patterns[:PatternRecognitionLimits.MAX_PATTERNS_PER_ANALYSIS],
                suggested_rules=suggested_rules[:PatternRecognitionLimits.MAX_RULES_GENERATE]
            )
            
            # Cache results for performance
            await self._cache_analysis_results(result)
            
            self.audit_logger.info(
                f"Pattern analysis completed for user {self.user.id}",
                extra={
                    "analysis_id": analysis_id,
                    "patterns_found": len(discovered_patterns),
                    "rules_suggested": len(suggested_rules),
                    "analysis_duration_ms": analysis_duration
                }
            )
            
            return result
            
        except Exception as e:
            self.audit_logger.error(
                f"Pattern analysis failed for user {self.user.id}",
                extra={
                    "analysis_id": analysis_id,
                    "error": str(e),
                    "user_id": self.user.id
                }
            )
            raise BusinessLogicException(f"Pattern analysis failed: {str(e)}")
    
    async def _get_transactions_for_pattern_analysis(
        self, 
        date_range_days: int, 
        include_uncategorized: bool
    ) -> List[Transaction]:
        """Get transactions for pattern analysis with proper filtering"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=date_range_days)
            
            query = self.db.query(Transaction).filter(
                Transaction.user_id == self.user.id,
                Transaction.date >= cutoff_date
            )
            
            if not include_uncategorized:
                query = query.filter(Transaction.is_categorized == True)
            
            transactions = query.order_by(desc(Transaction.date)).limit(
                PatternRecognitionLimits.MAX_TRANSACTIONS_ANALYZE
            ).all()
            
            return transactions
            
        except SQLAlchemyError as e:
            raise BusinessLogicException(f"Database error while fetching transactions: {str(e)}")
    
    async def _build_user_behavior_profile(self, transactions: List[Transaction]) -> UserBehaviorProfile:
        """Build comprehensive user behavior profile for pattern analysis"""
        
        manual_corrections = 0
        correction_patterns = defaultdict(int)
        category_counts = defaultdict(int)
        consistency_scores = []
        
        # Analyze categorization behavior
        for transaction in transactions:
            if transaction.is_categorized and transaction.category:
                category_counts[transaction.category] += 1
                
                # Check for manual corrections
                if (transaction.meta_data and 
                    transaction.meta_data.get('categorization_method') == 'manual'):
                    manual_corrections += 1
                    
                    # Track correction patterns
                    if transaction.meta_data.get('manual_correction'):
                        original_category = transaction.meta_data.get('original_ml_category')
                        if original_category:
                            correction_key = f"{original_category}->{transaction.category}"
                            correction_patterns[correction_key] += 1
                
                # Calculate consistency score based on confidence
                if transaction.confidence_score:
                    consistency_scores.append(transaction.confidence_score)
        
        # Determine categorization style
        categorization_style = self._determine_categorization_style(category_counts)
        
        # Calculate overall consistency
        consistency_score = statistics.mean(consistency_scores) if consistency_scores else 0.0
        
        # Calculate learning rate (how quickly user improves categorization)
        learning_rate = min(manual_corrections / max(len(transactions), 1), 1.0)
        
        profile = UserBehaviorProfile(
            user_id=self.user.id,
            total_manual_corrections=manual_corrections,
            correction_patterns=dict(correction_patterns),
            preferred_categories=dict(category_counts),
            categorization_style=categorization_style,
            consistency_score=consistency_score,
            learning_rate=learning_rate,
            last_updated=datetime.utcnow()
        )
        
        # Cache profile
        self._user_profile_cache = profile
        
        return profile
    
    def _determine_categorization_style(self, category_counts: Dict[str, int]) -> str:
        """Determine user's categorization style based on category usage"""
        total_categories = len(category_counts)
        total_transactions = sum(category_counts.values())
        
        if total_transactions == 0:
            return "unknown"
        
        # Calculate category distribution
        category_distribution = sorted(category_counts.values(), reverse=True)
        
        # Check if user prefers few categories (simple) or many (detailed)
        if total_categories <= 5:
            return "simple"
        elif total_categories >= 15:
            return "detailed"
        else:
            # Check distribution concentration
            if len(category_distribution) > 0:
                top_category_ratio = category_distribution[0] / total_transactions
                if top_category_ratio > 0.5:
                    return "simple"
                elif top_category_ratio < 0.2:
                    return "detailed"
            return "balanced"
    
    async def _discover_patterns(
        self, 
        transactions: List[Transaction],
        focus_corrections: bool
    ) -> List[RecognizedPattern]:
        """Discover categorization patterns using multiple algorithms"""
        
        discovered_patterns = []
        
        # 1. Vendor-based patterns
        vendor_patterns = await self._discover_vendor_patterns(transactions)
        discovered_patterns.extend(vendor_patterns)
        
        # 2. Description-based patterns
        description_patterns = await self._discover_description_patterns(transactions)
        discovered_patterns.extend(description_patterns)
        
        # 3. Amount-based patterns
        amount_patterns = await self._discover_amount_patterns(transactions)
        discovered_patterns.extend(amount_patterns)
        
        # 4. Frequency patterns
        frequency_patterns = await self._discover_frequency_patterns(transactions)
        discovered_patterns.extend(frequency_patterns)
        
        # 5. Correction patterns (if focus_corrections is True)
        if focus_corrections:
            correction_patterns = await self._discover_correction_patterns(transactions)
            discovered_patterns.extend(correction_patterns)
        
        # 6. Behavioral patterns
        behavioral_patterns = await self._discover_behavioral_patterns(transactions)
        discovered_patterns.extend(behavioral_patterns)
        
        # Filter and rank patterns
        filtered_patterns = self._filter_and_rank_patterns(discovered_patterns)
        
        return filtered_patterns
    
    async def _discover_vendor_patterns(self, transactions: List[Transaction]) -> List[RecognizedPattern]:
        """Discover patterns based on vendor names"""
        vendor_categories = defaultdict(lambda: defaultdict(list))
        
        for transaction in transactions:
            if transaction.vendor and transaction.is_categorized and transaction.category:
                vendor_key = transaction.vendor.lower().strip()
                category_key = f"{transaction.category}|{transaction.subcategory or ''}"
                vendor_categories[vendor_key][category_key].append(transaction.id)
        
        patterns = []
        for vendor, categories in vendor_categories.items():
            if len(categories) == 1:  # Vendor consistently categorized to one category
                category_key, transaction_ids = next(iter(categories.items()))
                if len(transaction_ids) >= self.analysis_config["min_pattern_frequency"]:
                    
                    category, subcategory = category_key.split('|', 1)
                    subcategory = subcategory if subcategory else None
                    
                    confidence = min(0.95, 0.7 + (len(transaction_ids) * 0.05))
                    
                    pattern = RecognizedPattern(
                        pattern_id=str(uuid.uuid4()),
                        pattern_type=PatternType.VENDOR_PATTERN,
                        pattern_value=vendor,
                        confidence_score=confidence,
                        frequency=len(transaction_ids),
                        category=category,
                        subcategory=subcategory,
                        supporting_transactions=transaction_ids,
                        pattern_metadata={
                            "vendor_name": vendor,
                            "consistency": 1.0,
                            "pattern_strength": "high"
                        },
                        created_at=datetime.utcnow(),
                        last_seen=datetime.utcnow()
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _discover_description_patterns(self, transactions: List[Transaction]) -> List[RecognizedPattern]:
        """Discover patterns based on transaction descriptions"""
        # Extract common keywords and phrases
        description_patterns = defaultdict(lambda: defaultdict(list))
        
        for transaction in transactions:
            if transaction.description and transaction.is_categorized and transaction.category:
                # Extract significant words (3+ characters, not common words)
                words = self._extract_significant_words(transaction.description)
                category_key = f"{transaction.category}|{transaction.subcategory or ''}"
                
                for word in words[:3]:  # Top 3 significant words
                    if len(word) >= 3:
                        description_patterns[word.lower()][category_key].append(transaction.id)
        
        patterns = []
        for keyword, categories in description_patterns.items():
            # Look for keywords that strongly predict a category
            total_occurrences = sum(len(txn_ids) for txn_ids in categories.values())
            
            if total_occurrences >= self.analysis_config["min_pattern_frequency"]:
                # Find dominant category
                dominant_category = max(categories.items(), key=lambda x: len(x[1]))
                category_key, transaction_ids = dominant_category
                
                # Calculate confidence based on dominance
                dominance = len(transaction_ids) / total_occurrences
                if dominance >= 0.7:  # At least 70% of the time leads to same category
                    
                    category, subcategory = category_key.split('|', 1)
                    subcategory = subcategory if subcategory else None
                    
                    confidence = min(0.90, dominance * 0.9)
                    
                    pattern = RecognizedPattern(
                        pattern_id=str(uuid.uuid4()),
                        pattern_type=PatternType.DESCRIPTION_PATTERN,
                        pattern_value=keyword,
                        confidence_score=confidence,
                        frequency=len(transaction_ids),
                        category=category,
                        subcategory=subcategory,
                        supporting_transactions=transaction_ids,
                        pattern_metadata={
                            "keyword": keyword,
                            "dominance": dominance,
                            "total_occurrences": total_occurrences
                        },
                        created_at=datetime.utcnow(),
                        last_seen=datetime.utcnow()
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _discover_amount_patterns(self, transactions: List[Transaction]) -> List[RecognizedPattern]:
        """Discover patterns based on transaction amounts"""
        amount_categories = defaultdict(lambda: defaultdict(list))
        
        for transaction in transactions:
            if transaction.amount and transaction.is_categorized and transaction.category:
                # Group amounts into ranges
                amount_range = self._get_amount_range(transaction.amount)
                category_key = f"{transaction.category}|{transaction.subcategory or ''}"
                amount_categories[amount_range][category_key].append(transaction.id)
        
        patterns = []
        for amount_range, categories in amount_categories.items():
            total_occurrences = sum(len(txn_ids) for txn_ids in categories.values())
            
            if total_occurrences >= self.analysis_config["min_pattern_frequency"]:
                # Find dominant category for this amount range
                dominant_category = max(categories.items(), key=lambda x: len(x[1]))
                category_key, transaction_ids = dominant_category
                
                dominance = len(transaction_ids) / total_occurrences
                if dominance >= 0.75:  # Strong pattern for amount range
                    
                    category, subcategory = category_key.split('|', 1)
                    subcategory = subcategory if subcategory else None
                    
                    confidence = min(0.85, dominance * 0.8)  # Lower max confidence for amounts
                    
                    pattern = RecognizedPattern(
                        pattern_id=str(uuid.uuid4()),
                        pattern_type=PatternType.AMOUNT_PATTERN,
                        pattern_value=amount_range,
                        confidence_score=confidence,
                        frequency=len(transaction_ids),
                        category=category,
                        subcategory=subcategory,
                        supporting_transactions=transaction_ids,
                        pattern_metadata={
                            "amount_range": amount_range,
                            "dominance": dominance,
                            "pattern_type": "amount_range"
                        },
                        created_at=datetime.utcnow(),
                        last_seen=datetime.utcnow()
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _discover_frequency_patterns(self, transactions: List[Transaction]) -> List[RecognizedPattern]:
        """Discover patterns based on transaction frequency and timing"""
        # Group transactions by vendor/description and analyze frequency
        frequency_groups = defaultdict(list)
        
        for transaction in transactions:
            if transaction.is_categorized and transaction.category:
                # Create key based on vendor or description
                key = (transaction.vendor or self._get_description_key(transaction.description)).lower()
                frequency_groups[key].append(transaction)
        
        patterns = []
        for key, group_transactions in frequency_groups.items():
            if len(group_transactions) >= self.analysis_config["min_pattern_frequency"]:
                # Check if this is a recurring pattern
                dates = sorted([txn.date for txn in group_transactions])
                
                if len(dates) >= 3:
                    # Calculate average interval
                    intervals = []
                    for i in range(1, len(dates)):
                        interval = (dates[i] - dates[i-1]).days
                        intervals.append(interval)
                    
                    if intervals:
                        avg_interval = statistics.mean(intervals)
                        interval_std = statistics.stdev(intervals) if len(intervals) > 1 else 0
                        
                        # Check for regular frequency (low variance)
                        if interval_std <= avg_interval * 0.3:  # Low variance indicates regularity
                            # This is a recurring pattern
                            category_counts = Counter(txn.category for txn in group_transactions)
                            dominant_category = category_counts.most_common(1)[0]
                            
                            consistency = dominant_category[1] / len(group_transactions)
                            
                            if consistency >= 0.8:  # High consistency
                                confidence = min(0.88, 0.6 + (consistency * 0.3))
                                
                                pattern = RecognizedPattern(
                                    pattern_id=str(uuid.uuid4()),
                                    pattern_type=PatternType.FREQUENCY_PATTERN,
                                    pattern_value=key,
                                    confidence_score=confidence,
                                    frequency=len(group_transactions),
                                    category=dominant_category[0],
                                    subcategory=None,
                                    supporting_transactions=[txn.id for txn in group_transactions],
                                    pattern_metadata={
                                        "avg_interval_days": avg_interval,
                                        "interval_consistency": 1 - (interval_std / max(avg_interval, 1)),
                                        "frequency_type": "regular_recurring",
                                        "consistency": consistency
                                    },
                                    created_at=datetime.utcnow(),
                                    last_seen=max(dates)
                                )
                                patterns.append(pattern)
        
        return patterns
    
    async def _discover_correction_patterns(self, transactions: List[Transaction]) -> List[RecognizedPattern]:
        """Discover patterns from user corrections to improve accuracy"""
        correction_patterns = defaultdict(lambda: defaultdict(list))
        
        for transaction in transactions:
            if (transaction.meta_data and 
                transaction.meta_data.get('manual_correction') and
                transaction.meta_data.get('original_ml_category')):
                
                original_category = transaction.meta_data['original_ml_category']
                corrected_category = transaction.category
                
                # Look for patterns in what gets corrected
                if transaction.vendor:
                    pattern_key = f"vendor:{transaction.vendor.lower()}"
                else:
                    # Use first significant words from description
                    words = self._extract_significant_words(transaction.description)
                    pattern_key = f"desc:{' '.join(words[:2])}"
                
                correction_key = f"{original_category}->{corrected_category}"
                correction_patterns[pattern_key][correction_key].append(transaction.id)
        
        patterns = []
        for pattern_key, corrections in correction_patterns.items():
            total_corrections = sum(len(txn_ids) for txn_ids in corrections.values())
            
            if total_corrections >= self.analysis_config["min_pattern_frequency"]:
                # Find most common correction
                dominant_correction = max(corrections.items(), key=lambda x: len(x[1]))
                correction_key, transaction_ids = dominant_correction
                
                # Extract corrected category
                corrected_category = correction_key.split('->')[-1]
                
                consistency = len(transaction_ids) / total_corrections
                
                if consistency >= 0.7:  # Strong correction pattern
                    confidence = min(0.92, 0.7 + (consistency * 0.22))
                    
                    pattern = RecognizedPattern(
                        pattern_id=str(uuid.uuid4()),
                        pattern_type=PatternType.CORRECTION_PATTERN,
                        pattern_value=pattern_key.split(':', 1)[1],
                        confidence_score=confidence,
                        frequency=len(transaction_ids),
                        category=corrected_category,
                        subcategory=None,
                        supporting_transactions=transaction_ids,
                        pattern_metadata={
                            "pattern_source": pattern_key.split(':', 1)[0],
                            "correction_consistency": consistency,
                            "total_corrections": total_corrections,
                            "correction_type": correction_key
                        },
                        created_at=datetime.utcnow(),
                        last_seen=datetime.utcnow()
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _discover_behavioral_patterns(self, transactions: List[Transaction]) -> List[RecognizedPattern]:
        """Discover high-level behavioral patterns in categorization"""
        patterns = []
        
        # Analyze categorization timing patterns
        categorized_transactions = [t for t in transactions if t.is_categorized]
        
        if len(categorized_transactions) >= 10:
            # Group by day of week, time of day, etc.
            day_patterns = defaultdict(lambda: defaultdict(int))
            
            for transaction in categorized_transactions:
                day_of_week = transaction.date.strftime('%A')
                category = transaction.category
                day_patterns[day_of_week][category] += 1
            
            # Look for strong day-category associations
            for day, categories in day_patterns.items():
                total_day_transactions = sum(categories.values())
                
                if total_day_transactions >= self.analysis_config["min_pattern_frequency"]:
                    dominant_category = max(categories.items(), key=lambda x: x[1])
                    category, count = dominant_category
                    
                    dominance = count / total_day_transactions
                    
                    if dominance >= 0.6:  # Strong day-category pattern
                        confidence = min(0.75, dominance * 0.75)
                        
                        pattern = RecognizedPattern(
                            pattern_id=str(uuid.uuid4()),
                            pattern_type=PatternType.BEHAVIORAL_PATTERN,
                            pattern_value=f"day:{day}",
                            confidence_score=confidence,
                            frequency=count,
                            category=category,
                            subcategory=None,
                            supporting_transactions=[],  # Would need to track transaction IDs
                            pattern_metadata={
                                "behavioral_type": "day_of_week",
                                "day": day,
                                "dominance": dominance,
                                "total_day_transactions": total_day_transactions
                            },
                            created_at=datetime.utcnow(),
                            last_seen=datetime.utcnow()
                        )
                        patterns.append(pattern)
        
        return patterns
    
    def _filter_and_rank_patterns(self, patterns: List[RecognizedPattern]) -> List[RecognizedPattern]:
        """Filter and rank patterns by confidence and utility"""
        # Filter by minimum confidence
        filtered = [p for p in patterns if p.confidence_score >= self.analysis_config["min_confidence"]]
        
        # Remove duplicate patterns (same value and category)
        seen_combinations = set()
        deduplicated = []
        
        for pattern in filtered:
            combo_key = f"{pattern.pattern_value}:{pattern.category}"
            if combo_key not in seen_combinations:
                seen_combinations.add(combo_key)
                deduplicated.append(pattern)
        
        # Sort by confidence score and frequency
        ranked = sorted(
            deduplicated,
            key=lambda p: (p.confidence_score, p.frequency, len(p.supporting_transactions)),
            reverse=True
        )
        
        return ranked[:self.analysis_config["max_patterns"]]
    
    async def _generate_rules_from_patterns(
        self, 
        patterns: List[RecognizedPattern],
        user_profile: UserBehaviorProfile
    ) -> List[PatternRule]:
        """Generate categorization rules from recognized patterns"""
        
        generated_rules = []
        
        for pattern in patterns:
            if pattern.confidence_score >= PatternRecognitionLimits.MIN_PATTERN_CONFIDENCE:
                
                # Determine rule type and pattern based on pattern type
                rule_type, rule_pattern = self._convert_pattern_to_rule(pattern)
                
                if rule_type and rule_pattern:
                    # Calculate rule priority based on confidence and frequency
                    priority = self._calculate_rule_priority(pattern, user_profile)
                    
                    # Estimate accuracy based on pattern strength
                    estimated_accuracy = self._estimate_rule_accuracy(pattern)
                    
                    rule = PatternRule(
                        rule_id=str(uuid.uuid4()),
                        pattern_id=pattern.pattern_id,
                        pattern_type=pattern.pattern_type,
                        rule_pattern=rule_pattern,
                        rule_type=rule_type,
                        category=pattern.category,
                        subcategory=pattern.subcategory,
                        confidence=pattern.confidence_score,
                        priority=priority,
                        estimated_accuracy=estimated_accuracy,
                        supporting_evidence={
                            "frequency": pattern.frequency,
                            "supporting_transactions": len(pattern.supporting_transactions),
                            "pattern_metadata": pattern.pattern_metadata,
                            "discovery_date": pattern.created_at.isoformat()
                        },
                        creation_reason=f"Generated from {pattern.pattern_type.value} pattern with {pattern.confidence_score:.2f} confidence"
                    )
                    
                    generated_rules.append(rule)
        
        # Sort rules by priority and confidence
        sorted_rules = sorted(
            generated_rules,
            key=lambda r: (r.priority, r.confidence),
            reverse=True
        )
        
        return sorted_rules[:PatternRecognitionLimits.MAX_RULES_GENERATE]
    
    def _convert_pattern_to_rule(self, pattern: RecognizedPattern) -> Tuple[str, str]:
        """Convert a recognized pattern to a rule type and pattern string"""
        
        if pattern.pattern_type == PatternType.VENDOR_PATTERN:
            return "vendor", pattern.pattern_value
        
        elif pattern.pattern_type == PatternType.DESCRIPTION_PATTERN:
            return "keyword", pattern.pattern_value
        
        elif pattern.pattern_type == PatternType.CORRECTION_PATTERN:
            # Determine if it's vendor or description based on metadata
            source_type = pattern.pattern_metadata.get("pattern_source", "desc")
            if source_type == "vendor":
                return "vendor", pattern.pattern_value
            else:
                return "keyword", pattern.pattern_value
        
        elif pattern.pattern_type == PatternType.FREQUENCY_PATTERN:
            return "keyword", pattern.pattern_value
        
        elif pattern.pattern_type == PatternType.AMOUNT_PATTERN:
            # Convert amount range to regex pattern
            amount_range = pattern.pattern_value
            if "-" in amount_range:
                min_amt, max_amt = amount_range.split("-")
                # Create a more flexible pattern - this is simplified
                return "regex", f"amount_range_{min_amt}_{max_amt}"
            
        # For patterns that can't be directly converted to rules
        return None, None
    
    def _calculate_rule_priority(
        self, 
        pattern: RecognizedPattern, 
        user_profile: UserBehaviorProfile
    ) -> int:
        """Calculate priority for generated rule based on pattern strength and user profile"""
        
        base_priority = 5  # Default priority
        
        # Adjust based on confidence
        if pattern.confidence_score >= 0.9:
            base_priority += 3
        elif pattern.confidence_score >= 0.8:
            base_priority += 2
        elif pattern.confidence_score >= 0.7:
            base_priority += 1
        
        # Adjust based on frequency
        if pattern.frequency >= 10:
            base_priority += 2
        elif pattern.frequency >= 5:
            base_priority += 1
        
        # Adjust based on pattern type
        if pattern.pattern_type == PatternType.CORRECTION_PATTERN:
            base_priority += 2  # User corrections are very important
        elif pattern.pattern_type == PatternType.VENDOR_PATTERN:
            base_priority += 1  # Vendor patterns are generally reliable
        
        # Adjust based on user profile
        if pattern.category in user_profile.preferred_categories:
            category_usage = user_profile.preferred_categories[pattern.category]
            if category_usage >= 10:  # Frequently used category
                base_priority += 1
        
        return min(base_priority, 10)  # Cap at 10
    
    def _estimate_rule_accuracy(self, pattern: RecognizedPattern) -> float:
        """Estimate accuracy of rule based on pattern characteristics"""
        
        base_accuracy = pattern.confidence_score
        
        # Adjust based on pattern type reliability
        if pattern.pattern_type == PatternType.VENDOR_PATTERN:
            base_accuracy *= 1.1  # Vendor patterns tend to be more reliable
        elif pattern.pattern_type == PatternType.CORRECTION_PATTERN:
            base_accuracy *= 1.15  # User corrections are highly reliable
        elif pattern.pattern_type == PatternType.FREQUENCY_PATTERN:
            base_accuracy *= 0.9  # Frequency patterns can have exceptions
        
        # Adjust based on supporting evidence
        support_strength = min(pattern.frequency / 10.0, 1.0)
        base_accuracy += (support_strength * 0.05)
        
        return min(base_accuracy, 0.98)  # Cap at 98% to account for edge cases
    
    async def _estimate_accuracy_improvements(
        self, 
        rules: List[PatternRule], 
        transactions: List[Transaction]
    ) -> Dict[str, float]:
        """Estimate accuracy improvements from proposed rules"""
        
        improvements = {
            "overall_accuracy_increase": 0.0,
            "uncategorized_transactions_addressable": 0.0,
            "categorization_speed_improvement": 0.0,
            "rule_coverage": 0.0
        }
        
        if not rules or not transactions:
            return improvements
        
        # Count uncategorized transactions
        uncategorized = [t for t in transactions if not t.is_categorized]
        total_transactions = len(transactions)
        
        # Simulate rule application
        addressable_transactions = 0
        
        for rule in rules:
            # Estimate how many transactions this rule would categorize
            estimated_matches = max(1, rule.supporting_evidence.get("frequency", 1))
            addressable_transactions += estimated_matches
        
        if uncategorized:
            improvements["uncategorized_transactions_addressable"] = min(
                addressable_transactions / len(uncategorized), 1.0
            )
        
        # Calculate overall accuracy increase
        if total_transactions > 0:
            current_accuracy = len([t for t in transactions if t.is_categorized]) / total_transactions
            potential_accuracy = min(current_accuracy + improvements["uncategorized_transactions_addressable"] * 0.5, 1.0)
            improvements["overall_accuracy_increase"] = potential_accuracy - current_accuracy
        
        # Rule coverage
        improvements["rule_coverage"] = min(len(rules) / 20.0, 1.0)  # Assuming 20 rules is good coverage
        
        # Speed improvement (rules are faster than ML)
        improvements["categorization_speed_improvement"] = 0.3 * improvements["rule_coverage"]
        
        return improvements
    
    async def apply_suggested_rules(
        self, 
        rule_ids: List[str], 
        dry_run: bool = True,
        auto_activate: bool = False
    ) -> Dict[str, Any]:
        """Apply suggested pattern rules to actual categorization system"""
        
        start_time = datetime.utcnow()
        
        # Get cached analysis results to find the rules
        suggested_rules = []
        # In production, this would be retrieved from cache/database
        # For now, we'll need to get from last analysis
        
        if dry_run:
            # Simulate rule application
            simulation_results = await self._simulate_rule_application(rule_ids)
            return {
                "dry_run": True,
                "simulation_results": simulation_results,
                "rules_processed": len(rule_ids),
                "estimated_improvements": simulation_results.get("estimated_improvements", {}),
                "warning": "This is a simulation. Set dry_run=false to apply rules."
            }
        
        # Actually create the rules in the database
        created_rules = []
        errors = []
        
        for rule_id in rule_ids:
            try:
                # Find the rule in suggested rules
                pattern_rule = await self._get_cached_suggested_rule(rule_id)
                
                if pattern_rule:
                    # Create actual CategorizationRule
                    db_rule = CategorizationRule(
                        user_id=self.user.id,
                        name=f"Pattern-generated: {pattern_rule.rule_pattern}",
                        pattern=pattern_rule.rule_pattern,
                        pattern_type=pattern_rule.rule_type,
                        category=pattern_rule.category,
                        subcategory=pattern_rule.subcategory,
                        priority=pattern_rule.priority,
                        is_active=auto_activate,
                        created_at=datetime.utcnow()
                    )
                    
                    self.db.add(db_rule)
                    self.db.flush()  # Get ID
                    
                    created_rules.append({
                        "rule_id": rule_id,
                        "db_rule_id": db_rule.id,
                        "pattern": pattern_rule.rule_pattern,
                        "category": pattern_rule.category,
                        "priority": pattern_rule.priority,
                        "active": auto_activate
                    })
                    
                else:
                    errors.append(f"Rule {rule_id} not found in suggested rules")
                    
            except Exception as e:
                errors.append(f"Error creating rule {rule_id}: {str(e)}")
        
        if created_rules:
            self.db.commit()
        
        # Audit log
        self.audit_logger.info(
            f"Applied {len(created_rules)} pattern-generated rules for user {self.user.id}",
            extra={
                "user_id": self.user.id,
                "rules_created": len(created_rules),
                "errors": len(errors),
                "auto_activated": auto_activate
            }
        )
        
        end_time = datetime.utcnow()
        processing_time = int((end_time - start_time).total_seconds() * 1000)
        
        return {
            "dry_run": False,
            "rules_created": len(created_rules),
            "rules_activated": len(created_rules) if auto_activate else 0,
            "errors": errors,
            "created_rules": created_rules,
            "processing_time_ms": processing_time,
            "success": len(errors) == 0
        }
    
    async def get_pattern_analytics(self) -> Dict[str, Any]:
        """Get analytics on pattern recognition performance and user engagement"""
        
        # This would integrate with the analytics system
        # For now, return basic metrics from user profile
        
        user_profile = self._user_profile_cache or await self._build_user_behavior_profile([])
        
        analytics = {
            "user_behavior": {
                "total_manual_corrections": user_profile.total_manual_corrections,
                "categorization_style": user_profile.categorization_style,
                "consistency_score": user_profile.consistency_score,
                "learning_rate": user_profile.learning_rate
            },
            "pattern_discovery": {
                "patterns_in_cache": len(self._pattern_cache),
                "cache_age_minutes": (datetime.utcnow() - self._cache_timestamp).total_seconds() / 60
            },
            "rule_generation": {
                "generation_strategy": self.analysis_config["generation_strategy"].value,
                "min_confidence_threshold": self.analysis_config["min_confidence"]
            }
        }
        
        return analytics
    
    # Helper methods
    
    def _extract_significant_words(self, text: str) -> List[str]:
        """Extract significant words from transaction description"""
        if not text:
            return []
        
        # Remove common financial terms and stop words
        stop_words = {
            'payment', 'purchase', 'transaction', 'debit', 'credit', 'card', 'pos',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'over', 'after'
        }
        
        # Extract words (alphanumeric, 3+ chars)
        words = re.findall(r'\b[a-zA-Z0-9]{3,}\b', text.lower())
        significant = [w for w in words if w not in stop_words]
        
        return significant[:5]  # Top 5 significant words
    
    def _get_amount_range(self, amount: Decimal) -> str:
        """Get amount range category for pattern analysis"""
        amount_abs = abs(amount)
        
        if amount_abs < 10:
            return "0-10"
        elif amount_abs < 25:
            return "10-25"
        elif amount_abs < 50:
            return "25-50"
        elif amount_abs < 100:
            return "50-100"
        elif amount_abs < 250:
            return "100-250"
        elif amount_abs < 500:
            return "250-500"
        elif amount_abs < 1000:
            return "500-1000"
        else:
            return "1000+"
    
    def _get_description_key(self, description: str) -> str:
        """Get normalized description key for frequency analysis"""
        if not description:
            return ""
        
        # Extract key terms (first 2-3 significant words)
        words = self._extract_significant_words(description)
        return " ".join(words[:3])
    
    async def _cache_analysis_results(self, result: PatternAnalysisResult):
        """Cache analysis results for performance"""
        # In production, this would use Redis
        # For now, use in-memory cache
        self._pattern_cache.clear()
        
        for pattern in result.discovered_patterns:
            self._pattern_cache[pattern.pattern_id] = pattern
        
        self._cache_timestamp = datetime.utcnow()
    
    async def _simulate_rule_application(self, rule_ids: List[str]) -> Dict[str, Any]:
        """Simulate rule application for dry run"""
        
        return {
            "estimated_improvements": {
                "transactions_categorized": len(rule_ids) * 5,  # Rough estimate
                "accuracy_increase": min(len(rule_ids) * 0.02, 0.15),  # Max 15% increase
                "processing_speed_increase": "30-50%"
            },
            "rule_coverage": {
                "vendor_rules": len([r for r in rule_ids if "vendor" in r]),
                "keyword_rules": len([r for r in rule_ids if "keyword" in r]),
                "pattern_rules": len(rule_ids)
            }
        }
    
    async def _get_cached_suggested_rule(self, rule_id: str) -> Optional[PatternRule]:
        """Get suggested rule from cache by ID"""
        # In production, this would query cache/database
        # For now, return None as we'd need actual analysis results
        return None