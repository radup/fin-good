"""
Comprehensive file validation service for FinGood platform.
Implements secure file upload validation including magic number detection,
malware scanning, and content validation for financial data security.
"""

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    magic = None
import hashlib
import os
import tempfile
import subprocess
import time
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, BinaryIO
from dataclasses import dataclass
from enum import Enum
import logging
import mimetypes
import io
import pandas as pd
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.audit_logger import SecurityAuditLogger as AuditLogger

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat levels for file validation"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationResult(Enum):
    """File validation results"""
    APPROVED = "approved"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"


@dataclass
class FileValidationResult:
    """Comprehensive file validation result"""
    is_valid: bool
    validation_result: ValidationResult
    threat_level: ThreatLevel
    file_info: Dict[str, Any]
    validation_checks: Dict[str, bool]
    errors: List[str]
    warnings: List[str]
    quarantine_id: Optional[str] = None
    scan_duration: float = 0.0
    metadata: Dict[str, Any] = None


@dataclass
class FileMetrics:
    """File upload metrics for monitoring"""
    file_size: int
    mime_type: str
    file_extension: str
    checksum_md5: str
    checksum_sha256: str
    upload_timestamp: datetime
    validation_duration: float


class FileValidator:
    """
    Comprehensive file validation service for financial data uploads.
    Implements multiple layers of security validation.
    """
    
    # Magic numbers for common file types
    MAGIC_NUMBERS = {
        'csv': [
            b'\xef\xbb\xbf',  # UTF-8 BOM
            b'\xff\xfe',      # UTF-16 LE BOM
            b'\xfe\xff',      # UTF-16 BE BOM
        ],
        'xlsx': [b'PK\x03\x04'],
        'xls': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],
        'xlsm': [b'PK\x03\x04'],  # Excel with macros (potential security risk)
        'zip': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],
        'exe': [b'MZ'],
        'pdf': [b'%PDF'],
        'png': [b'\x89PNG\r\n\x1a\n'],
        'jpg': [b'\xff\xd8\xff'],
        'gif': [b'GIF87a', b'GIF89a'],
        'rtf': [b'{\\rtf'],
        'docx': [b'PK\x03\x04'],
        'pptx': [b'PK\x03\x04'],
    }
    
    # Financial file format specific validation
    FINANCIAL_FILE_PATTERNS = {
        'ofx': [b'<OFX>', b'OFXHEADER:'],  # Open Financial Exchange
        'qif': [b'!Type:', b'!Option:'],   # Quicken Interchange Format  
        'mt940': [b':20:', b':25:', b':28C:'],  # SWIFT MT940
        'bai': [b'01,', b'02,', b'03,'],   # Bank Administration Institute
    }
    
    # Suspicious file signatures
    SUSPICIOUS_SIGNATURES = [
        b'MZ',  # PE executable
        b'\x7fELF',  # ELF executable
        b'\xca\xfe\xba\xbe',  # Java class file
        b'\xfe\xed\xfa\xce',  # Mach-O binary
        b'\xfe\xed\xfa\xcf',  # Mach-O binary
        b'#!/bin/',  # Shell script
        b'<?php',  # PHP script
        b'<script',  # JavaScript/HTML
        b'javascript:',  # JavaScript URL
        b'vbscript:',  # VBScript URL
        b'<%@',  # JSP/ASP directive
        b'<?xml version=',  # XML declaration (potential XXE)
        b'\x50\x4b\x03\x04\x14\x00\x06\x00',  # Encrypted ZIP
        b'\x50\x4b\x07\x08',  # ZIP with digital signature
        b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',  # OLE compound (can contain macros)
    ]
    
    # Financial malware indicators
    FINANCIAL_THREAT_PATTERNS = [
        b'bitcoin',
        b'wallet.dat',
        b'cryptocurrency',
        b'mining',
        b'keylogger',
        b'bankbot',
        b'trojan.banker',
        b'carbanak',
        b'zeus',
        b'credential',
        b'password',
        b'private key',
        b'seed phrase',
    ]
    
    # Maximum file sizes by type (bytes)
    MAX_FILE_SIZES = {
        'csv': 50 * 1024 * 1024,  # 50MB for CSV
        'xlsx': 25 * 1024 * 1024,  # 25MB for Excel
        'xls': 25 * 1024 * 1024,   # 25MB for Excel
    }
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        self.audit_logger = audit_logger or AuditLogger()
        self.quarantine_dir = Path(settings.UPLOAD_DIR) / "quarantine"
        self.quarantine_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize libmagic
        try:
            if MAGIC_AVAILABLE and magic:
                self.magic = magic.Magic(mime=True)
                self.magic_enabled = True
            else:
                self.magic = None
                self.magic_enabled = False
        except Exception as e:
            logger.warning(f"libmagic not available: {e}. Falling back to basic validation.")
            self.magic_enabled = False
    
    async def validate_file(
        self, 
        file_content: bytes, 
        filename: str,
        user_id: Optional[str] = None
    ) -> FileValidationResult:
        """
        Comprehensive file validation pipeline.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            user_id: User ID for audit logging
            
        Returns:
            FileValidationResult with comprehensive validation details
        """
        start_time = time.time()
        
        try:
            # Initialize validation result
            result = FileValidationResult(
                is_valid=False,
                validation_result=ValidationResult.REJECTED,
                threat_level=ThreatLevel.HIGH,
                file_info={},
                validation_checks={},
                errors=[],
                warnings=[],
                metadata={}
            )
            
            # Log validation start
            self.audit_logger.log_file_upload_attempt(
                user_id=user_id,
                filename=filename,
                file_size=len(file_content),
                timestamp=datetime.utcnow()
            )
            
            # Step 1: Basic file validation
            await self._validate_basic_properties(file_content, filename, result)
            
            # Step 2: Magic number validation
            await self._validate_magic_numbers(file_content, filename, result)
            
            # Step 3: Content type validation
            await self._validate_content_type(file_content, filename, result)
            
            # Step 4: Malware scanning
            await self._scan_for_malware(file_content, filename, result)
            
            # Step 5: CSV structure validation (if applicable)
            if self._is_csv_file(filename):
                await self._validate_csv_structure(file_content, result)
            
            # Step 6: Size and resource validation
            await self._validate_file_size(file_content, filename, result)
            
            # Step 7: Financial threat detection
            await self._detect_financial_threats(file_content, filename, result)
            
            # Step 8: Steganography detection
            await self._detect_steganography(file_content, filename, result)
            
            # Step 9: Suspicious content detection
            await self._detect_suspicious_content(file_content, result)
            
            # Calculate final threat level and validation result
            self._calculate_final_result(result)
            
            # Handle quarantine if needed
            if result.validation_result == ValidationResult.QUARANTINED:
                result.quarantine_id = await self._quarantine_file(file_content, filename)
            
            result.scan_duration = time.time() - start_time
            
            # Log validation result
            self.audit_logger.log_file_validation_result(
                user_id=user_id,
                filename=filename,
                validation_result=result.validation_result.value,
                threat_level=result.threat_level.value,
                errors=result.errors,
                duration=result.scan_duration
            )
            
            return result
            
        except Exception as e:
            logger.error(f"File validation failed for {filename}: {e}")
            error_result = FileValidationResult(
                is_valid=False,
                validation_result=ValidationResult.REJECTED,
                threat_level=ThreatLevel.CRITICAL,
                file_info={'filename': filename, 'size': len(file_content)},
                validation_checks={'validation_error': False},
                errors=[f"Validation system error: {str(e)}"],
                warnings=[],
                scan_duration=time.time() - start_time
            )
            
            self.audit_logger.log_file_validation_error(
                user_id=user_id,
                filename=filename,
                error=str(e)
            )
            
            return error_result
    
    async def _validate_basic_properties(
        self, 
        file_content: bytes, 
        filename: str, 
        result: FileValidationResult
    ) -> None:
        """Validate basic file properties"""
        
        # File size validation
        file_size = len(file_content)
        if file_size == 0:
            result.errors.append("File is empty")
            result.validation_checks['non_empty'] = False
        else:
            result.validation_checks['non_empty'] = True
        
        # Filename validation
        if not filename or len(filename.strip()) == 0:
            result.errors.append("Invalid filename")
            result.validation_checks['valid_filename'] = False
        elif any(char in filename for char in ['<', '>', ':', '"', '|', '?', '*', '\0']):
            result.errors.append("Filename contains invalid characters")
            result.validation_checks['valid_filename'] = False
        else:
            result.validation_checks['valid_filename'] = True
        
        # Extension validation
        file_ext = Path(filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            result.errors.append(f"File extension {file_ext} not allowed")
            result.validation_checks['allowed_extension'] = False
        else:
            result.validation_checks['allowed_extension'] = True
        
        # Store file info
        result.file_info.update({
            'filename': filename,
            'size': file_size,
            'extension': file_ext,
            'md5': hashlib.md5(file_content).hexdigest(),
            'sha256': hashlib.sha256(file_content).hexdigest()
        })
    
    async def _validate_magic_numbers(
        self, 
        file_content: bytes, 
        filename: str, 
        result: FileValidationResult
    ) -> None:
        """Validate file magic numbers against expected types"""
        
        if len(file_content) < 16:
            result.warnings.append("File too small for magic number validation")
            result.validation_checks['magic_number'] = False
            return
        
        file_ext = Path(filename).suffix.lower().lstrip('.')
        file_header = file_content[:16]
        
        # Check for expected magic numbers
        expected_magics = self.MAGIC_NUMBERS.get(file_ext, [])
        magic_match = False
        
        for magic in expected_magics:
            if file_content.startswith(magic):
                magic_match = True
                break
        
        # For CSV files, also allow plain text (no magic number)
        if file_ext == 'csv' and not magic_match:
            try:
                # Try to decode as text to verify it's a text file
                file_content[:1024].decode('utf-8')
                magic_match = True
            except UnicodeDecodeError:
                pass
        
        # Use libmagic if available
        if self.magic_enabled:
            try:
                detected_mime = self.magic.from_buffer(file_content)
                result.file_info['detected_mime'] = detected_mime
                
                # Validate MIME type matches extension
                expected_mimes = {
                    'csv': ['text/csv', 'text/plain', 'application/csv'],
                    'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
                    'xls': ['application/vnd.ms-excel']
                }
                
                if file_ext in expected_mimes:
                    if detected_mime not in expected_mimes[file_ext]:
                        result.warnings.append(
                            f"MIME type mismatch: detected {detected_mime}, expected one of {expected_mimes[file_ext]}"
                        )
            except Exception as e:
                logger.warning(f"libmagic detection failed: {e}")
        
        # Check for suspicious magic numbers
        for suspicious in self.SUSPICIOUS_SIGNATURES:
            if file_content.startswith(suspicious):
                result.errors.append(f"Suspicious file signature detected")
                result.validation_checks['no_suspicious_signature'] = False
                return
        
        result.validation_checks['magic_number'] = magic_match
        result.validation_checks['no_suspicious_signature'] = True
        
        if not magic_match and file_ext in expected_magics:
            result.warnings.append(f"Magic number mismatch for {file_ext} file")
    
    async def _validate_content_type(
        self, 
        file_content: bytes, 
        filename: str, 
        result: FileValidationResult
    ) -> None:
        """Validate file content type consistency"""
        
        # Use mimetypes library
        guessed_type, _ = mimetypes.guess_type(filename)
        if guessed_type:
            result.file_info['guessed_mime'] = guessed_type
        
        # Additional content validation for text files
        file_ext = Path(filename).suffix.lower().lstrip('.')
        if file_ext == 'csv':
            try:
                # Validate text encoding
                decoded_content = file_content.decode('utf-8')
                result.validation_checks['valid_encoding'] = True
                
                # Basic CSV structure check
                if ',' in decoded_content or '\t' in decoded_content or ';' in decoded_content:
                    result.validation_checks['csv_structure'] = True
                else:
                    result.warnings.append("File may not contain valid CSV delimiters")
                    result.validation_checks['csv_structure'] = False
                    
            except UnicodeDecodeError:
                try:
                    # Try other common encodings
                    decoded_content = file_content.decode('latin-1')
                    result.warnings.append("File uses non-UTF-8 encoding")
                    result.validation_checks['valid_encoding'] = True
                except UnicodeDecodeError:
                    result.errors.append("Invalid text encoding")
                    result.validation_checks['valid_encoding'] = False
    
    async def _scan_for_malware(
        self, 
        file_content: bytes, 
        filename: str, 
        result: FileValidationResult
    ) -> None:
        """Basic malware detection and suspicious content scanning"""
        
        # Check for embedded executables
        suspicious_patterns = [
            b'MZ\x90\x00',  # PE header
            b'\x7fELF',     # ELF header
            b'#!/bin/sh',   # Shell script
            b'#!/bin/bash', # Bash script
            b'<script',     # JavaScript
            b'<?php',       # PHP
            b'<%@',         # JSP/ASP
            b'eval(',       # Code evaluation
            b'exec(',       # Code execution
            b'system(',     # System calls
            b'shell_exec(', # Shell execution
        ]
        
        malware_detected = False
        for pattern in suspicious_patterns:
            if pattern in file_content:
                result.errors.append(f"Suspicious content pattern detected")
                malware_detected = True
                break
        
        # Check for excessive binary content in text files
        file_ext = Path(filename).suffix.lower().lstrip('.')
        if file_ext == 'csv':
            # Count non-printable characters
            non_printable = sum(1 for byte in file_content if byte < 32 and byte not in [9, 10, 13])
            if len(file_content) > 0:
                non_printable_ratio = non_printable / len(file_content)
                if non_printable_ratio > 0.1:  # More than 10% non-printable
                    result.warnings.append("High ratio of non-printable characters detected")
                    result.validation_checks['text_file_integrity'] = False
                else:
                    result.validation_checks['text_file_integrity'] = True
        
        # Check file entropy (basic detection of compressed/encrypted content)
        entropy = self._calculate_entropy(file_content[:4096])  # Check first 4KB
        if entropy > 7.5:  # High entropy suggests encrypted/compressed content
            result.warnings.append("High entropy detected - file may be compressed or encrypted")
        
        result.validation_checks['malware_scan'] = not malware_detected
    
    async def _validate_csv_structure(
        self, 
        file_content: bytes, 
        result: FileValidationResult
    ) -> None:
        """Comprehensive CSV structure validation"""
        
        try:
            # Decode content
            content_str = file_content.decode('utf-8')
            
            # Basic structure validation
            lines = content_str.split('\n')
            if len(lines) < 2:
                result.errors.append("CSV file must have at least a header and one data row")
                result.validation_checks['csv_min_rows'] = False
                return
            
            result.validation_checks['csv_min_rows'] = True
            
            # Try to parse with pandas for structure validation
            try:
                df = pd.read_csv(io.StringIO(content_str), nrows=10)  # Sample first 10 rows
                
                if len(df.columns) == 0:
                    result.errors.append("CSV file has no columns")
                    result.validation_checks['csv_valid_structure'] = False
                elif len(df.columns) > 100:
                    result.warnings.append("CSV file has unusually many columns")
                    result.validation_checks['csv_valid_structure'] = True
                else:
                    result.validation_checks['csv_valid_structure'] = True
                
                # Check for required columns for financial data
                required_cols = ['date', 'amount', 'description']
                csv_cols = [col.lower().strip() for col in df.columns]
                
                missing_cols = []
                for req_col in required_cols:
                    if not any(req_col in col for col in csv_cols):
                        missing_cols.append(req_col)
                
                if missing_cols:
                    result.warnings.append(f"Recommended columns missing: {missing_cols}")
                else:
                    result.validation_checks['csv_financial_columns'] = True
                
            except Exception as e:
                result.warnings.append(f"CSV structure validation warning: {str(e)}")
                result.validation_checks['csv_valid_structure'] = False
            
            # Check for suspicious CSV content
            if any(pattern in content_str.lower() for pattern in ['<script', '<?php', 'javascript:', 'vbscript:']):
                result.errors.append("Suspicious script content detected in CSV")
                result.validation_checks['csv_no_scripts'] = False
            else:
                result.validation_checks['csv_no_scripts'] = True
            
        except UnicodeDecodeError:
            result.errors.append("CSV file encoding error")
            result.validation_checks['csv_encoding'] = False
    
    async def _validate_file_size(
        self, 
        file_content: bytes, 
        filename: str, 
        result: FileValidationResult
    ) -> None:
        """Validate file size restrictions"""
        
        file_size = len(file_content)
        file_ext = Path(filename).suffix.lower().lstrip('.')
        
        # Check against global maximum
        if file_size > settings.MAX_FILE_SIZE:
            result.errors.append(f"File size {file_size} exceeds maximum {settings.MAX_FILE_SIZE}")
            result.validation_checks['size_within_global_limit'] = False
        else:
            result.validation_checks['size_within_global_limit'] = True
        
        # Check against type-specific maximum
        if file_ext in self.MAX_FILE_SIZES:
            max_size = self.MAX_FILE_SIZES[file_ext]
            if file_size > max_size:
                result.errors.append(f"File size {file_size} exceeds {file_ext} limit {max_size}")
                result.validation_checks['size_within_type_limit'] = False
            else:
                result.validation_checks['size_within_type_limit'] = True
        
        # Warning for unusually large files
        if file_size > 10 * 1024 * 1024:  # 10MB
            result.warnings.append("Large file detected - processing may take longer")
    
    async def _detect_financial_threats(
        self,
        file_content: bytes,
        filename: str,
        result: FileValidationResult
    ) -> None:
        """Detect financial sector specific threats"""
        
        content_lower = file_content.lower()
        threats_found = []
        
        # Check for financial malware indicators
        for pattern in self.FINANCIAL_THREAT_PATTERNS:
            if pattern in content_lower:
                threats_found.append(pattern.decode('utf-8', errors='ignore'))
        
        if threats_found:
            result.errors.append(f"Financial threat indicators detected: {', '.join(threats_found[:3])}")
            result.validation_checks['no_financial_threats'] = False
        else:
            result.validation_checks['no_financial_threats'] = True
        
        # Check for banking trojan signatures
        banking_trojan_patterns = [
            b'account number',
            b'social security',
            b'credit card',
            b'pin number',
            b'routing number',
            b'swift code',
            b'iban',
        ]
        
        suspicious_financial_data = []
        for pattern in banking_trojan_patterns:
            if pattern in content_lower:
                suspicious_financial_data.append(pattern.decode('utf-8', errors='ignore'))
        
        if len(suspicious_financial_data) > 3:  # Multiple financial identifiers
            result.warnings.append(f"Multiple financial data patterns detected: {len(suspicious_financial_data)}")
            result.validation_checks['financial_data_patterns'] = False
        else:
            result.validation_checks['financial_data_patterns'] = True
        
        # Check for cryptocurrency threats
        crypto_patterns = [
            b'bitcoin address',
            b'ethereum wallet',
            b'crypto wallet',
            b'mining pool',
            b'blockchain',
            b'cryptocurrency exchange',
        ]
        
        crypto_indicators = []
        for pattern in crypto_patterns:
            if pattern in content_lower:
                crypto_indicators.append(pattern.decode('utf-8', errors='ignore'))
        
        if crypto_indicators:
            result.warnings.append(f"Cryptocurrency indicators detected: {', '.join(crypto_indicators[:2])}")
    
    async def _detect_steganography(
        self,
        file_content: bytes,
        filename: str,
        result: FileValidationResult
    ) -> None:
        """Detect potential steganography in files"""
        
        file_ext = Path(filename).suffix.lower()
        
        # For image files, check for hidden data
        if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            # Check for unusual file size ratios
            if len(file_content) > 1024 * 1024:  # Files larger than 1MB
                result.warnings.append("Large image file - potential steganography risk")
            
            # Check for embedded ZIP archives in images
            if b'PK\x03\x04' in file_content[100:]:  # ZIP signature not at beginning
                result.warnings.append("Embedded archive detected in image file")
                result.validation_checks['no_embedded_archives'] = False
            else:
                result.validation_checks['no_embedded_archives'] = True
        
        # For text files, check for unusual encoding patterns
        elif file_ext in ['.csv', '.txt']:
            try:
                # Check for non-standard characters that might hide data
                decoded = file_content.decode('utf-8', errors='ignore')
                
                # Count unusual Unicode characters
                unusual_chars = sum(1 for char in decoded if ord(char) > 127 and ord(char) < 160)
                if unusual_chars > len(decoded) * 0.01:  # More than 1% unusual chars
                    result.warnings.append("Unusual character encoding detected - potential steganography")
                
                # Check for excessive whitespace (common steganography technique)
                whitespace_ratio = (decoded.count(' ') + decoded.count('\t')) / len(decoded) if decoded else 0
                if whitespace_ratio > 0.3:
                    result.warnings.append("High whitespace ratio detected")
                
            except Exception:
                pass
        
        # Check for ZIP files with suspicious content
        elif file_ext in ['.zip', '.xlsx', '.docx']:
            # Look for multiple embedded files (potential data hiding)
            zip_entries = file_content.count(b'PK\x03\x04')
            if zip_entries > 50:  # Many embedded files
                result.warnings.append(f"Archive contains {zip_entries} files - potential data hiding")
    
    async def _detect_suspicious_content(
        self, 
        file_content: bytes, 
        result: FileValidationResult
    ) -> None:
        """Advanced suspicious content detection"""
        
        # Check for polyglot files (files that are valid in multiple formats)
        polyglot_signatures = [
            (b'PK\x03\x04', b'%PDF'),  # ZIP + PDF
            (b'GIF8', b'<script'),      # GIF + JavaScript
            (b'\xff\xd8\xff', b'<?php'), # JPEG + PHP
            (b'%PDF', b'<script'),      # PDF + JavaScript
            (b'\x89PNG', b'<?php'),     # PNG + PHP
        ]
        
        for sig1, sig2 in polyglot_signatures:
            if sig1 in file_content and sig2 in file_content:
                result.errors.append("Polyglot file detected - potential security risk")
                result.validation_checks['no_polyglot'] = False
                return
        
        result.validation_checks['no_polyglot'] = True
        
        # Check for unusual file structure
        if len(file_content) > 1024:
            # Look for embedded files
            zip_signatures = [b'PK\x03\x04', b'PK\x05\x06']
            for sig in zip_signatures:
                positions = [i for i in range(len(file_content) - len(sig)) if file_content[i:i+len(sig)] == sig]
                if len(positions) > 1:  # Multiple zip signatures
                    result.warnings.append("Multiple archive signatures detected")
                    break
        
        # Check for macro-enabled files disguised as regular files
        if b'vbaProject' in file_content or b'macros/' in file_content:
            result.errors.append("Macro content detected in file")
            result.validation_checks['no_macros'] = False
        else:
            result.validation_checks['no_macros'] = True
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data"""
        if not data:
            return 0
        
        # Count frequency of each byte value
        byte_counts = [0] * 256
        for byte in data:
            byte_counts[byte] += 1
        
        # Calculate entropy
        entropy = 0
        data_len = len(data)
        for count in byte_counts:
            if count > 0:
                probability = count / data_len
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _calculate_final_result(self, result: FileValidationResult) -> None:
        """Calculate final validation result based on all checks"""
        
        # Count critical errors
        critical_errors = len([e for e in result.errors if any(
            term in e.lower() for term in ['malware', 'suspicious', 'executable', 'script']
        )])
        
        # Count total errors and warnings
        total_errors = len(result.errors)
        total_warnings = len(result.warnings)
        
        # Determine threat level
        if critical_errors > 0:
            result.threat_level = ThreatLevel.CRITICAL
            result.validation_result = ValidationResult.REJECTED
        elif total_errors > 3:
            result.threat_level = ThreatLevel.HIGH
            result.validation_result = ValidationResult.REJECTED
        elif total_errors > 1:
            result.threat_level = ThreatLevel.MEDIUM
            result.validation_result = ValidationResult.QUARANTINED
        elif total_warnings > 2:
            result.threat_level = ThreatLevel.LOW
            result.validation_result = ValidationResult.QUARANTINED
        elif total_errors == 0 and total_warnings <= 1:
            result.threat_level = ThreatLevel.SAFE
            result.validation_result = ValidationResult.APPROVED
        else:
            result.threat_level = ThreatLevel.LOW
            result.validation_result = ValidationResult.APPROVED
        
        # Final validation decision
        result.is_valid = result.validation_result == ValidationResult.APPROVED
    
    async def _quarantine_file(self, file_content: bytes, filename: str) -> str:
        """Quarantine suspicious file"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        quarantine_id = f"{timestamp}_{hashlib.md5(file_content).hexdigest()[:8]}"
        
        quarantine_path = self.quarantine_dir / f"{quarantine_id}_{filename}"
        
        try:
            with open(quarantine_path, 'wb') as f:
                f.write(file_content)
            
            # Create metadata file
            metadata = {
                'original_filename': filename,
                'quarantine_timestamp': timestamp,
                'file_size': len(file_content),
                'md5': hashlib.md5(file_content).hexdigest(),
                'sha256': hashlib.sha256(file_content).hexdigest(),
            }
            
            metadata_path = self.quarantine_dir / f"{quarantine_id}_metadata.json"
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.warning(f"File quarantined: {quarantine_id} ({filename})")
            return quarantine_id
            
        except Exception as e:
            logger.error(f"Failed to quarantine file {filename}: {e}")
            raise
    
    def _is_csv_file(self, filename: str) -> bool:
        """Check if file is a CSV file"""
        return Path(filename).suffix.lower() == '.csv'
    
    async def get_quarantine_info(self, quarantine_id: str) -> Optional[Dict[str, Any]]:
        """Get information about quarantined file"""
        
        metadata_path = self.quarantine_dir / f"{quarantine_id}_metadata.json"
        if not metadata_path.exists():
            return None
        
        try:
            import json
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read quarantine metadata {quarantine_id}: {e}")
            return None
    
    async def release_from_quarantine(self, quarantine_id: str, user_id: str) -> bool:
        """Release file from quarantine (admin function)"""
        
        file_path = None
        metadata_path = self.quarantine_dir / f"{quarantine_id}_metadata.json"
        
        # Find the quarantined file
        for file in self.quarantine_dir.glob(f"{quarantine_id}_*"):
            if not file.name.endswith('_metadata.json'):
                file_path = file
                break
        
        if not file_path or not file_path.exists():
            return False
        
        try:
            # Log the release
            self.audit_logger.log_quarantine_release(
                user_id=user_id,
                quarantine_id=quarantine_id,
                timestamp=datetime.utcnow()
            )
            
            # Remove quarantined files
            file_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()
            
            logger.info(f"File released from quarantine: {quarantine_id} by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to release file from quarantine {quarantine_id}: {e}")
            return False


class FileValidationMonitor:
    """Monitor file validation metrics and trends"""
    
    def __init__(self):
        self.metrics_cache = {}
        self.cache_expiry = timedelta(hours=1)
    
    async def get_validation_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get file validation statistics"""
        
        # This would typically query a database or metrics store
        # For now, return placeholder data
        return {
            'total_files_processed': 0,
            'files_approved': 0,
            'files_quarantined': 0,
            'files_rejected': 0,
            'average_file_size': 0,
            'common_threats': [],
            'validation_performance': {
                'average_scan_time': 0.0,
                'slowest_scans': []
            }
        }