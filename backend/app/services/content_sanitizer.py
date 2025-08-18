"""
Content sanitization service for FinGood platform.
Implements secure data sanitization for CSV financial data uploads.
"""

import re
import html
import unicodedata
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging
import pandas as pd
from datetime import datetime
import bleach

from app.core.config import settings
from app.core.audit_logger import security_audit_logger

logger = logging.getLogger(__name__)


class SanitizationLevel(Enum):
    """Sanitization strictness levels"""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


@dataclass
class SanitizationResult:
    """Result of content sanitization"""
    is_safe: bool
    sanitized_content: str
    modifications_made: List[str]
    security_issues: List[str]
    original_size: int
    sanitized_size: int
    sanitization_level: SanitizationLevel


class ContentSanitizer:
    """
    Comprehensive content sanitization for financial CSV data.
    Removes malicious content while preserving data integrity.
    """
    
    # Dangerous patterns that should be completely removed
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # JavaScript
        r'javascript:',                # JavaScript URLs
        r'vbscript:',                 # VBScript URLs
        r'data:text/html',            # Data URLs with HTML
        r'onclick\s*=',               # Event handlers
        r'onload\s*=',
        r'onerror\s*=',
        r'onmouseover\s*=',
        r'<%.*?%>',                   # Server-side scripts
        r'<?php.*?\?>',               # PHP code
        r'#!/bin/',                   # Shell scripts
        r'exec\s*\(',                 # Code execution
        r'eval\s*\(',                 # Code evaluation
        r'system\s*\(',               # System calls
        r'shell_exec\s*\(',           # Shell execution
        r'passthru\s*\(',             # Process execution
    ]
    
    # Suspicious patterns that require special handling
    SUSPICIOUS_PATTERNS = [
        r'=\s*[A-Z]+\(',              # Excel formulas that might be dangerous
        r'@\s*[A-Z]+\(',              # Alternative formula syntax
        r'=\s*HYPERLINK\s*\(',        # Hyperlink formulas
        r'=\s*WEBSERVICE\s*\(',       # Web service calls
        r'=\s*IMPORTDATA\s*\(',       # Data import functions
        r'=\s*IMPORTXML\s*\(',        # XML import functions
        r'=\s*IMPORTHTML\s*\(',       # HTML import functions
        r'=\s*IMPORTFEED\s*\(',       # Feed import functions
    ]
    
    # Financial data patterns to preserve
    FINANCIAL_PATTERNS = [
        r'\$[\d,]+\.?\d*',            # Currency amounts
        r'[\d,]+\.?\d*\s*(USD|EUR|GBP|CAD)', # Currency with codes
        r'\d{4}-\d{2}-\d{2}',         # ISO dates
        r'\d{1,2}/\d{1,2}/\d{4}',     # US dates
        r'\d{1,2}-\d{1,2}-\d{4}',     # Alternative date format
        r'[A-Z]{2}\d{2}[A-Z]{4}\d{14}', # IBAN
        r'\d{3}-\d{2}-\d{4}',         # SSN format
        r'\d{9}',                     # Routing numbers
    ]
    
    # Safe characters for financial data
    SAFE_CHARS = set(
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        '0123456789'
        ' .,;:!?()[]{}@#$%^&*-+=_|\\/"\'`~'
        '\n\r\t'
    )
    
    def __init__(self):
        # Configure bleach for HTML sanitization
        self.allowed_tags = []  # No HTML tags allowed in CSV
        self.allowed_attributes = {}
        self.allowed_protocols = ['http', 'https', 'mailto']
    
    async def sanitize_csv_content(
        self,
        content: str,
        filename: str,
        user_id: Optional[str] = None,
        level: SanitizationLevel = SanitizationLevel.STRICT
    ) -> SanitizationResult:
        """
        Sanitize CSV content for safe processing.
        
        Args:
            content: Raw CSV content as string
            filename: Original filename for audit logging
            user_id: User ID for audit logging
            level: Sanitization strictness level
            
        Returns:
            SanitizationResult with sanitized content and metadata
        """
        
        try:
            original_size = len(content)
            modifications = []
            security_issues = []
            
            # Log sanitization start
            security_audit_logger.log_content_sanitization_start(
                user_id=user_id,
                filename=filename,
                content_size=original_size,
                level=level.value
            )
            
            # Step 1: Remove dangerous patterns
            sanitized_content, dangerous_mods = self._remove_dangerous_patterns(content)
            modifications.extend(dangerous_mods)
            
            # Step 2: Handle suspicious patterns
            sanitized_content, suspicious_mods = self._handle_suspicious_patterns(
                sanitized_content, level
            )
            modifications.extend(suspicious_mods)
            security_issues.extend(suspicious_mods)
            
            # Step 3: Normalize Unicode characters
            sanitized_content, unicode_mods = self._normalize_unicode(sanitized_content)
            modifications.extend(unicode_mods)
            
            # Step 4: Remove or escape HTML entities
            sanitized_content, html_mods = self._sanitize_html(sanitized_content)
            modifications.extend(html_mods)
            
            # Step 5: Filter characters based on level
            sanitized_content, char_mods = self._filter_characters(sanitized_content, level)
            modifications.extend(char_mods)
            
            # Step 6: Validate line endings and structure
            sanitized_content, structure_mods = self._sanitize_structure(sanitized_content)
            modifications.extend(structure_mods)
            
            # Step 7: Final validation
            security_issues.extend(self._final_security_check(sanitized_content))
            
            sanitized_size = len(sanitized_content)
            is_safe = len(security_issues) == 0
            
            result = SanitizationResult(
                is_safe=is_safe,
                sanitized_content=sanitized_content,
                modifications_made=modifications,
                security_issues=security_issues,
                original_size=original_size,
                sanitized_size=sanitized_size,
                sanitization_level=level
            )
            
            # Log sanitization result
            security_audit_logger.log_content_sanitization_complete(
                user_id=user_id,
                filename=filename,
                original_size=original_size,
                sanitized_size=sanitized_size,
                modifications_count=len(modifications),
                security_issues_count=len(security_issues),
                is_safe=is_safe
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Content sanitization failed for {filename}: {e}")
            security_audit_logger.log_content_sanitization_error(
                user_id=user_id,
                filename=filename,
                error=str(e)
            )
            
            # Return original content with error flag
            return SanitizationResult(
                is_safe=False,
                sanitized_content=content,
                modifications_made=[],
                security_issues=[f"Sanitization error: {str(e)}"],
                original_size=len(content),
                sanitized_size=len(content),
                sanitization_level=level
            )
    
    def _remove_dangerous_patterns(self, content: str) -> Tuple[str, List[str]]:
        """Remove obviously dangerous patterns"""
        
        modifications = []
        sanitized = content
        
        for pattern in self.DANGEROUS_PATTERNS:
            matches = re.findall(pattern, sanitized, re.IGNORECASE | re.DOTALL)
            if matches:
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
                modifications.append(f"Removed dangerous pattern: {pattern}")
                logger.warning(f"Removed {len(matches)} instances of dangerous pattern: {pattern[:30]}...")
        
        return sanitized, modifications
    
    def _handle_suspicious_patterns(
        self, 
        content: str, 
        level: SanitizationLevel
    ) -> Tuple[str, List[str]]:
        """Handle suspicious patterns based on sanitization level"""
        
        modifications = []
        sanitized = content
        
        for pattern in self.SUSPICIOUS_PATTERNS:
            matches = re.findall(pattern, sanitized, re.IGNORECASE)
            if matches:
                if level == SanitizationLevel.STRICT:
                    # Remove completely
                    sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
                    modifications.append(f"Removed suspicious pattern (strict): {pattern}")
                elif level == SanitizationLevel.MODERATE:
                    # Escape the pattern
                    sanitized = re.sub(pattern, lambda m: f"'{m.group()}'", sanitized, flags=re.IGNORECASE)
                    modifications.append(f"Escaped suspicious pattern (moderate): {pattern}")
                else:  # LENIENT
                    # Just log but keep
                    modifications.append(f"Detected suspicious pattern (lenient): {pattern}")
        
        return sanitized, modifications
    
    def _normalize_unicode(self, content: str) -> Tuple[str, List[str]]:
        """Normalize Unicode characters to prevent encoding attacks"""
        
        modifications = []
        
        try:
            # Normalize to NFC form
            normalized = unicodedata.normalize('NFC', content)
            
            if normalized != content:
                modifications.append("Normalized Unicode characters")
            
            # Remove or replace dangerous Unicode categories
            filtered_chars = []
            dangerous_categories = ['Cc', 'Cf', 'Co', 'Cs']  # Control, format, private use, surrogate
            
            for char in normalized:
                category = unicodedata.category(char)
                if category in dangerous_categories and char not in ['\n', '\r', '\t']:
                    # Replace with space or remove
                    if char.isspace():
                        filtered_chars.append(' ')
                    # Skip other control characters
                    modifications.append(f"Removed dangerous Unicode character: {category}")
                else:
                    filtered_chars.append(char)
            
            return ''.join(filtered_chars), modifications
            
        except Exception as e:
            logger.warning(f"Unicode normalization failed: {e}")
            return content, [f"Unicode normalization failed: {str(e)}"]
    
    def _sanitize_html(self, content: str) -> Tuple[str, List[str]]:
        """Remove or escape HTML content"""
        
        modifications = []
        
        # Use bleach to remove HTML
        sanitized = bleach.clean(
            content,
            tags=self.allowed_tags,
            attributes=self.allowed_attributes,
            protocols=self.allowed_protocols,
            strip=True
        )
        
        if sanitized != content:
            modifications.append("Removed HTML tags and entities")
        
        # Additional HTML entity decoding for safer handling
        try:
            decoded = html.unescape(sanitized)
            if decoded != sanitized:
                modifications.append("Decoded HTML entities")
            sanitized = decoded
        except Exception:
            pass
        
        return sanitized, modifications
    
    def _filter_characters(
        self, 
        content: str, 
        level: SanitizationLevel
    ) -> Tuple[str, List[str]]:
        """Filter characters based on sanitization level"""
        
        modifications = []
        
        if level == SanitizationLevel.STRICT:
            # Only allow safe characters
            filtered = ''.join(char for char in content if char in self.SAFE_CHARS)
            if len(filtered) != len(content):
                removed_count = len(content) - len(filtered)
                modifications.append(f"Removed {removed_count} unsafe characters")
            return filtered, modifications
        
        elif level == SanitizationLevel.MODERATE:
            # Allow most printable characters but filter dangerous ones
            dangerous_chars = set('<>&"\'`')
            filtered = ''.join(
                char if char not in dangerous_chars or char in self.SAFE_CHARS 
                else f'&#{ord(char)};' 
                for char in content
            )
            if filtered != content:
                modifications.append("Escaped dangerous characters")
            return filtered, modifications
        
        else:  # LENIENT
            # Minimal filtering - just remove null bytes and extreme control chars
            filtered = content.replace('\x00', '').replace('\x01', '').replace('\x02', '')
            if filtered != content:
                modifications.append("Removed null bytes and extreme control characters")
            return filtered, modifications
    
    def _sanitize_structure(self, content: str) -> Tuple[str, List[str]]:
        """Sanitize CSV structure and line endings"""
        
        modifications = []
        
        # Normalize line endings
        normalized = content.replace('\r\n', '\n').replace('\r', '\n')
        if normalized != content:
            modifications.append("Normalized line endings")
        
        # Remove excessive blank lines
        lines = normalized.split('\n')
        filtered_lines = []
        consecutive_empty = 0
        
        for line in lines:
            if line.strip() == '':
                consecutive_empty += 1
                if consecutive_empty <= 2:  # Allow up to 2 consecutive empty lines
                    filtered_lines.append(line)
            else:
                consecutive_empty = 0
                filtered_lines.append(line)
        
        if len(filtered_lines) != len(lines):
            modifications.append("Removed excessive blank lines")
        
        # Limit line length to prevent buffer overflow attacks
        max_line_length = 10000
        truncated_lines = []
        for line in filtered_lines:
            if len(line) > max_line_length:
                truncated_lines.append(line[:max_line_length])
                modifications.append(f"Truncated line exceeding {max_line_length} characters")
            else:
                truncated_lines.append(line)
        
        return '\n'.join(truncated_lines), modifications
    
    def _final_security_check(self, content: str) -> List[str]:
        """Final security validation of sanitized content"""
        
        security_issues = []
        
        # Check for remaining dangerous patterns
        remaining_dangerous = [
            r'<script',
            r'javascript:',
            r'vbscript:',
            r'data:',
            r'<?php',
            r'<%',
            r'exec\s*\(',
            r'eval\s*\(',
        ]
        
        for pattern in remaining_dangerous:
            if re.search(pattern, content, re.IGNORECASE):
                security_issues.append(f"Dangerous pattern still present after sanitization: {pattern}")
        
        # Check content size after sanitization
        if len(content) > 100 * 1024 * 1024:  # 100MB
            security_issues.append("Content size exceeds safety limits after sanitization")
        
        # Check for suspicious character sequences
        if '\x00' in content:
            security_issues.append("Null bytes present in sanitized content")
        
        # Check for excessive special characters
        special_char_ratio = sum(1 for char in content if not char.isalnum() and char not in ' \n\r\t.,;:') / len(content) if content else 0
        if special_char_ratio > 0.5:
            security_issues.append("High ratio of special characters in sanitized content")
        
        return security_issues
    
    async def sanitize_dataframe(
        self,
        df: pd.DataFrame,
        filename: str,
        user_id: Optional[str] = None,
        level: SanitizationLevel = SanitizationLevel.STRICT
    ) -> Tuple[pd.DataFrame, SanitizationResult]:
        """
        Sanitize DataFrame content for safe processing.
        
        Args:
            df: DataFrame to sanitize
            filename: Original filename for audit logging
            user_id: User ID for audit logging
            level: Sanitization strictness level
            
        Returns:
            Tuple of (sanitized_dataframe, sanitization_result)
        """
        
        modifications = []
        security_issues = []
        
        try:
            # Sanitize column names
            original_columns = df.columns.tolist()
            sanitized_columns = []
            
            for col in original_columns:
                sanitized_col = re.sub(r'[^\w\s-]', '_', str(col))
                sanitized_columns.append(sanitized_col)
                if sanitized_col != str(col):
                    modifications.append(f"Sanitized column name: {col} -> {sanitized_col}")
            
            df.columns = sanitized_columns
            
            # Sanitize cell values
            for column in df.columns:
                if df[column].dtype == 'object':  # String columns
                    for idx, value in df[column].items():
                        if pd.notna(value):
                            str_value = str(value)
                            # Quick sanitization for cell values
                            sanitized_value = self._sanitize_cell_value(str_value, level)
                            if sanitized_value != str_value:
                                df.at[idx, column] = sanitized_value
                                modifications.append(f"Sanitized cell value in column {column}, row {idx}")
            
            # Create result summary
            result = SanitizationResult(
                is_safe=len(security_issues) == 0,
                sanitized_content="<DataFrame>",
                modifications_made=modifications,
                security_issues=security_issues,
                original_size=df.memory_usage(deep=True).sum(),
                sanitized_size=df.memory_usage(deep=True).sum(),
                sanitization_level=level
            )
            
            return df, result
            
        except Exception as e:
            logger.error(f"DataFrame sanitization failed: {e}")
            security_issues.append(f"DataFrame sanitization error: {str(e)}")
            
            result = SanitizationResult(
                is_safe=False,
                sanitized_content="<DataFrame with errors>",
                modifications_made=modifications,
                security_issues=security_issues,
                original_size=0,
                sanitized_size=0,
                sanitization_level=level
            )
            
            return df, result
    
    def _sanitize_cell_value(self, value: str, level: SanitizationLevel) -> str:
        """Sanitize individual cell value"""
        
        if not value or len(value) > 1000:  # Limit cell size
            return value[:1000] if value else value
        
        # Remove dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE | re.DOTALL)
        
        # Handle suspicious patterns
        if level == SanitizationLevel.STRICT:
            for pattern in self.SUSPICIOUS_PATTERNS:
                value = re.sub(pattern, '', value, flags=re.IGNORECASE)
        
        # Basic character filtering
        if level == SanitizationLevel.STRICT:
            value = ''.join(char for char in value if char in self.SAFE_CHARS)
        
        return value


# Convenience functions
async def sanitize_csv_content(
    content: str,
    filename: str,
    user_id: Optional[str] = None,
    level: SanitizationLevel = SanitizationLevel.STRICT
) -> SanitizationResult:
    """Convenience function to sanitize CSV content"""
    sanitizer = ContentSanitizer()
    return await sanitizer.sanitize_csv_content(content, filename, user_id, level)


async def sanitize_dataframe(
    df: pd.DataFrame,
    filename: str,
    user_id: Optional[str] = None,
    level: SanitizationLevel = SanitizationLevel.STRICT
) -> Tuple[pd.DataFrame, SanitizationResult]:
    """Convenience function to sanitize DataFrame"""
    sanitizer = ContentSanitizer()
    return await sanitizer.sanitize_dataframe(df, filename, user_id, level)