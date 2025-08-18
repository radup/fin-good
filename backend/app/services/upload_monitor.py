"""
File upload monitoring and rate limiting service for FinGood platform.
Tracks upload patterns, detects anomalies, and enforces security policies.
"""

import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
import logging
from pathlib import Path
import json

from app.core.config import settings
from app.core.audit_logger import security_audit_logger

logger = logging.getLogger(__name__)


@dataclass
class UploadAttempt:
    """Record of a file upload attempt"""
    user_id: str
    filename: str
    file_size: int
    file_hash: str
    timestamp: datetime
    success: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    error: Optional[str] = None


@dataclass
class UploadStats:
    """Upload statistics for monitoring"""
    total_attempts: int
    successful_uploads: int
    failed_uploads: int
    total_bytes: int
    average_file_size: float
    unique_files: int
    suspicious_attempts: int
    rate_limit_violations: int


@dataclass
class SecurityAlert:
    """Security alert for suspicious upload patterns"""
    alert_type: str
    severity: str
    user_id: str
    description: str
    details: Dict[str, Any]
    timestamp: datetime


class UploadMonitor:
    """
    Monitors file upload patterns and enforces security policies.
    """
    
    def __init__(self):
        self.upload_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.file_hashes: Dict[str, List[UploadAttempt]] = defaultdict(list)
        self.ip_attempts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))
        self.security_alerts: List[SecurityAlert] = []
        
        # Load persistent data if available
        self._load_persistent_data()
    
    async def check_upload_permission(
        self,
        user_id: str,
        filename: str,
        file_size: int,
        file_content: bytes,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if upload should be allowed based on rate limits and patterns.
        
        Returns:
            (allowed, reason) - True if allowed, False with reason if blocked
        """
        
        try:
            # Calculate file hash
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Check rate limits
            rate_limit_result = await self._check_rate_limits(user_id, ip_address)
            if not rate_limit_result[0]:
                return rate_limit_result
            
            # Check file size limits
            size_limit_result = await self._check_size_limits(filename, file_size)
            if not size_limit_result[0]:
                return size_limit_result
            
            # Check for duplicate uploads
            duplicate_result = await self._check_duplicate_uploads(user_id, file_hash, filename)
            if not duplicate_result[0]:
                return duplicate_result
            
            # Check for suspicious patterns
            pattern_result = await self._check_suspicious_patterns(
                user_id, filename, file_size, ip_address, user_agent
            )
            if not pattern_result[0]:
                return pattern_result
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking upload permission: {e}")
            return False, "Upload validation error"
    
    async def record_upload_attempt(
        self,
        user_id: str,
        filename: str,
        file_size: int,
        file_content: bytes,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """Record an upload attempt for monitoring"""
        
        try:
            file_hash = hashlib.sha256(file_content).hexdigest()
            timestamp = datetime.utcnow()
            
            attempt = UploadAttempt(
                user_id=user_id,
                filename=filename,
                file_size=file_size,
                file_hash=file_hash,
                timestamp=timestamp,
                success=success,
                ip_address=ip_address,
                user_agent=user_agent,
                error=error
            )
            
            # Store in memory structures
            self.upload_history[user_id].append(attempt)
            self.file_hashes[file_hash].append(attempt)
            
            if ip_address:
                self.ip_attempts[ip_address].append(attempt)
            
            # Analyze for anomalies
            await self._analyze_upload_patterns(user_id, attempt)
            
            # Save persistent data
            await self._save_persistent_data()
            
        except Exception as e:
            logger.error(f"Error recording upload attempt: {e}")
    
    async def _check_rate_limits(
        self, 
        user_id: str, 
        ip_address: Optional[str]
    ) -> Tuple[bool, Optional[str]]:
        """Check rate limiting constraints"""
        
        now = datetime.utcnow()
        
        # Check user rate limits
        user_attempts = self.upload_history[user_id]
        
        # Hourly limit
        hour_ago = now - timedelta(hours=1)
        recent_attempts = [a for a in user_attempts if a.timestamp > hour_ago]
        
        if len(recent_attempts) >= settings.MAX_UPLOADS_PER_HOUR:
            security_audit_logger.log_suspicious_activity(
                description=f"User {user_id} exceeded hourly upload limit",
                user_id=user_id,
                details={
                    "attempts_last_hour": len(recent_attempts),
                    "limit": settings.MAX_UPLOADS_PER_HOUR
                }
            )
            return False, f"Hourly upload limit exceeded ({settings.MAX_UPLOADS_PER_HOUR} uploads/hour)"
        
        # Daily limit
        day_ago = now - timedelta(days=1)
        daily_attempts = [a for a in user_attempts if a.timestamp > day_ago]
        
        if len(daily_attempts) >= settings.MAX_UPLOADS_PER_DAY:
            security_audit_logger.log_suspicious_activity(
                description=f"User {user_id} exceeded daily upload limit",
                user_id=user_id,
                details={
                    "attempts_last_day": len(daily_attempts),
                    "limit": settings.MAX_UPLOADS_PER_DAY
                }
            )
            return False, f"Daily upload limit exceeded ({settings.MAX_UPLOADS_PER_DAY} uploads/day)"
        
        # Check IP-based rate limits (if available)
        if ip_address:
            ip_attempts = self.ip_attempts[ip_address]
            recent_ip_attempts = [a for a in ip_attempts if a.timestamp > hour_ago]
            
            # Allow more attempts per IP than per user (multiple users might share IP)
            ip_hourly_limit = settings.MAX_UPLOADS_PER_HOUR * 3
            
            if len(recent_ip_attempts) >= ip_hourly_limit:
                security_audit_logger.log_suspicious_activity(
                    description=f"IP {ip_address} exceeded hourly upload limit",
                    details={
                        "ip_address": ip_address,
                        "attempts_last_hour": len(recent_ip_attempts),
                        "limit": ip_hourly_limit
                    }
                )
                return False, "IP address upload limit exceeded"
        
        return True, None
    
    async def _check_size_limits(
        self, 
        filename: str, 
        file_size: int
    ) -> Tuple[bool, Optional[str]]:
        """Check file size limits based on file type"""
        
        file_ext = Path(filename).suffix.lower()
        
        # Type-specific limits
        if file_ext == '.csv' and file_size > settings.MAX_CSV_SIZE:
            return False, f"CSV file too large (max: {settings.MAX_CSV_SIZE / (1024*1024):.1f} MB)"
        
        elif file_ext in ['.xlsx', '.xls'] and file_size > settings.MAX_EXCEL_SIZE:
            return False, f"Excel file too large (max: {settings.MAX_EXCEL_SIZE / (1024*1024):.1f} MB)"
        
        # Global limit
        elif file_size > settings.MAX_FILE_SIZE:
            return False, f"File too large (max: {settings.MAX_FILE_SIZE / (1024*1024):.1f} MB)"
        
        return True, None
    
    async def _check_duplicate_uploads(
        self, 
        user_id: str, 
        file_hash: str, 
        filename: str
    ) -> Tuple[bool, Optional[str]]:
        """Check for duplicate file uploads"""
        
        # Check if this exact file was uploaded recently
        recent_uploads = self.file_hashes.get(file_hash, [])
        
        if recent_uploads:
            # Check for uploads in the last hour
            hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_same_file = [
                upload for upload in recent_uploads 
                if upload.timestamp > hour_ago and upload.user_id == user_id
            ]
            
            if recent_same_file:
                logger.warning(f"User {user_id} attempting to upload duplicate file: {filename}")
                return False, "Duplicate file uploaded recently"
        
        return True, None
    
    async def _check_suspicious_patterns(
        self,
        user_id: str,
        filename: str,
        file_size: int,
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> Tuple[bool, Optional[str]]:
        """Check for suspicious upload patterns"""
        
        user_attempts = self.upload_history[user_id]
        
        if len(user_attempts) < 2:
            return True, None  # Not enough history to analyze
        
        recent_attempts = list(user_attempts)[-10:]  # Last 10 attempts
        
        # Check for rapid successive uploads
        if len(recent_attempts) >= 5:
            time_diffs = []
            for i in range(1, len(recent_attempts)):
                diff = (recent_attempts[i].timestamp - recent_attempts[i-1].timestamp).total_seconds()
                time_diffs.append(diff)
            
            avg_interval = sum(time_diffs) / len(time_diffs)
            
            # Flag if uploads are happening too rapidly (less than 10 seconds apart on average)
            if avg_interval < 10:
                await self._create_security_alert(
                    alert_type="rapid_uploads",
                    severity="medium",
                    user_id=user_id,
                    description="Rapid successive file uploads detected",
                    details={
                        "average_interval_seconds": avg_interval,
                        "recent_uploads": len(recent_attempts)
                    }
                )
                return False, "Upload rate too high - please wait between uploads"
        
        # Check for unusual file sizes
        if len(recent_attempts) >= 3:
            sizes = [attempt.file_size for attempt in recent_attempts]
            avg_size = sum(sizes) / len(sizes)
            
            # Flag if current file is significantly larger than typical uploads
            if file_size > avg_size * 10 and file_size > 1024 * 1024:  # 10x larger and > 1MB
                await self._create_security_alert(
                    alert_type="unusual_file_size",
                    severity="low",
                    user_id=user_id,
                    description="Unusually large file upload compared to user history",
                    details={
                        "current_size": file_size,
                        "average_size": avg_size,
                        "size_ratio": file_size / avg_size
                    }
                )
        
        # Check for suspicious filenames
        suspicious_patterns = [
            'test', 'temp', 'tmp', 'sample', 'dummy', 'fake',
            '.exe', '.bat', '.cmd', '.scr', '.com', '.pif'
        ]
        
        filename_lower = filename.lower()
        for pattern in suspicious_patterns:
            if pattern in filename_lower:
                await self._create_security_alert(
                    alert_type="suspicious_filename",
                    severity="medium",
                    user_id=user_id,
                    description=f"Suspicious filename pattern detected: {pattern}",
                    details={
                        "filename": filename,
                        "pattern": pattern
                    }
                )
                # Don't block, just alert
                break
        
        return True, None
    
    async def _analyze_upload_patterns(
        self, 
        user_id: str, 
        attempt: UploadAttempt
    ) -> None:
        """Analyze upload patterns for anomaly detection"""
        
        user_attempts = self.upload_history[user_id]
        
        # Check for failed upload patterns
        recent_failures = [
            a for a in user_attempts 
            if not a.success and a.timestamp > datetime.utcnow() - timedelta(hours=1)
        ]
        
        if len(recent_failures) >= 5:
            await self._create_security_alert(
                alert_type="multiple_failed_uploads",
                severity="high",
                user_id=user_id,
                description="Multiple failed upload attempts detected",
                details={
                    "failed_attempts_last_hour": len(recent_failures),
                    "last_errors": [a.error for a in recent_failures[-3:]]
                }
            )
        
        # Check for unusual upload times
        upload_hour = attempt.timestamp.hour
        
        # Get user's typical upload hours
        successful_attempts = [a for a in user_attempts if a.success and a != attempt]
        if len(successful_attempts) >= 5:
            typical_hours = [a.timestamp.hour for a in successful_attempts]
            hour_counts = defaultdict(int)
            for hour in typical_hours:
                hour_counts[hour] += 1
            
            # If current upload is outside typical hours and it's very late/early
            if hour_counts.get(upload_hour, 0) == 0 and (upload_hour < 6 or upload_hour > 23):
                await self._create_security_alert(
                    alert_type="unusual_upload_time",
                    severity="low",
                    user_id=user_id,
                    description="Upload at unusual time detected",
                    details={
                        "upload_hour": upload_hour,
                        "typical_hours": list(hour_counts.keys())
                    }
                )
    
    async def _create_security_alert(
        self,
        alert_type: str,
        severity: str,
        user_id: str,
        description: str,
        details: Dict[str, Any]
    ) -> None:
        """Create and log security alert"""
        
        alert = SecurityAlert(
            alert_type=alert_type,
            severity=severity,
            user_id=user_id,
            description=description,
            details=details,
            timestamp=datetime.utcnow()
        )
        
        self.security_alerts.append(alert)
        
        # Keep only recent alerts
        cutoff = datetime.utcnow() - timedelta(days=7)
        self.security_alerts = [a for a in self.security_alerts if a.timestamp > cutoff]
        
        # Log to audit system
        security_audit_logger.log_suspicious_activity(
            description=f"Upload security alert: {description}",
            user_id=user_id,
            details={
                "alert_type": alert_type,
                "severity": severity,
                **details
            }
        )
        
        logger.warning(f"Security alert - {alert_type}: {description} (User: {user_id})")
    
    async def get_upload_stats(
        self, 
        user_id: Optional[str] = None, 
        hours: int = 24
    ) -> UploadStats:
        """Get upload statistics"""
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        if user_id:
            attempts = [a for a in self.upload_history[user_id] if a.timestamp > cutoff]
        else:
            attempts = []
            for user_attempts in self.upload_history.values():
                attempts.extend([a for a in user_attempts if a.timestamp > cutoff])
        
        if not attempts:
            return UploadStats(0, 0, 0, 0, 0.0, 0, 0, 0)
        
        successful = [a for a in attempts if a.success]
        failed = [a for a in attempts if not a.success]
        
        total_bytes = sum(a.file_size for a in successful)
        unique_hashes = len(set(a.file_hash for a in attempts))
        
        # Count suspicious attempts (those with security alerts)
        suspicious_count = len([
            alert for alert in self.security_alerts 
            if alert.timestamp > cutoff and (not user_id or alert.user_id == user_id)
        ])
        
        return UploadStats(
            total_attempts=len(attempts),
            successful_uploads=len(successful),
            failed_uploads=len(failed),
            total_bytes=total_bytes,
            average_file_size=total_bytes / len(successful) if successful else 0,
            unique_files=unique_hashes,
            suspicious_attempts=suspicious_count,
            rate_limit_violations=0  # Would need to track this separately
        )
    
    def _load_persistent_data(self) -> None:
        """Load persistent monitoring data from disk"""
        try:
            data_file = Path(settings.UPLOAD_DIR) / "monitor_data.json"
            if data_file.exists():
                with open(data_file, 'r') as f:
                    data = json.load(f)
                
                # Load recent upload history (last 7 days)
                cutoff = datetime.utcnow() - timedelta(days=7)
                for user_id, attempts_data in data.get('upload_history', {}).items():
                    for attempt_data in attempts_data:
                        timestamp = datetime.fromisoformat(attempt_data['timestamp'])
                        if timestamp > cutoff:
                            attempt = UploadAttempt(
                                user_id=attempt_data['user_id'],
                                filename=attempt_data['filename'],
                                file_size=attempt_data['file_size'],
                                file_hash=attempt_data['file_hash'],
                                timestamp=timestamp,
                                success=attempt_data['success'],
                                ip_address=attempt_data.get('ip_address'),
                                user_agent=attempt_data.get('user_agent'),
                                error=attempt_data.get('error')
                            )
                            self.upload_history[user_id].append(attempt)
                            self.file_hashes[attempt.file_hash].append(attempt)
                            
                            if attempt.ip_address:
                                self.ip_attempts[attempt.ip_address].append(attempt)
                
                logger.info("Loaded persistent upload monitoring data")
                
        except Exception as e:
            logger.warning(f"Could not load persistent monitoring data: {e}")
    
    async def _save_persistent_data(self) -> None:
        """Save monitoring data to disk"""
        try:
            # Save only recent data (last 7 days)
            cutoff = datetime.utcnow() - timedelta(days=7)
            
            data = {
                'upload_history': {},
                'last_updated': datetime.utcnow().isoformat()
            }
            
            for user_id, attempts in self.upload_history.items():
                recent_attempts = [a for a in attempts if a.timestamp > cutoff]
                if recent_attempts:
                    data['upload_history'][user_id] = [
                        {
                            'user_id': a.user_id,
                            'filename': a.filename,
                            'file_size': a.file_size,
                            'file_hash': a.file_hash,
                            'timestamp': a.timestamp.isoformat(),
                            'success': a.success,
                            'ip_address': a.ip_address,
                            'user_agent': a.user_agent,
                            'error': a.error
                        }
                        for a in recent_attempts
                    ]
            
            data_file = Path(settings.UPLOAD_DIR) / "monitor_data.json"
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Could not save persistent monitoring data: {e}")


# Global monitor instance
upload_monitor = UploadMonitor()


# Convenience functions
async def check_upload_allowed(
    user_id: str,
    filename: str,
    file_size: int,
    file_content: bytes,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Check if upload should be allowed"""
    return await upload_monitor.check_upload_permission(
        user_id, filename, file_size, file_content, ip_address, user_agent
    )


async def record_upload(
    user_id: str,
    filename: str,
    file_size: int,
    file_content: bytes,
    success: bool,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    error: Optional[str] = None
) -> None:
    """Record upload attempt"""
    await upload_monitor.record_upload_attempt(
        user_id, filename, file_size, file_content, success, 
        ip_address, user_agent, error
    )


async def get_user_upload_stats(user_id: str, hours: int = 24) -> UploadStats:
    """Get upload statistics for a user"""
    return await upload_monitor.get_upload_stats(user_id, hours)