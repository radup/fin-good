"""
Transaction Duplicate Detection Service

Advanced duplicate transaction detection using fuzzy matching algorithms,
confidence-based scoring, and automated merge suggestions with user review workflow.
"""

from typing import List, Dict, Any, Optional, Set, Tuple, Union
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from sqlalchemy.exc import SQLAlchemyError
import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import difflib
import re
from collections import defaultdict

from app.models.transaction import Transaction
from app.models.user import User
from app.core.exceptions import ValidationException, BusinessLogicException
from app.core.security_utils import input_sanitizer
from app.core.audit_logger import security_audit_logger
from app.services.transaction_operations import TransactionBulkOperations, BulkUpdateRequest, BulkOperationType


class DuplicateConfidenceLevel(Enum):
    """Confidence levels for duplicate detection"""
    VERY_LOW = "very_low"      # 0.0 - 0.3
    LOW = "low"                # 0.3 - 0.5
    MEDIUM = "medium"          # 0.5 - 0.7
    HIGH = "high"              # 0.7 - 0.85
    VERY_HIGH = "very_high"    # 0.85 - 1.0


class DuplicateMatchType(Enum):
    """Types of duplicate matches"""
    EXACT = "exact"                    # Identical transactions
    NEAR_EXACT = "near_exact"         # Very similar (amount + date + vendor)
    FUZZY = "fuzzy"                   # Similar description/vendor
    AMOUNT_DATE = "amount_date"       # Same amount and date
    VENDOR_AMOUNT = "vendor_amount"   # Same vendor and amount
    DESCRIPTION = "description"        # Similar description


class DuplicateReviewStatus(Enum):
    """Status of duplicate review"""
    PENDING = "pending"
    REVIEWED = "reviewed"
    MERGED = "merged"
    DISMISSED = "dismissed"
    AUTO_MERGED = "auto_merged"


# Configuration constants
class DuplicateDetectionLimits:
    MIN_CONFIDENCE_THRESHOLD = 0.5      # Minimum confidence to suggest as duplicate
    AUTO_MERGE_THRESHOLD = 0.95         # Auto-merge threshold for very high confidence
    MAX_DUPLICATES_PER_SCAN = 10000     # Maximum duplicates to process in one scan
    MAX_COMPARISON_DAYS = 90            # Maximum days to look back for duplicates
    MIN_AMOUNT_THRESHOLD = Decimal('0.01')  # Minimum amount to consider for duplicates
    MAX_DESCRIPTION_DISTANCE = 0.8      # Maximum string distance for description matching


@dataclass
class DuplicateMatch:
    """Information about a potential duplicate match"""
    primary_transaction_id: int
    duplicate_transaction_id: int
    confidence_score: float
    match_type: DuplicateMatchType
    match_reasons: List[str]
    suggested_action: str
    primary_transaction: Optional[Dict[str, Any]] = None
    duplicate_transaction: Optional[Dict[str, Any]] = None


@dataclass
class DuplicateGroup:
    """Group of potentially duplicate transactions"""
    group_id: str
    transactions: List[Dict[str, Any]]
    confidence_score: float
    primary_transaction_id: int
    duplicate_count: int
    total_amount: Decimal
    date_range: Dict[str, str]
    review_status: DuplicateReviewStatus = DuplicateReviewStatus.PENDING


@dataclass
class DuplicateDetectionResult:
    """Result of duplicate detection scan"""
    scan_id: str
    user_id: int
    total_transactions_scanned: int
    potential_duplicates_found: int
    duplicate_groups: List[DuplicateGroup]
    high_confidence_matches: int
    auto_merge_candidates: int
    total_amount_affected: Decimal
    scan_duration_ms: int
    started_at: datetime
    completed_at: datetime


class DuplicateDetectionService:
    """
    Advanced duplicate detection service using multiple matching algorithms
    with confidence scoring and automated merge suggestions.
    """
    
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.audit_logger = security_audit_logger
        
        # Initialize fuzzy matching components
        self._stop_words = {
            'payment', 'debit', 'credit', 'card', 'transaction', 'purchase',
            'pos', 'atm', 'transfer', 'withdrawal', 'deposit', 'fee',
            'charge', 'refund', 'return', 'pending', 'auth', 'hold'
        }
        
    async def scan_for_duplicates(
        self, 
        date_range_days: int = 30,
        min_confidence: float = DuplicateDetectionLimits.MIN_CONFIDENCE_THRESHOLD,
        include_reviewed: bool = False
    ) -> DuplicateDetectionResult:
        """
        Scan for potential duplicate transactions using multiple algorithms
        
        Args:
            date_range_days: Number of days to look back for duplicates
            min_confidence: Minimum confidence score to include in results
            include_reviewed: Include previously reviewed duplicates
            
        Returns:
            DuplicateDetectionResult with all potential duplicates found
        """
        scan_id = f"dup_scan_{self.user.id}_{datetime.utcnow().isoformat()}"
        start_time = datetime.utcnow()
        
        self.audit_logger.info(
            f"Starting duplicate detection scan: {scan_id}",
            extra={
                "scan_id": scan_id,
                "user_id": self.user.id,
                "date_range_days": date_range_days,
                "min_confidence": min_confidence
            }
        )
        
        try:
            # Get transactions to analyze
            cutoff_date = datetime.utcnow() - timedelta(days=date_range_days)
            transactions = await self._get_transactions_for_analysis(cutoff_date)
            
            if not transactions:
                return DuplicateDetectionResult(
                    scan_id=scan_id,
                    user_id=self.user.id,
                    total_transactions_scanned=0,
                    potential_duplicates_found=0,
                    duplicate_groups=[],
                    high_confidence_matches=0,
                    auto_merge_candidates=0,
                    total_amount_affected=Decimal('0.00'),
                    scan_duration_ms=0,
                    started_at=start_time,
                    completed_at=datetime.utcnow()
                )
            
            # Find duplicate matches using multiple algorithms
            duplicate_matches = await self._find_duplicate_matches(transactions, min_confidence)
            
            # Group duplicates and create duplicate groups
            duplicate_groups = await self._create_duplicate_groups(duplicate_matches, transactions)
            
            # Calculate statistics
            high_confidence_count = sum(1 for group in duplicate_groups 
                                      if group.confidence_score >= 0.7)
            auto_merge_count = sum(1 for group in duplicate_groups 
                                 if group.confidence_score >= DuplicateDetectionLimits.AUTO_MERGE_THRESHOLD)
            total_amount = sum(group.total_amount for group in duplicate_groups)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            result = DuplicateDetectionResult(
                scan_id=scan_id,
                user_id=self.user.id,
                total_transactions_scanned=len(transactions),
                potential_duplicates_found=len(duplicate_groups),
                duplicate_groups=duplicate_groups,
                high_confidence_matches=high_confidence_count,
                auto_merge_candidates=auto_merge_count,
                total_amount_affected=total_amount,
                scan_duration_ms=duration_ms,
                started_at=start_time,
                completed_at=end_time
            )
            
            self.audit_logger.info(
                f"Duplicate detection scan completed: {scan_id}",
                extra={
                    "scan_id": scan_id,
                    "duplicates_found": len(duplicate_groups),
                    "high_confidence_matches": high_confidence_count,
                    "auto_merge_candidates": auto_merge_count,
                    "duration_ms": duration_ms
                }
            )
            
            return result
            
        except Exception as e:
            self.audit_logger.error(
                f"Duplicate detection scan failed: {scan_id}",
                extra={
                    "scan_id": scan_id,
                    "error": str(e),
                    "user_id": self.user.id
                }
            )
            raise BusinessLogicException(f"Failed to scan for duplicates: {str(e)}")
    
    async def _get_transactions_for_analysis(self, cutoff_date: datetime) -> List[Transaction]:
        """Get transactions for duplicate analysis with user isolation"""
        try:
            transactions = self.db.query(Transaction).filter(
                and_(
                    Transaction.user_id == self.user.id,
                    Transaction.date >= cutoff_date,
                    Transaction.amount.isnot(None),
                    func.abs(Transaction.amount) >= DuplicateDetectionLimits.MIN_AMOUNT_THRESHOLD
                )
            ).order_by(Transaction.date.desc()).limit(
                DuplicateDetectionLimits.MAX_DUPLICATES_PER_SCAN
            ).all()
            
            return transactions
            
        except SQLAlchemyError as e:
            raise BusinessLogicException(f"Database error while fetching transactions: {str(e)}")
    
    async def _find_duplicate_matches(
        self, 
        transactions: List[Transaction], 
        min_confidence: float
    ) -> List[DuplicateMatch]:
        """Find potential duplicate matches using multiple algorithms"""
        matches = []
        
        # Sort transactions by date for efficient comparison
        sorted_transactions = sorted(transactions, key=lambda t: t.date)
        
        for i, txn1 in enumerate(sorted_transactions):
            for j, txn2 in enumerate(sorted_transactions[i+1:], i+1):
                # Skip if transactions are too far apart
                date_diff = abs((txn1.date - txn2.date).days)
                if date_diff > 7:  # Only compare transactions within a week
                    continue
                
                # Calculate duplicate confidence using multiple algorithms
                confidence_score, match_type, reasons = await self._calculate_duplicate_confidence(
                    txn1, txn2
                )
                
                if confidence_score >= min_confidence:
                    match = DuplicateMatch(
                        primary_transaction_id=txn1.id,
                        duplicate_transaction_id=txn2.id,
                        confidence_score=confidence_score,
                        match_type=match_type,
                        match_reasons=reasons,
                        suggested_action=self._get_suggested_action(confidence_score),
                        primary_transaction=self._transaction_to_dict(txn1),
                        duplicate_transaction=self._transaction_to_dict(txn2)
                    )
                    matches.append(match)
        
        return matches
    
    async def _calculate_duplicate_confidence(
        self, 
        txn1: Transaction, 
        txn2: Transaction
    ) -> Tuple[float, DuplicateMatchType, List[str]]:
        """Calculate confidence score for potential duplicate using multiple factors"""
        reasons = []
        scores = {}
        
        # 1. Exact match check
        if (txn1.amount == txn2.amount and 
            txn1.date.date() == txn2.date.date() and
            txn1.description == txn2.description and
            txn1.vendor == txn2.vendor):
            return 1.0, DuplicateMatchType.EXACT, ["Exact match on all fields"]
        
        # 2. Amount comparison (weight: 0.3)
        if txn1.amount == txn2.amount:
            scores['amount'] = 1.0
            reasons.append("Identical amounts")
        else:
            # Allow small differences for rounding
            diff_ratio = abs(txn1.amount - txn2.amount) / max(abs(txn1.amount), abs(txn2.amount))
            if diff_ratio <= 0.01:  # 1% difference
                scores['amount'] = 0.9
                reasons.append("Very similar amounts (within 1%)")
            elif diff_ratio <= 0.05:  # 5% difference  
                scores['amount'] = 0.7
                reasons.append("Similar amounts (within 5%)")
            else:
                scores['amount'] = 0.0
        
        # 3. Date comparison (weight: 0.2)
        date_diff = abs((txn1.date - txn2.date).days)
        if date_diff == 0:
            scores['date'] = 1.0
            reasons.append("Same date")
        elif date_diff == 1:
            scores['date'] = 0.8
            reasons.append("1 day difference")
        elif date_diff <= 3:
            scores['date'] = 0.6
            reasons.append("Within 3 days")
        else:
            scores['date'] = max(0, 1 - (date_diff / 7))  # Decay over a week
        
        # 4. Vendor comparison (weight: 0.25)
        vendor_score = self._calculate_string_similarity(
            txn1.vendor or "", txn2.vendor or ""
        )
        scores['vendor'] = vendor_score
        if vendor_score >= 0.9:
            reasons.append("Very similar vendors")
        elif vendor_score >= 0.7:
            reasons.append("Similar vendors")
        
        # 5. Description comparison (weight: 0.25)
        desc_score = self._calculate_string_similarity(
            txn1.description or "", txn2.description or ""
        )
        scores['description'] = desc_score
        if desc_score >= 0.9:
            reasons.append("Very similar descriptions")
        elif desc_score >= 0.7:
            reasons.append("Similar descriptions")
        
        # Calculate weighted confidence score
        weights = {
            'amount': 0.3,
            'date': 0.2, 
            'vendor': 0.25,
            'description': 0.25
        }
        
        confidence = sum(scores[factor] * weights[factor] for factor in weights)
        
        # Determine match type based on highest scoring factors
        if scores.get('amount', 0) >= 0.9 and scores.get('date', 0) >= 0.8:
            if scores.get('vendor', 0) >= 0.8:
                match_type = DuplicateMatchType.NEAR_EXACT
            else:
                match_type = DuplicateMatchType.AMOUNT_DATE
        elif scores.get('vendor', 0) >= 0.8 and scores.get('amount', 0) >= 0.9:
            match_type = DuplicateMatchType.VENDOR_AMOUNT
        elif scores.get('description', 0) >= 0.8:
            match_type = DuplicateMatchType.DESCRIPTION
        else:
            match_type = DuplicateMatchType.FUZZY
        
        return confidence, match_type, reasons
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using multiple algorithms"""
        if not str1 or not str2:
            return 0.0 if str1 != str2 else 1.0
        
        # Normalize strings
        str1_norm = self._normalize_string(str1)
        str2_norm = self._normalize_string(str2)
        
        if str1_norm == str2_norm:
            return 1.0
        
        # Use difflib for sequence matching
        sequence_ratio = difflib.SequenceMatcher(None, str1_norm, str2_norm).ratio()
        
        # Use Levenshtein-like distance for character-level similarity
        char_ratio = self._levenshtein_similarity(str1_norm, str2_norm)
        
        # Use token-based similarity for word-level matching
        token_ratio = self._token_similarity(str1_norm, str2_norm)
        
        # Weighted combination of similarity measures
        combined_score = (
            sequence_ratio * 0.4 + 
            char_ratio * 0.3 + 
            token_ratio * 0.3
        )
        
        return min(1.0, combined_score)
    
    def _normalize_string(self, s: str) -> str:
        """Normalize string for comparison"""
        # Convert to lowercase and remove extra whitespace
        s = s.lower().strip()
        
        # Remove common payment prefixes/suffixes
        s = re.sub(r'^(pos\s+|card\s+|debit\s+|credit\s+)', '', s)
        s = re.sub(r'\s+(pending|auth|hold)$', '', s)
        
        # Remove special characters except spaces and alphanumeric
        s = re.sub(r'[^\w\s]', ' ', s)
        
        # Remove extra whitespace
        s = ' '.join(s.split())
        
        return s
    
    def _levenshtein_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity using Levenshtein distance"""
        if len(str1) == 0:
            return 0.0 if len(str2) > 0 else 1.0
        if len(str2) == 0:
            return 0.0
        
        # Create matrix
        matrix = [[0] * (len(str2) + 1) for _ in range(len(str1) + 1)]
        
        # Initialize first row and column
        for i in range(len(str1) + 1):
            matrix[i][0] = i
        for j in range(len(str2) + 1):
            matrix[0][j] = j
        
        # Fill matrix
        for i in range(1, len(str1) + 1):
            for j in range(1, len(str2) + 1):
                cost = 0 if str1[i-1] == str2[j-1] else 1
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # deletion
                    matrix[i][j-1] + 1,      # insertion  
                    matrix[i-1][j-1] + cost  # substitution
                )
        
        distance = matrix[len(str1)][len(str2)]
        max_length = max(len(str1), len(str2))
        
        return 1.0 - (distance / max_length)
    
    def _token_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity based on common tokens"""
        tokens1 = set(word for word in str1.split() if word not in self._stop_words)
        tokens2 = set(word for word in str2.split() if word not in self._stop_words)
        
        if not tokens1 and not tokens2:
            return 1.0
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0
    
    async def _create_duplicate_groups(
        self, 
        matches: List[DuplicateMatch],
        transactions: List[Transaction]
    ) -> List[DuplicateGroup]:
        """Group duplicate matches into logical groups"""
        # Create transaction lookup
        txn_lookup = {txn.id: txn for txn in transactions}
        
        # Group matches by connected components
        groups = []
        processed_txns = set()
        
        # Sort matches by confidence (highest first)
        sorted_matches = sorted(matches, key=lambda m: m.confidence_score, reverse=True)
        
        for match in sorted_matches:
            primary_id = match.primary_transaction_id
            duplicate_id = match.duplicate_transaction_id
            
            # Skip if already processed
            if primary_id in processed_txns and duplicate_id in processed_txns:
                continue
            
            # Find existing group that contains either transaction
            target_group = None
            for group in groups:
                group_txn_ids = [txn['id'] for txn in group.transactions]
                if primary_id in group_txn_ids or duplicate_id in group_txn_ids:
                    target_group = group
                    break
            
            if target_group:
                # Add transactions to existing group
                if primary_id not in [txn['id'] for txn in target_group.transactions]:
                    if primary_id in txn_lookup:
                        target_group.transactions.append(
                            self._transaction_to_dict(txn_lookup[primary_id])
                        )
                if duplicate_id not in [txn['id'] for txn in target_group.transactions]:
                    if duplicate_id in txn_lookup:
                        target_group.transactions.append(
                            self._transaction_to_dict(txn_lookup[duplicate_id])
                        )
            else:
                # Create new group
                group_transactions = []
                if primary_id in txn_lookup:
                    group_transactions.append(self._transaction_to_dict(txn_lookup[primary_id]))
                if duplicate_id in txn_lookup:
                    group_transactions.append(self._transaction_to_dict(txn_lookup[duplicate_id]))
                
                if group_transactions:
                    group = DuplicateGroup(
                        group_id=f"dup_group_{len(groups)}_{datetime.utcnow().isoformat()}",
                        transactions=group_transactions,
                        confidence_score=match.confidence_score,
                        primary_transaction_id=primary_id,
                        duplicate_count=len(group_transactions),
                        total_amount=sum(Decimal(str(txn['amount'])) for txn in group_transactions),
                        date_range=self._calculate_date_range(group_transactions)
                    )
                    groups.append(group)
            
            processed_txns.add(primary_id)
            processed_txns.add(duplicate_id)
        
        # Update group statistics
        for group in groups:
            group.duplicate_count = len(group.transactions)
            group.total_amount = sum(Decimal(str(txn['amount'])) for txn in group.transactions)
            group.date_range = self._calculate_date_range(group.transactions)
        
        return groups
    
    def _transaction_to_dict(self, transaction: Transaction) -> Dict[str, Any]:
        """Convert transaction to dictionary for serialization"""
        return {
            'id': transaction.id,
            'date': transaction.date.isoformat(),
            'amount': str(transaction.amount),
            'description': transaction.description,
            'vendor': transaction.vendor,
            'category': transaction.category,
            'subcategory': transaction.subcategory,
            'is_categorized': transaction.is_categorized,
            'confidence_score': transaction.confidence_score or 0.0
        }
    
    def _calculate_date_range(self, transactions: List[Dict[str, Any]]) -> Dict[str, str]:
        """Calculate date range for a group of transactions"""
        dates = [datetime.fromisoformat(txn['date']) for txn in transactions]
        return {
            'start_date': min(dates).isoformat(),
            'end_date': max(dates).isoformat()
        }
    
    def _get_suggested_action(self, confidence_score: float) -> str:
        """Get suggested action based on confidence score"""
        if confidence_score >= DuplicateDetectionLimits.AUTO_MERGE_THRESHOLD:
            return "auto_merge"
        elif confidence_score >= 0.8:
            return "review_for_merge"
        elif confidence_score >= 0.6:
            return "manual_review"
        else:
            return "flag_for_attention"
    
    async def auto_merge_high_confidence_duplicates(
        self, 
        duplicate_groups: List[DuplicateGroup],
        min_auto_merge_confidence: float = DuplicateDetectionLimits.AUTO_MERGE_THRESHOLD
    ) -> Dict[str, Any]:
        """Automatically merge high-confidence duplicate groups"""
        merged_groups = []
        merge_errors = []
        
        for group in duplicate_groups:
            if group.confidence_score >= min_auto_merge_confidence:
                try:
                    result = await self._merge_duplicate_group(group, auto_merge=True)
                    merged_groups.append({
                        'group_id': group.group_id,
                        'merged_transaction_id': result['primary_transaction_id'],
                        'deleted_transaction_ids': result['deleted_transaction_ids'],
                        'confidence_score': group.confidence_score
                    })
                    
                    self.audit_logger.info(
                        f"Auto-merged duplicate group: {group.group_id}",
                        extra={
                            'group_id': group.group_id,
                            'confidence_score': group.confidence_score,
                            'transaction_count': len(group.transactions),
                            'user_id': self.user.id
                        }
                    )
                    
                except Exception as e:
                    merge_errors.append({
                        'group_id': group.group_id,
                        'error': str(e)
                    })
                    
                    self.audit_logger.error(
                        f"Failed to auto-merge duplicate group: {group.group_id}",
                        extra={
                            'group_id': group.group_id,
                            'error': str(e),
                            'user_id': self.user.id
                        }
                    )
        
        return {
            'merged_groups': merged_groups,
            'merge_errors': merge_errors,
            'total_merged': len(merged_groups),
            'total_errors': len(merge_errors)
        }
    
    async def _merge_duplicate_group(self, group: DuplicateGroup, auto_merge: bool = False) -> Dict[str, Any]:
        """Merge transactions in a duplicate group"""
        if len(group.transactions) < 2:
            raise ValidationException("Group must have at least 2 transactions to merge")
        
        # Use the primary transaction as the keeper
        primary_txn_id = group.primary_transaction_id
        other_txn_ids = [txn['id'] for txn in group.transactions if txn['id'] != primary_txn_id]
        
        if not other_txn_ids:
            raise ValidationException("No duplicate transactions found to merge")
        
        # Use the bulk operations service to delete the duplicates
        bulk_ops = TransactionBulkOperations(self.db, self.user)
        delete_request = BulkUpdateRequest(
            transaction_ids=other_txn_ids,
            operation_type=BulkOperationType.DELETE,
            updates={},
            create_backup=not auto_merge  # Only create backup for manual merges
        )
        
        result = await bulk_ops.execute_bulk_update(delete_request)
        
        if result.failed_count > 0:
            raise BusinessLogicException(
                f"Failed to merge {result.failed_count} transactions: {result.errors}"
            )
        
        return {
            'primary_transaction_id': primary_txn_id,
            'deleted_transaction_ids': other_txn_ids,
            'merge_type': 'auto' if auto_merge else 'manual'
        }
    
    async def get_duplicate_statistics(self) -> Dict[str, Any]:
        """Get statistics about duplicate detection for the user"""
        try:
            # Get recent transactions for analysis
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            recent_txns = await self._get_transactions_for_analysis(cutoff_date)
            
            # Quick duplicate scan with higher threshold
            quick_matches = await self._find_duplicate_matches(recent_txns, 0.7)
            
            stats = {
                'total_transactions_analyzed': len(recent_txns),
                'potential_duplicates_found': len(quick_matches),
                'high_confidence_duplicates': len([m for m in quick_matches if m.confidence_score >= 0.8]),
                'auto_merge_candidates': len([m for m in quick_matches if m.confidence_score >= DuplicateDetectionLimits.AUTO_MERGE_THRESHOLD]),
                'match_types': {},
                'confidence_distribution': {
                    'very_high': 0,
                    'high': 0, 
                    'medium': 0,
                    'low': 0
                }
            }
            
            # Count match types
            for match in quick_matches:
                match_type = match.match_type.value
                stats['match_types'][match_type] = stats['match_types'].get(match_type, 0) + 1
                
                # Count confidence distribution
                if match.confidence_score >= 0.85:
                    stats['confidence_distribution']['very_high'] += 1
                elif match.confidence_score >= 0.7:
                    stats['confidence_distribution']['high'] += 1
                elif match.confidence_score >= 0.5:
                    stats['confidence_distribution']['medium'] += 1
                else:
                    stats['confidence_distribution']['low'] += 1
            
            return stats
            
        except Exception as e:
            self.audit_logger.error(
                f"Failed to get duplicate statistics",
                extra={'error': str(e), 'user_id': self.user.id}
            )
            raise BusinessLogicException(f"Failed to get duplicate statistics: {str(e)}")