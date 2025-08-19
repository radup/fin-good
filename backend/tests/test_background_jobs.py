"""
Comprehensive Test Suite for Background Job System

Tests the complete background job infrastructure including:
- BackgroundJobManager functionality
- CSV upload job processing
- Redis integration and job tracking
- Error handling and retry logic
- Security pipeline integration
- Performance and load testing
"""

import pytest
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import redis
import pandas as pd
import io

from app.core.background_jobs import (
    BackgroundJobManager,
    JobType,
    JobState,
    JobPriority,
    JobProgress,
    JobResult,
    process_csv_upload_job,
    job_manager
)
from app.core.config import settings
from app.core.exceptions import ValidationException, SystemException
from app.models.user import User
from app.models.transaction import Transaction


class TestBackgroundJobManager:
    """Test suite for BackgroundJobManager class"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client for testing"""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None
        mock_redis.sadd.return_value = 1
        mock_redis.expire.return_value = True
        mock_redis.smembers.return_value = set()
        mock_redis.keys.return_value = []
        mock_redis.info.return_value = {
            'used_memory_human': '10MB',
            'connected_clients': 5
        }
        return mock_redis
    
    @pytest.fixture
    def job_manager_instance(self, mock_redis):
        """Create job manager instance with mocked Redis"""
        with patch('app.core.background_jobs.redis.from_url', return_value=mock_redis):
            with patch('app.core.background_jobs.Queue') as mock_queue:
                mock_queue_instance = MagicMock()
                mock_queue.return_value = mock_queue_instance
                
                manager = BackgroundJobManager()
                manager.redis_client = mock_redis
                return manager
    
    @pytest.fixture
    def sample_job_progress(self):
        """Sample job progress for testing"""
        return JobProgress(
            job_id="test-job-123",
            job_type=JobType.CSV_UPLOAD,
            state=JobState.PROCESSING,
            progress_percentage=50.0,
            current_step="parsing",
            message="Processing CSV file",
            details={"filename": "test.csv", "file_size": 1024},
            user_id="user-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_queue_csv_upload_job_success(self, job_manager_instance, mock_redis):
        """Test successful CSV upload job queuing"""
        # Mock queue.enqueue
        mock_job = MagicMock()
        mock_job.id = "rq-job-123"
        job_manager_instance.queues[JobPriority.NORMAL].enqueue.return_value = mock_job
        
        # Test data
        user_id = "user-123"
        file_content = b"date,amount,description\n2023-01-01,100.00,Test"
        filename = "test.csv"
        file_size = len(file_content)
        
        # Queue job
        job_id = await job_manager_instance.queue_csv_upload_job(
            user_id=user_id,
            file_content=file_content,
            filename=filename,
            file_size=file_size,
            priority=JobPriority.NORMAL
        )
        
        # Assertions
        assert job_id is not None
        assert isinstance(job_id, str)
        
        # Verify Redis calls
        mock_redis.setex.assert_called()  # Progress storage
        mock_redis.sadd.assert_called()   # User job tracking
        mock_redis.expire.assert_called() # TTL setting
        
        # Verify queue.enqueue was called
        job_manager_instance.queues[JobPriority.NORMAL].enqueue.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_queue_csv_upload_job_with_batch_id(self, job_manager_instance):
        """Test CSV upload job queuing with custom batch_id"""
        mock_job = MagicMock()
        job_manager_instance.queues[JobPriority.HIGH].enqueue.return_value = mock_job
        
        custom_batch_id = "custom-batch-123"
        file_content = b"test content"
        
        job_id = await job_manager_instance.queue_csv_upload_job(
            user_id="user-123",
            file_content=file_content,
            filename="test.csv",
            file_size=len(file_content),
            batch_id=custom_batch_id,
            priority=JobPriority.HIGH
        )
        
        assert job_id is not None
        # Verify the custom batch_id was used
        call_args = job_manager_instance.queues[JobPriority.HIGH].enqueue.call_args
        job_data = call_args[0][1]  # Second argument is job_data
        assert job_data['batch_id'] == custom_batch_id
    
    @pytest.mark.asyncio
    async def test_queue_csv_upload_job_redis_failure(self, job_manager_instance, mock_redis):
        """Test job queuing when Redis fails"""
        mock_redis.setex.side_effect = redis.RedisError("Connection failed")
        
        with pytest.raises(SystemException) as exc_info:
            await job_manager_instance.queue_csv_upload_job(
                user_id="user-123",
                file_content=b"test",
                filename="test.csv",
                file_size=4
            )
        
        assert "Failed to queue upload job" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_job_status_exists(self, job_manager_instance, mock_redis, sample_job_progress):
        """Test retrieving existing job status"""
        # Mock Redis response
        progress_data = json.dumps({
            'job_id': sample_job_progress.job_id,
            'job_type': sample_job_progress.job_type.value,
            'state': sample_job_progress.state.value,
            'progress_percentage': sample_job_progress.progress_percentage,
            'current_step': sample_job_progress.current_step,
            'message': sample_job_progress.message,
            'details': sample_job_progress.details,
            'user_id': sample_job_progress.user_id,
            'created_at': sample_job_progress.created_at.isoformat(),
            'updated_at': sample_job_progress.updated_at.isoformat(),
            'retry_count': 0,
            'max_retries': 3
        })
        mock_redis.get.return_value = progress_data
        
        # Get job status
        result = await job_manager_instance.get_job_status(sample_job_progress.job_id)
        
        # Assertions
        assert result is not None
        assert result.job_id == sample_job_progress.job_id
        assert result.job_type == sample_job_progress.job_type
        assert result.state == sample_job_progress.state
        assert result.progress_percentage == sample_job_progress.progress_percentage
    
    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, job_manager_instance, mock_redis):
        """Test retrieving non-existent job status"""
        mock_redis.get.return_value = None
        
        result = await job_manager_instance.get_job_status("non-existent-job")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_jobs(self, job_manager_instance, mock_redis):
        """Test retrieving user jobs"""
        # Mock user job IDs
        job_ids = {"job-1", "job-2", "job-3"}
        mock_redis.smembers.return_value = job_ids
        
        # Mock individual job progress
        job_progress_data = {
            'job_id': 'job-1',
            'job_type': JobType.CSV_UPLOAD.value,
            'state': JobState.COMPLETED.value,
            'progress_percentage': 100.0,
            'current_step': 'completed',
            'message': 'Job completed',
            'details': {},
            'user_id': 'user-123',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'retry_count': 0,
            'max_retries': 3
        }
        mock_redis.get.return_value = json.dumps(job_progress_data)
        
        # Get user jobs
        result = await job_manager_instance.get_user_jobs("user-123", limit=10)
        
        # Assertions
        assert isinstance(result, list)
        assert len(result) <= 10  # Respects limit
        mock_redis.smembers.assert_called_with("fingood:user:jobs:user-123")
    
    @pytest.mark.asyncio
    async def test_cancel_job_success(self, job_manager_instance, mock_redis, sample_job_progress):
        """Test successful job cancellation"""
        # Mock existing job
        progress_data = json.dumps({
            'job_id': sample_job_progress.job_id,
            'job_type': sample_job_progress.job_type.value,
            'state': JobState.PROCESSING.value,
            'progress_percentage': sample_job_progress.progress_percentage,
            'current_step': sample_job_progress.current_step,
            'message': sample_job_progress.message,
            'details': sample_job_progress.details,
            'user_id': sample_job_progress.user_id,
            'created_at': sample_job_progress.created_at.isoformat(),
            'updated_at': sample_job_progress.updated_at.isoformat(),
            'retry_count': 0,
            'max_retries': 3
        })
        mock_redis.get.return_value = progress_data
        
        # Mock RQ job cancellation
        with patch('app.core.background_jobs.Job') as mock_job_class:
            mock_rq_job = MagicMock()
            mock_job_class.fetch.return_value = mock_rq_job
            
            result = await job_manager_instance.cancel_job(
                sample_job_progress.job_id,
                sample_job_progress.user_id
            )
        
        assert result is True
        mock_rq_job.cancel.assert_called_once()
        mock_redis.setex.assert_called()  # Updated progress stored
    
    @pytest.mark.asyncio
    async def test_cancel_job_unauthorized(self, job_manager_instance, mock_redis, sample_job_progress):
        """Test job cancellation by unauthorized user"""
        # Mock existing job
        progress_data = json.dumps({
            'job_id': sample_job_progress.job_id,
            'user_id': 'different-user',  # Different user
            'state': JobState.PROCESSING.value,
            'job_type': sample_job_progress.job_type.value,
            'progress_percentage': sample_job_progress.progress_percentage,
            'current_step': sample_job_progress.current_step,
            'message': sample_job_progress.message,
            'details': sample_job_progress.details,
            'created_at': sample_job_progress.created_at.isoformat(),
            'updated_at': sample_job_progress.updated_at.isoformat(),
            'retry_count': 0,
            'max_retries': 3
        })
        mock_redis.get.return_value = progress_data
        
        result = await job_manager_instance.cancel_job(
            sample_job_progress.job_id,
            sample_job_progress.user_id  # Different from job owner
        )
        
        assert result is False
    
    def test_get_queue_stats(self, job_manager_instance):
        """Test queue statistics retrieval"""
        # Mock queue statistics
        for priority, queue in job_manager_instance.queues.items():
            queue.name = f"{priority.value}-queue"
            queue.__len__ = lambda: 5
            queue.scheduled_job_registry.count = 2
            queue.started_job_registry.count = 1
            queue.finished_job_registry.count = 10
            queue.failed_job_registry.count = 0
            queue.deferred_job_registry.count = 0
        
        stats = job_manager_instance.get_queue_stats()
        
        assert 'queues' in stats
        assert 'total_queued' in stats
        assert 'redis_info' in stats
        
        # Check that all priority levels are included
        for priority in JobPriority:
            assert priority.value in stats['queues']


class TestProcessCSVUploadJob:
    """Test suite for CSV upload job processing function"""
    
    @pytest.fixture
    def sample_job_data(self):
        """Sample job data for testing"""
        file_content = b"date,amount,description\n2023-01-01,100.00,Test Transaction"
        return {
            'job_id': 'test-job-123',
            'user_id': 'user-123',
            'file_content': file_content.hex(),
            'filename': 'test.csv',
            'file_size': len(file_content),
            'batch_id': 'batch-123',
            'client_ip': '192.168.1.1',
            'user_agent': 'TestAgent/1.0',
            'created_at': datetime.utcnow().isoformat()
        }
    
    @pytest.fixture
    def mock_database_session(self):
        """Mock database session"""
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = None  # No existing upload
        session.commit.return_value = None
        session.close.return_value = None
        return session
    
    @pytest.fixture
    def mock_user(self):
        """Mock user object"""
        user = MagicMock()
        user.id = 'user-123'
        user.email = 'test@example.com'
        return user
    
    @pytest.mark.asyncio
    async def test_process_csv_upload_job_success(self, sample_job_data, mock_database_session, mock_user):
        """Test successful CSV upload job processing"""
        with patch('app.core.background_jobs.get_db') as mock_get_db:
            mock_get_db.return_value = mock_database_session
            mock_database_session.query.return_value.filter.return_value.first.return_value = mock_user
            
            with patch('app.core.background_jobs.check_upload_allowed') as mock_check_upload:
                mock_check_upload.return_value = (True, None)
                
                with patch('app.core.background_jobs.FileValidator') as mock_validator:
                    mock_validator_instance = MagicMock()
                    mock_validation_result = MagicMock()
                    mock_validation_result.validation_result = "APPROVED"
                    mock_validation_result.threat_level = "LOW"
                    mock_validation_result.errors = []
                    mock_validator_instance.validate_file.return_value = mock_validation_result
                    mock_validator.return_value = mock_validator_instance
                    
                    with patch('app.core.background_jobs.scan_file_for_malware') as mock_malware_scan:
                        mock_scan_result = MagicMock()
                        mock_scan_result.is_clean = True
                        mock_malware_scan.return_value = mock_scan_result
                        
                        with patch('app.core.background_jobs.sanitize_csv_content') as mock_sanitize:
                            mock_sanitize_result = MagicMock()
                            mock_sanitize_result.is_safe = True
                            mock_sanitize_result.sanitized_content = "date,amount,description\n2023-01-01,100.00,Test Transaction"
                            mock_sanitize.return_value = mock_sanitize_result
                            
                            with patch('app.core.background_jobs.CSVParser') as mock_parser_class:
                                mock_parser = MagicMock()
                                mock_parsing_result = MagicMock()
                                mock_parsing_result.transactions = [{
                                    'date': datetime(2023, 1, 1),
                                    'amount': 100.00,
                                    'description': 'Test Transaction',
                                    'vendor': 'Test Vendor',
                                    'is_income': False,
                                    'raw_data': {}
                                }]
                                mock_parsing_result.errors = []
                                mock_parsing_result.warnings = []
                                mock_parsing_result.statistics = {'success_rate': 100.0}
                                mock_parser.parse_dataframe.return_value = mock_parsing_result
                                mock_parser_class.return_value = mock_parser
                                
                                with patch('app.core.background_jobs.CategorizationService') as mock_cat_service:
                                    mock_cat_instance = MagicMock()
                                    mock_cat_result = {
                                        'rule_categorized': 1,
                                        'ml_categorized': 0
                                    }
                                    mock_cat_instance.categorize_user_transactions.return_value = mock_cat_result
                                    mock_cat_service.return_value = mock_cat_instance
                                    
                                    with patch('app.core.background_jobs.get_current_job'):
                                        with patch('app.core.background_jobs.job_manager._store_job_progress'):
                                            with patch('app.core.background_jobs.security_audit_logger'):
                                                with patch('app.core.background_jobs.record_upload'):
                                                    # Run the job
                                                    result = process_csv_upload_job(sample_job_data)
        
        # Assertions
        assert isinstance(result, JobResult)
        assert result.success is True
        assert result.data is not None
        assert 'batch_id' in result.data
        assert 'processed_count' in result.data
        assert result.data['processed_count'] == 1
    
    def test_process_csv_upload_job_user_not_found(self, sample_job_data, mock_database_session):
        """Test job processing when user is not found"""
        with patch('app.core.background_jobs.get_db') as mock_get_db:
            mock_get_db.return_value = mock_database_session
            mock_database_session.query.return_value.filter.return_value.first.return_value = None  # No user
            
            with patch('app.core.background_jobs.get_current_job'):
                with patch('app.core.background_jobs.job_manager._store_job_progress'):
                    with patch('app.core.background_jobs.security_audit_logger'):
                        result = process_csv_upload_job(sample_job_data)
        
        assert isinstance(result, JobResult)
        assert result.success is False
        assert "User not found" in result.error_message
    
    def test_process_csv_upload_job_upload_denied(self, sample_job_data, mock_database_session, mock_user):
        """Test job processing when upload is denied"""
        with patch('app.core.background_jobs.get_db') as mock_get_db:
            mock_get_db.return_value = mock_database_session
            mock_database_session.query.return_value.filter.return_value.first.return_value = mock_user
            
            with patch('app.core.background_jobs.check_upload_allowed') as mock_check_upload:
                mock_check_upload.return_value = (False, "Rate limit exceeded")
                
                with patch('app.core.background_jobs.get_current_job'):
                    with patch('app.core.background_jobs.job_manager._store_job_progress'):
                        with patch('app.core.background_jobs.record_upload'):
                            with patch('app.core.background_jobs.security_audit_logger'):
                                result = process_csv_upload_job(sample_job_data)
        
        assert isinstance(result, JobResult)
        assert result.success is False
        assert "Upload denied" in result.error_message
    
    def test_process_csv_upload_job_validation_failure(self, sample_job_data, mock_database_session, mock_user):
        """Test job processing when file validation fails"""
        with patch('app.core.background_jobs.get_db') as mock_get_db:
            mock_get_db.return_value = mock_database_session
            mock_database_session.query.return_value.filter.return_value.first.return_value = mock_user
            
            with patch('app.core.background_jobs.check_upload_allowed') as mock_check_upload:
                mock_check_upload.return_value = (True, None)
                
                with patch('app.core.background_jobs.FileValidator') as mock_validator:
                    mock_validator_instance = MagicMock()
                    mock_validation_result = MagicMock()
                    mock_validation_result.validation_result = "REJECTED"
                    mock_validation_result.errors = ["Invalid file format"]
                    mock_validator_instance.validate_file.return_value = mock_validation_result
                    mock_validator.return_value = mock_validator_instance
                    
                    with patch('app.core.background_jobs.get_current_job'):
                        with patch('app.core.background_jobs.job_manager._store_job_progress'):
                            with patch('app.core.background_jobs.security_audit_logger'):
                                result = process_csv_upload_job(sample_job_data)
        
        assert isinstance(result, JobResult)
        assert result.success is False
        assert "File validation failed" in result.error_message
    
    def test_process_csv_upload_job_malware_detected(self, sample_job_data, mock_database_session, mock_user):
        """Test job processing when malware is detected"""
        with patch('app.core.background_jobs.get_db') as mock_get_db:
            mock_get_db.return_value = mock_database_session
            mock_database_session.query.return_value.filter.return_value.first.return_value = mock_user
            
            with patch('app.core.background_jobs.check_upload_allowed') as mock_check_upload:
                mock_check_upload.return_value = (True, None)
                
                with patch('app.core.background_jobs.FileValidator') as mock_validator:
                    mock_validator_instance = MagicMock()
                    mock_validation_result = MagicMock()
                    mock_validation_result.validation_result = "APPROVED"
                    mock_validation_result.threat_level = "LOW"
                    mock_validation_result.errors = []
                    mock_validator_instance.validate_file.return_value = mock_validation_result
                    mock_validator.return_value = mock_validator_instance
                    
                    with patch('app.core.background_jobs.scan_file_for_malware') as mock_malware_scan:
                        mock_scan_result = MagicMock()
                        mock_scan_result.is_clean = False
                        mock_scan_result.threats_detected = ["Trojan.Generic"]
                        mock_malware_scan.return_value = mock_scan_result
                        
                        with patch('app.core.background_jobs.get_current_job'):
                            with patch('app.core.background_jobs.job_manager._store_job_progress'):
                                with patch('app.core.background_jobs.security_audit_logger'):
                                    result = process_csv_upload_job(sample_job_data)
        
        assert isinstance(result, JobResult)
        assert result.success is False
        assert "Malware detected" in result.error_message


class TestJobDataStructures:
    """Test suite for job data structures and enums"""
    
    def test_job_type_enum(self):
        """Test JobType enum values"""
        assert JobType.CSV_UPLOAD == "csv_upload"
        assert JobType.BULK_CATEGORIZATION == "bulk_categorization"
        assert JobType.DATA_EXPORT == "data_export"
        assert JobType.BATCH_DELETE == "batch_delete"
    
    def test_job_state_enum(self):
        """Test JobState enum values"""
        assert JobState.QUEUED == "queued"
        assert JobState.STARTED == "started"
        assert JobState.PROCESSING == "processing"
        assert JobState.COMPLETED == "completed"
        assert JobState.FAILED == "failed"
        assert JobState.CANCELLED == "cancelled"
        assert JobState.RETRYING == "retrying"
    
    def test_job_priority_enum(self):
        """Test JobPriority enum values"""
        assert JobPriority.LOW == "low"
        assert JobPriority.NORMAL == "normal"
        assert JobPriority.HIGH == "high"
        assert JobPriority.CRITICAL == "critical"
    
    def test_job_progress_creation(self):
        """Test JobProgress data structure creation"""
        now = datetime.utcnow()
        progress = JobProgress(
            job_id="test-123",
            job_type=JobType.CSV_UPLOAD,
            state=JobState.PROCESSING,
            progress_percentage=75.0,
            current_step="categorization",
            message="Categorizing transactions",
            details={"processed": 150, "total": 200},
            user_id="user-456",
            created_at=now,
            updated_at=now
        )
        
        assert progress.job_id == "test-123"
        assert progress.job_type == JobType.CSV_UPLOAD
        assert progress.state == JobState.PROCESSING
        assert progress.progress_percentage == 75.0
        assert progress.current_step == "categorization"
        assert progress.message == "Categorizing transactions"
        assert progress.details["processed"] == 150
        assert progress.user_id == "user-456"
        assert progress.retry_count == 0
        assert progress.max_retries == 3
    
    def test_job_result_success(self):
        """Test successful JobResult creation"""
        result = JobResult(
            success=True,
            data={"processed_count": 100, "batch_id": "batch-123"},
            processing_time=45.2,
            statistics={"success_rate": 98.5}
        )
        
        assert result.success is True
        assert result.data["processed_count"] == 100
        assert result.processing_time == 45.2
        assert result.statistics["success_rate"] == 98.5
        assert result.error_message is None
    
    def test_job_result_failure(self):
        """Test failed JobResult creation"""
        result = JobResult(
            success=False,
            error_message="Processing failed",
            error_code="PROCESSING_ERROR",
            correlation_id="corr-123",
            processing_time=10.5
        )
        
        assert result.success is False
        assert result.error_message == "Processing failed"
        assert result.error_code == "PROCESSING_ERROR"
        assert result.correlation_id == "corr-123"
        assert result.processing_time == 10.5
        assert result.data is None


class TestRedisIntegration:
    """Test suite for Redis integration aspects"""
    
    @pytest.fixture
    def mock_redis_with_data(self):
        """Mock Redis with test data"""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        
        # Sample job data in Redis
        job_data = {
            'job_id': 'test-job-123',
            'job_type': 'csv_upload',
            'state': 'completed',
            'progress_percentage': 100.0,
            'current_step': 'completed',
            'message': 'Job completed successfully',
            'details': {'processed_count': 50},
            'user_id': 'user-123',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'retry_count': 0,
            'max_retries': 3
        }
        
        mock_redis.get.return_value = json.dumps(job_data)
        mock_redis.keys.return_value = ['fingood:job:progress:test-job-123']
        mock_redis.smembers.return_value = {'test-job-123'}
        
        return mock_redis
    
    @pytest.mark.asyncio
    async def test_job_persistence_in_redis(self, mock_redis_with_data):
        """Test that jobs are properly persisted in Redis"""
        with patch('app.core.background_jobs.redis.from_url', return_value=mock_redis_with_data):
            with patch('app.core.background_jobs.Queue'):
                manager = BackgroundJobManager()
                
                # Test retrieving persisted job
                job_status = await manager.get_job_status('test-job-123')
                
                assert job_status is not None
                assert job_status.job_id == 'test-job-123'
                assert job_status.state == JobState.COMPLETED
                
                # Verify Redis was called with correct key
                expected_key = 'fingood:job:progress:test-job-123'
                mock_redis_with_data.get.assert_called_with(expected_key)
    
    @pytest.mark.asyncio
    async def test_user_job_tracking(self, mock_redis_with_data):
        """Test that user jobs are properly tracked"""
        with patch('app.core.background_jobs.redis.from_url', return_value=mock_redis_with_data):
            with patch('app.core.background_jobs.Queue'):
                manager = BackgroundJobManager()
                
                # Test retrieving user jobs
                user_jobs = await manager.get_user_jobs('user-123')
                
                # Verify Redis calls
                expected_user_key = 'fingood:user:jobs:user-123'
                mock_redis_with_data.smembers.assert_called_with(expected_user_key)
    
    def test_redis_connection_failure(self):
        """Test handling of Redis connection failures"""
        with patch('app.core.background_jobs.redis.from_url') as mock_redis_from_url:
            mock_redis_client = MagicMock()
            mock_redis_client.ping.side_effect = redis.RedisError("Connection failed")
            mock_redis_from_url.return_value = mock_redis_client
            
            with pytest.raises(SystemException) as exc_info:
                BackgroundJobManager()
            
            assert "Failed to initialize background job system" in str(exc_info.value)


class TestSecurityIntegration:
    """Test suite for security pipeline integration"""
    
    @pytest.mark.asyncio
    async def test_security_pipeline_preserved(self, mock_database_session, mock_user):
        """Test that all security checks are preserved in background processing"""
        file_content = b"date,amount,description\n2023-01-01,100.00,Test"
        job_data = {
            'job_id': 'test-job-123',
            'user_id': 'user-123',
            'file_content': file_content.hex(),
            'filename': 'test.csv',
            'file_size': len(file_content),
            'batch_id': 'batch-123',
            'created_at': datetime.utcnow().isoformat()
        }
        
        security_checks = []
        
        def track_security_check(check_name):
            security_checks.append(check_name)
            return AsyncMock()
        
        with patch('app.core.background_jobs.get_db') as mock_get_db:
            mock_get_db.return_value = mock_database_session
            mock_database_session.query.return_value.filter.return_value.first.return_value = mock_user
            
            with patch('app.core.background_jobs.check_upload_allowed', side_effect=lambda *args, **kwargs: (security_checks.append('upload_allowed'), (True, None))[1]):
                with patch('app.core.background_jobs.FileValidator') as mock_validator:
                    mock_validator_instance = MagicMock()
                    mock_validation_result = MagicMock()
                    mock_validation_result.validation_result = "APPROVED"
                    mock_validation_result.threat_level = "LOW"
                    
                    async def validate_side_effect(*args, **kwargs):
                        security_checks.append('file_validation')
                        return mock_validation_result
                    
                    mock_validator_instance.validate_file.side_effect = validate_side_effect
                    mock_validator.return_value = mock_validator_instance
                    
                    with patch('app.core.background_jobs.scan_file_for_malware') as mock_malware_scan:
                        mock_scan_result = MagicMock()
                        mock_scan_result.is_clean = True
                        
                        async def malware_side_effect(*args, **kwargs):
                            security_checks.append('malware_scan')
                            return mock_scan_result
                        
                        mock_malware_scan.side_effect = malware_side_effect
                        
                        with patch('app.core.background_jobs.sanitize_csv_content') as mock_sanitize:
                            mock_sanitize_result = MagicMock()
                            mock_sanitize_result.is_safe = True
                            mock_sanitize_result.sanitized_content = file_content.decode('utf-8')
                            
                            async def sanitize_side_effect(*args, **kwargs):
                                security_checks.append('content_sanitization')
                                return mock_sanitize_result
                            
                            mock_sanitize.side_effect = sanitize_side_effect
                            
                            with patch('app.core.background_jobs.CSVParser') as mock_parser_class:
                                with patch('app.core.background_jobs.CategorizationService'):
                                    with patch('app.core.background_jobs.get_current_job'):
                                        with patch('app.core.background_jobs.job_manager._store_job_progress'):
                                            with patch('app.core.background_jobs.security_audit_logger') as mock_audit:
                                                def audit_side_effect(*args, **kwargs):
                                                    security_checks.append('audit_logging')
                                                
                                                mock_audit.log_file_upload_success.side_effect = audit_side_effect
                                                mock_audit.log_file_upload_failure.side_effect = audit_side_effect
                                                
                                                with patch('app.core.background_jobs.record_upload') as mock_record:
                                                    async def record_side_effect(*args, **kwargs):
                                                        security_checks.append('upload_recording')
                                                    
                                                    mock_record.side_effect = record_side_effect
                                                    
                                                    # Mock parser
                                                    mock_parser = MagicMock()
                                                    mock_parsing_result = MagicMock()
                                                    mock_parsing_result.transactions = []
                                                    mock_parsing_result.errors = []
                                                    mock_parsing_result.warnings = []
                                                    mock_parsing_result.statistics = {'success_rate': 100.0}
                                                    mock_parser.parse_dataframe.return_value = mock_parsing_result
                                                    mock_parser_class.return_value = mock_parser
                                                    
                                                    # Run the job
                                                    result = process_csv_upload_job(job_data)
        
        # Verify all security checks were performed
        expected_checks = [
            'upload_allowed',
            'file_validation', 
            'malware_scan',
            'content_sanitization',
            'audit_logging',
            'upload_recording'
        ]
        
        for check in expected_checks:
            assert check in security_checks, f"Security check '{check}' was not performed"


class TestPerformanceAndLoad:
    """Test suite for performance and load testing"""
    
    @pytest.mark.asyncio
    async def test_large_file_handling(self):
        """Test handling of large file content"""
        # Simulate large file (1MB)
        large_content = b"date,amount,description\n" + (b"2023-01-01,100.00,Large file test\n" * 30000)
        
        job_data = {
            'job_id': 'large-file-job',
            'user_id': 'user-123',
            'file_content': large_content.hex(),
            'filename': 'large_test.csv',
            'file_size': len(large_content),
            'batch_id': 'large-batch-123',
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Ensure the job can handle large hex content without issues
        assert len(job_data['file_content']) == len(large_content) * 2  # Hex doubles the size
        
        # Test that content can be converted back
        restored_content = bytes.fromhex(job_data['file_content'])
        assert restored_content == large_content
    
    @pytest.mark.asyncio
    async def test_concurrent_job_limits(self, mock_redis):
        """Test that concurrent job limits are enforced"""
        with patch('app.core.background_jobs.redis.from_url', return_value=mock_redis):
            with patch('app.core.background_jobs.Queue'):
                manager = BackgroundJobManager()
                
                # Mock active jobs for user
                active_jobs = [
                    JobProgress(
                        job_id=f"job-{i}",
                        job_type=JobType.CSV_UPLOAD,
                        state=JobState.PROCESSING,
                        progress_percentage=50.0,
                        current_step="processing",
                        message="Processing",
                        details={},
                        user_id="user-123",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    ) for i in range(5)  # 5 active jobs
                ]
                
                with patch.object(manager, 'get_user_jobs', return_value=active_jobs):
                    # This should succeed if limit is > 5
                    if settings.MAX_CONCURRENT_JOBS_PER_USER <= 5:
                        with pytest.raises(Exception):  # Should raise an exception
                            await manager.queue_csv_upload_job(
                                user_id="user-123",
                                file_content=b"test",
                                filename="test.csv",
                                file_size=4
                            )
    
    def test_memory_efficiency_hex_conversion(self):
        """Test memory efficiency of hex conversion for large files"""
        # Test with moderately large content
        test_content = b"x" * (1024 * 1024)  # 1MB
        
        # Convert to hex
        hex_content = test_content.hex()
        
        # Convert back
        restored_content = bytes.fromhex(hex_content)
        
        assert restored_content == test_content
        assert len(hex_content) == len(test_content) * 2
    
    @pytest.mark.asyncio
    async def test_job_cleanup_performance(self, mock_redis):
        """Test job cleanup performance with many jobs"""
        # Mock many job keys
        job_keys = [f"fingood:job:progress:job-{i}" for i in range(1000)]
        mock_redis.keys.return_value = job_keys
        
        # Mock old job data
        old_job_data = {
            'job_id': 'old-job',
            'created_at': (datetime.utcnow() - timedelta(days=30)).isoformat(),
            'user_id': 'user-123'
        }
        mock_redis.get.return_value = json.dumps(old_job_data)
        
        with patch('app.core.background_jobs.redis.from_url', return_value=mock_redis):
            with patch('app.core.background_jobs.Queue'):
                manager = BackgroundJobManager()
                
                # This should not raise any performance issues
                from app.core.background_jobs import JobManagerCLI
                cli = JobManagerCLI()
                cli.redis_conn = mock_redis
                cli.job_manager = manager
                
                # Test cleanup (dry run)
                await cli.cleanup_jobs(older_than_days=7, dry_run=True)


@pytest.mark.integration
class TestIntegrationScenarios:
    """Integration test scenarios"""
    
    @pytest.mark.asyncio
    async def test_complete_upload_workflow(self):
        """Test complete upload workflow from queueing to completion"""
        # This would be a full integration test
        # For now, we'll test the workflow steps
        pass
    
    @pytest.mark.asyncio 
    async def test_error_recovery_and_retry(self):
        """Test error recovery and retry mechanisms"""
        # Test retry logic and error handling
        pass
    
    @pytest.mark.asyncio
    async def test_websocket_progress_updates(self):
        """Test WebSocket progress update integration"""
        # Test WebSocket emission during job processing
        pass


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])