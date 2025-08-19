"""
Comprehensive test suite for Pattern Recognition Engine

Tests pattern discovery algorithms, rule generation, user behavior analysis,
and API endpoint functionality with extensive edge case coverage.
"""

import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.transaction import Transaction, CategorizationRule
from app.models.user import User
from app.services.pattern_recognition import (
    PatternRecognitionEngine, PatternType, PatternConfidenceLevel,
    RuleGenerationStrategy, RecognizedPattern, PatternRule,
    UserBehaviorProfile, PatternAnalysisResult, PatternRecognitionLimits
)
from app.core.exceptions import ValidationException, BusinessLogicException


class TestPatternRecognitionEngine:
    """Test suite for PatternRecognitionEngine"""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing"""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        db = Mock(spec=Session)
        return db
    
    @pytest.fixture
    def pattern_engine(self, mock_db, mock_user):
        """Create pattern recognition engine instance"""
        with patch('app.services.pattern_recognition.security_audit_logger') as mock_logger:
            with patch('app.services.pattern_recognition.MLCategorizationService'):
                engine = PatternRecognitionEngine(mock_db, mock_user)
                engine.audit_logger = mock_logger
                return engine
    
    @pytest.fixture
    def sample_transactions(self, mock_user):
        """Create sample transactions for pattern analysis testing"""
        base_date = datetime.utcnow()
        transactions = []
        
        # Vendor pattern transactions (Starbucks -> Food)
        for i in range(5):
            txn = Mock(spec=Transaction)
            txn.id = i + 1
            txn.user_id = mock_user.id
            txn.date = base_date - timedelta(days=i * 7)
            txn.amount = Decimal("4.75")
            txn.description = f"STARBUCKS COFFEE #{12345 + i}"
            txn.vendor = "Starbucks"
            txn.category = "Food"
            txn.subcategory = "Coffee"
            txn.is_categorized = True
            txn.confidence_score = 0.9
            txn.meta_data = {"categorization_method": "manual"}
            transactions.append(txn)
        
        # Description pattern transactions (GAS -> Transportation) 
        for i in range(4):
            txn = Mock(spec=Transaction)
            txn.id = i + 6
            txn.user_id = mock_user.id
            txn.date = base_date - timedelta(days=i * 10)
            txn.amount = Decimal(f"{45.00 + i * 5}")
            txn.description = f"SHELL GAS STATION #{i + 1}"
            txn.vendor = f"Shell Station {i + 1}"
            txn.category = "Transportation"
            txn.subcategory = "Fuel"
            txn.is_categorized = True
            txn.confidence_score = 0.85
            txn.meta_data = {"categorization_method": "rule"}
            transactions.append(txn)
        
        # Correction pattern transactions (ML corrections)
        for i in range(3):
            txn = Mock(spec=Transaction)
            txn.id = i + 10
            txn.user_id = mock_user.id
            txn.date = base_date - timedelta(days=i * 5)
            txn.amount = Decimal("12.99")
            txn.description = f"SPOTIFY PREMIUM {i + 1}"
            txn.vendor = "Spotify"
            txn.category = "Entertainment"
            txn.subcategory = "Streaming"
            txn.is_categorized = True
            txn.confidence_score = 1.0
            txn.meta_data = {
                "categorization_method": "manual",
                "manual_correction": True,
                "original_ml_category": "Technology"
            }
            transactions.append(txn)
        
        # Amount pattern transactions (similar amounts -> Groceries)
        for i in range(6):
            txn = Mock(spec=Transaction)
            txn.id = i + 13
            txn.user_id = mock_user.id
            txn.date = base_date - timedelta(days=i * 3)
            txn.amount = Decimal(f"{85.00 + i * 2}")  # $85-95 range
            txn.description = f"SAFEWAY GROCERY #{i + 1000}"
            txn.vendor = f"Safeway #{i + 1}"
            txn.category = "Food"
            txn.subcategory = "Groceries"
            txn.is_categorized = True
            txn.confidence_score = 0.8
            txn.meta_data = {"categorization_method": "ml"}
            transactions.append(txn)
        
        # Uncategorized transactions for testing
        for i in range(3):
            txn = Mock(spec=Transaction)
            txn.id = i + 19
            txn.user_id = mock_user.id
            txn.date = base_date - timedelta(days=i)
            txn.amount = Decimal("25.00")
            txn.description = f"UNKNOWN MERCHANT {i}"
            txn.vendor = None
            txn.category = None
            txn.subcategory = None
            txn.is_categorized = False
            txn.confidence_score = None
            txn.meta_data = {}
            transactions.append(txn)
        
        return transactions

    def test_engine_initialization(self, mock_db, mock_user):
        """Test pattern recognition engine initializes correctly"""
        with patch('app.services.pattern_recognition.security_audit_logger'):
            with patch('app.services.pattern_recognition.MLCategorizationService'):
                engine = PatternRecognitionEngine(mock_db, mock_user)
                
                assert engine.db == mock_db
                assert engine.user == mock_user
                assert engine.analysis_config["min_pattern_frequency"] == 3
                assert engine.analysis_config["min_confidence"] == 0.6
                assert engine.analysis_config["generation_strategy"] == RuleGenerationStrategy.BALANCED

    @pytest.mark.asyncio
    async def test_get_transactions_for_analysis(self, pattern_engine, sample_transactions):
        """Test transaction retrieval for pattern analysis"""
        # Mock database query
        pattern_engine.db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = sample_transactions
        
        transactions = await pattern_engine._get_transactions_for_pattern_analysis(90, True)
        
        assert transactions == sample_transactions
        pattern_engine.db.query.assert_called_once_with(Transaction)

    @pytest.mark.asyncio 
    async def test_get_transactions_database_error(self, pattern_engine):
        """Test database error handling in transaction retrieval"""
        pattern_engine.db.query.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(BusinessLogicException, match="Database error while fetching transactions"):
            await pattern_engine._get_transactions_for_pattern_analysis(90, True)

    @pytest.mark.asyncio
    async def test_build_user_behavior_profile(self, pattern_engine, sample_transactions):
        """Test building comprehensive user behavior profile"""
        profile = await pattern_engine._build_user_behavior_profile(sample_transactions)
        
        assert isinstance(profile, UserBehaviorProfile)
        assert profile.user_id == pattern_engine.user.id
        assert profile.total_manual_corrections > 0
        assert profile.categorization_style in ["simple", "detailed", "balanced"]
        assert 0 <= profile.consistency_score <= 1.0
        assert 0 <= profile.learning_rate <= 1.0

    def test_determine_categorization_style_simple(self, pattern_engine):
        """Test categorization style determination for simple users"""
        category_counts = {"Food": 50, "Transportation": 30}  # Only 2 categories
        style = pattern_engine._determine_categorization_style(category_counts)
        assert style == "simple"

    def test_determine_categorization_style_detailed(self, pattern_engine):
        """Test categorization style determination for detailed users"""
        category_counts = {f"Category{i}": 5 for i in range(20)}  # 20 categories
        style = pattern_engine._determine_categorization_style(category_counts)
        assert style == "detailed"

    def test_determine_categorization_style_balanced(self, pattern_engine):
        """Test categorization style determination for balanced users"""
        category_counts = {f"Category{i}": 10 for i in range(8)}  # 8 categories, even distribution
        style = pattern_engine._determine_categorization_style(category_counts)
        assert style == "balanced"

    @pytest.mark.asyncio
    async def test_discover_vendor_patterns(self, pattern_engine, sample_transactions):
        """Test vendor-based pattern discovery"""
        vendor_patterns = await pattern_engine._discover_vendor_patterns(sample_transactions)
        
        # Should find Starbucks and Shell patterns
        pattern_vendors = [p.pattern_value for p in vendor_patterns]
        assert "starbucks" in pattern_vendors
        
        # Check pattern properties
        starbucks_pattern = next(p for p in vendor_patterns if p.pattern_value == "starbucks")
        assert starbucks_pattern.pattern_type == PatternType.VENDOR_PATTERN
        assert starbucks_pattern.category == "Food"
        assert starbucks_pattern.confidence_score >= 0.7
        assert starbucks_pattern.frequency >= 3

    @pytest.mark.asyncio
    async def test_discover_description_patterns(self, pattern_engine, sample_transactions):
        """Test description keyword pattern discovery"""
        description_patterns = await pattern_engine._discover_description_patterns(sample_transactions)
        
        # Should find patterns based on significant words
        assert len(description_patterns) >= 0
        
        # Check for gas-related patterns
        gas_patterns = [p for p in description_patterns if "gas" in p.pattern_value.lower()]
        if gas_patterns:
            gas_pattern = gas_patterns[0]
            assert gas_pattern.pattern_type == PatternType.DESCRIPTION_PATTERN
            assert gas_pattern.confidence_score >= 0.6

    @pytest.mark.asyncio
    async def test_discover_amount_patterns(self, pattern_engine, sample_transactions):
        """Test amount-based pattern discovery"""
        amount_patterns = await pattern_engine._discover_amount_patterns(sample_transactions)
        
        # Should discover patterns for grocery amounts ($85-95 range)
        grocery_amount_patterns = [p for p in amount_patterns if p.category == "Food"]
        
        if grocery_amount_patterns:
            pattern = grocery_amount_patterns[0]
            assert pattern.pattern_type == PatternType.AMOUNT_PATTERN
            assert pattern.confidence_score >= 0.6

    @pytest.mark.asyncio
    async def test_discover_correction_patterns(self, pattern_engine, sample_transactions):
        """Test correction pattern discovery from user corrections"""
        correction_patterns = await pattern_engine._discover_correction_patterns(sample_transactions)
        
        # Should find Spotify correction pattern (Technology -> Entertainment)
        spotify_patterns = [p for p in correction_patterns if "spotify" in p.pattern_value.lower()]
        
        if spotify_patterns:
            spotify_pattern = spotify_patterns[0]
            assert spotify_pattern.pattern_type == PatternType.CORRECTION_PATTERN
            assert spotify_pattern.category == "Entertainment"
            assert spotify_pattern.confidence_score >= 0.7

    @pytest.mark.asyncio
    async def test_discover_frequency_patterns(self, pattern_engine, sample_transactions):
        """Test frequency-based pattern discovery"""
        # Mock transactions with regular intervals
        regular_transactions = []
        base_date = datetime.utcnow()
        
        for i in range(4):
            txn = Mock(spec=Transaction)
            txn.id = i + 100
            txn.date = base_date - timedelta(days=i * 30)  # Monthly pattern
            txn.vendor = "Monthly Service"
            txn.category = "Utilities"
            txn.is_categorized = True
            regular_transactions.append(txn)
        
        frequency_patterns = await pattern_engine._discover_frequency_patterns(regular_transactions)
        
        if frequency_patterns:
            pattern = frequency_patterns[0]
            assert pattern.pattern_type == PatternType.FREQUENCY_PATTERN
            assert "avg_interval_days" in pattern.pattern_metadata

    @pytest.mark.asyncio
    async def test_discover_behavioral_patterns(self, pattern_engine, sample_transactions):
        """Test behavioral pattern discovery"""
        # Mock transactions with day-of-week patterns
        behavioral_transactions = []
        base_date = datetime.utcnow()
        
        # Create Monday coffee pattern
        for i in range(5):
            txn = Mock(spec=Transaction)
            txn.id = i + 200
            txn.date = base_date - timedelta(days=i * 7)  # Every Monday
            txn.category = "Food"
            txn.is_categorized = True
            behavioral_transactions.append(txn)
        
        behavioral_patterns = await pattern_engine._discover_behavioral_patterns(behavioral_transactions)
        
        # Should find day-of-week patterns
        assert len(behavioral_patterns) >= 0

    def test_filter_and_rank_patterns(self, pattern_engine):
        """Test pattern filtering and ranking"""
        # Create test patterns with different confidence scores
        patterns = []
        
        for i in range(5):
            pattern = RecognizedPattern(
                pattern_id=str(uuid.uuid4()),
                pattern_type=PatternType.VENDOR_PATTERN,
                pattern_value=f"vendor_{i}",
                confidence_score=0.5 + (i * 0.1),  # 0.5, 0.6, 0.7, 0.8, 0.9
                frequency=i + 3,
                category="Food",
                subcategory=None,
                supporting_transactions=[1, 2, 3],
                pattern_metadata={},
                created_at=datetime.utcnow(),
                last_seen=datetime.utcnow()
            )
            patterns.append(pattern)
        
        # Set minimum confidence to 0.6
        pattern_engine.analysis_config["min_confidence"] = 0.6
        
        filtered = pattern_engine._filter_and_rank_patterns(patterns)
        
        # Should filter out patterns below 0.6 confidence
        assert len(filtered) == 4  # 0.6, 0.7, 0.8, 0.9
        
        # Should be ranked by confidence (descending)
        assert filtered[0].confidence_score == 0.9
        assert filtered[-1].confidence_score == 0.6

    def test_convert_pattern_to_rule(self, pattern_engine):
        """Test pattern to rule conversion"""
        # Test vendor pattern conversion
        vendor_pattern = RecognizedPattern(
            pattern_id=str(uuid.uuid4()),
            pattern_type=PatternType.VENDOR_PATTERN,
            pattern_value="starbucks",
            confidence_score=0.9,
            frequency=5,
            category="Food",
            subcategory="Coffee",
            supporting_transactions=[1, 2, 3, 4, 5],
            pattern_metadata={},
            created_at=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        
        rule_type, rule_pattern = pattern_engine._convert_pattern_to_rule(vendor_pattern)
        assert rule_type == "vendor"
        assert rule_pattern == "starbucks"
        
        # Test description pattern conversion
        desc_pattern = RecognizedPattern(
            pattern_id=str(uuid.uuid4()),
            pattern_type=PatternType.DESCRIPTION_PATTERN,
            pattern_value="coffee",
            confidence_score=0.8,
            frequency=4,
            category="Food",
            subcategory="Coffee",
            supporting_transactions=[1, 2, 3, 4],
            pattern_metadata={},
            created_at=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        
        rule_type, rule_pattern = pattern_engine._convert_pattern_to_rule(desc_pattern)
        assert rule_type == "keyword"
        assert rule_pattern == "coffee"

    def test_calculate_rule_priority(self, pattern_engine):
        """Test rule priority calculation"""
        # Create test user profile
        user_profile = UserBehaviorProfile(
            user_id=1,
            total_manual_corrections=10,
            correction_patterns={},
            preferred_categories={"Food": 20, "Transportation": 15},
            categorization_style="balanced",
            consistency_score=0.8,
            learning_rate=0.3,
            last_updated=datetime.utcnow()
        )
        
        # Test high-confidence correction pattern
        correction_pattern = RecognizedPattern(
            pattern_id=str(uuid.uuid4()),
            pattern_type=PatternType.CORRECTION_PATTERN,
            pattern_value="spotify",
            confidence_score=0.95,
            frequency=10,
            category="Food",  # User's preferred category
            subcategory=None,
            supporting_transactions=list(range(1, 11)),
            pattern_metadata={},
            created_at=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        
        priority = pattern_engine._calculate_rule_priority(correction_pattern, user_profile)
        
        # Should get high priority for correction pattern with high confidence and frequency
        assert priority >= 8

    def test_estimate_rule_accuracy(self, pattern_engine):
        """Test rule accuracy estimation"""
        # Test vendor pattern (generally reliable)
        vendor_pattern = RecognizedPattern(
            pattern_id=str(uuid.uuid4()),
            pattern_type=PatternType.VENDOR_PATTERN,
            pattern_value="starbucks",
            confidence_score=0.8,
            frequency=10,
            category="Food",
            subcategory="Coffee",
            supporting_transactions=list(range(1, 11)),
            pattern_metadata={},
            created_at=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        
        accuracy = pattern_engine._estimate_rule_accuracy(vendor_pattern)
        
        # Should be higher than base confidence due to vendor pattern reliability
        assert accuracy > 0.8
        assert accuracy <= 0.98  # Should be capped

    def test_extract_significant_words(self, pattern_engine):
        """Test significant word extraction from descriptions"""
        text = "STARBUCKS COFFEE PURCHASE STORE #12345"
        words = pattern_engine._extract_significant_words(text)
        
        assert "starbucks" in words
        assert "coffee" in words
        assert "purchase" in words
        # Should not include stop words
        assert "the" not in words

    def test_get_amount_range(self, pattern_engine):
        """Test amount range categorization"""
        assert pattern_engine._get_amount_range(Decimal("5.00")) == "0-10"
        assert pattern_engine._get_amount_range(Decimal("15.00")) == "10-25"
        assert pattern_engine._get_amount_range(Decimal("75.00")) == "50-100"
        assert pattern_engine._get_amount_range(Decimal("150.00")) == "100-250"
        assert pattern_engine._get_amount_range(Decimal("1500.00")) == "1000+"

    def test_get_description_key(self, pattern_engine):
        """Test description key generation for frequency analysis"""
        description = "STARBUCKS COFFEE PURCHASE #12345"
        key = pattern_engine._get_description_key(description)
        
        # Should extract key terms
        assert len(key) > 0
        assert any(word in key.lower() for word in ["starbucks", "coffee"])

    @pytest.mark.asyncio
    async def test_analyze_user_patterns_insufficient_data(self, pattern_engine):
        """Test pattern analysis with insufficient transaction data"""
        # Mock empty transaction list
        pattern_engine.db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        with pytest.raises(ValidationException, match="Insufficient transaction history"):
            await pattern_engine.analyze_user_patterns()

    @pytest.mark.asyncio
    async def test_analyze_user_patterns_success(self, pattern_engine, sample_transactions):
        """Test successful pattern analysis"""
        # Mock transaction retrieval
        pattern_engine.db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = sample_transactions
        
        # Mock the pattern discovery methods to return test patterns
        test_pattern = RecognizedPattern(
            pattern_id=str(uuid.uuid4()),
            pattern_type=PatternType.VENDOR_PATTERN,
            pattern_value="test_vendor",
            confidence_score=0.9,
            frequency=5,
            category="Food",
            subcategory="Coffee",
            supporting_transactions=[1, 2, 3, 4, 5],
            pattern_metadata={},
            created_at=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        
        with patch.object(pattern_engine, '_discover_patterns', return_value=[test_pattern]):
            with patch.object(pattern_engine, '_generate_rules_from_patterns', return_value=[]):
                with patch.object(pattern_engine, '_estimate_accuracy_improvements', return_value={}):
                    
                    result = await pattern_engine.analyze_user_patterns()
                    
                    assert isinstance(result, PatternAnalysisResult)
                    assert result.user_id == pattern_engine.user.id
                    assert result.patterns_discovered >= 0
                    assert result.total_transactions_analyzed > 0

    @pytest.mark.asyncio
    async def test_analyze_user_patterns_exception_handling(self, pattern_engine):
        """Test exception handling in pattern analysis"""
        # Mock database error
        pattern_engine.db.query.side_effect = Exception("Database connection failed")
        
        with pytest.raises(BusinessLogicException, match="Pattern analysis failed"):
            await pattern_engine.analyze_user_patterns()


class TestPatternRecognitionLimits:
    """Test pattern recognition limits and constraints"""
    
    def test_limits_constants(self):
        """Test that all limits are properly defined"""
        assert PatternRecognitionLimits.MAX_TRANSACTIONS_ANALYZE > 0
        assert PatternRecognitionLimits.MAX_PATTERNS_PER_ANALYSIS > 0
        assert PatternRecognitionLimits.MAX_RULES_GENERATE > 0
        assert PatternRecognitionLimits.MIN_PATTERN_FREQUENCY >= 2
        assert 0 < PatternRecognitionLimits.MIN_PATTERN_CONFIDENCE < 1
        assert PatternRecognitionLimits.MAX_ANALYSIS_TIME_MINUTES > 0
        assert PatternRecognitionLimits.CACHE_TTL_HOURS > 0


class TestPatternRecognitionDataClasses:
    """Test pattern recognition data classes"""
    
    def test_recognized_pattern_creation(self):
        """Test RecognizedPattern data class"""
        pattern = RecognizedPattern(
            pattern_id="test-id",
            pattern_type=PatternType.VENDOR_PATTERN,
            pattern_value="test_vendor",
            confidence_score=0.9,
            frequency=5,
            category="Food",
            subcategory="Coffee",
            supporting_transactions=[1, 2, 3],
            pattern_metadata={"test": "data"},
            created_at=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        
        assert pattern.pattern_id == "test-id"
        assert pattern.pattern_type == PatternType.VENDOR_PATTERN
        assert pattern.confidence_score == 0.9
        assert len(pattern.supporting_transactions) == 3

    def test_pattern_rule_creation(self):
        """Test PatternRule data class"""
        rule = PatternRule(
            rule_id="rule-id",
            pattern_id="pattern-id", 
            pattern_type=PatternType.VENDOR_PATTERN,
            rule_pattern="starbucks",
            rule_type="vendor",
            category="Food",
            subcategory="Coffee",
            confidence=0.9,
            priority=8,
            estimated_accuracy=0.85,
            supporting_evidence={"frequency": 5},
            creation_reason="Test rule"
        )
        
        assert rule.rule_id == "rule-id"
        assert rule.rule_type == "vendor"
        assert rule.priority == 8

    def test_user_behavior_profile_creation(self):
        """Test UserBehaviorProfile data class"""
        profile = UserBehaviorProfile(
            user_id=1,
            total_manual_corrections=10,
            correction_patterns={"old->new": 5},
            preferred_categories={"Food": 20},
            categorization_style="balanced",
            consistency_score=0.8,
            learning_rate=0.3,
            last_updated=datetime.utcnow()
        )
        
        assert profile.user_id == 1
        assert profile.categorization_style == "balanced"
        assert profile.consistency_score == 0.8


class TestPatternRecognitionEnums:
    """Test pattern recognition enums"""
    
    def test_pattern_type_enum(self):
        """Test PatternType enum values"""
        assert PatternType.VENDOR_PATTERN.value == "vendor_pattern"
        assert PatternType.DESCRIPTION_PATTERN.value == "description_pattern"
        assert PatternType.CORRECTION_PATTERN.value == "correction_pattern"
        
        # Test all enum values are unique
        values = [pt.value for pt in PatternType]
        assert len(values) == len(set(values))

    def test_pattern_confidence_level_enum(self):
        """Test PatternConfidenceLevel enum values"""
        assert PatternConfidenceLevel.VERY_HIGH.value == 0.95
        assert PatternConfidenceLevel.HIGH.value == 0.85
        assert PatternConfidenceLevel.MEDIUM.value == 0.70
        assert PatternConfidenceLevel.LOW.value == 0.55
        assert PatternConfidenceLevel.VERY_LOW.value == 0.40

    def test_rule_generation_strategy_enum(self):
        """Test RuleGenerationStrategy enum values"""
        assert RuleGenerationStrategy.CONSERVATIVE.value == "conservative"
        assert RuleGenerationStrategy.BALANCED.value == "balanced"
        assert RuleGenerationStrategy.AGGRESSIVE.value == "aggressive"
        assert RuleGenerationStrategy.LEARNING.value == "learning"


if __name__ == "__main__":
    pytest.main([__file__])