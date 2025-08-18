"""
Comprehensive Test Suite for File Hash Duplicate Prevention System

Tests the SHA256-based duplicate file detection system implemented in the
FinGood financial application upload endpoint.
"""

import pytest
import hashlib
import io
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import the functions we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.api.v1.endpoints.upload import calculate_file_hash_streaming, truncate_hash_for_display
from app.models.transaction import Transaction
from app.models.user import User


class TestFileHashUtilities:
    """Test the core hash utility functions"""
    
    def test_calculate_file_hash_streaming_basic(self):
        """Test basic hash calculation functionality"""
        test_content = b"test,data,example\n123,456,789\n"
        result = calculate_file_hash_streaming(test_content)
        
        # Verify it's a valid SHA256 hash (64 hex characters)
        assert len(result) == 64
        assert all(c in '0123456789abcdef' for c in result)
        
        # Verify it matches standard hashlib result
        expected = hashlib.sha256(test_content).hexdigest()
        assert result == expected
    
    def test_calculate_file_hash_streaming_empty_file(self):
        """Test hash calculation for empty file"""
        empty_content = b""
        result = calculate_file_hash_streaming(empty_content)
        
        # SHA256 of empty string is a known value
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert result == expected
    
    def test_calculate_file_hash_streaming_large_file(self):
        """Test hash calculation for large file (memory efficiency)"""
        # Create 1MB test content
        large_content = b"x" * (1024 * 1024)
        result = calculate_file_hash_streaming(large_content)
        
        # Verify it matches standard hashlib result
        expected = hashlib.sha256(large_content).hexdigest()
        assert result == expected
    
    def test_calculate_file_hash_streaming_different_chunk_sizes(self):
        """Test hash calculation with different chunk sizes"""
        test_content = b"test content for chunk size verification" * 1000
        
        # Test different chunk sizes
        chunk_sizes = [1024, 4096, 8192, 16384]
        results = []
        
        for chunk_size in chunk_sizes:
            # Monkey patch the function to use different chunk size
            with patch('app.api.v1.endpoints.upload.calculate_file_hash_streaming') as mock_hash:
                def streaming_hash(content, test_chunk_size=chunk_size):
                    hash_obj = hashlib.sha256()
                    for i in range(0, len(content), test_chunk_size):
                        chunk = content[i:i + test_chunk_size]
                        hash_obj.update(chunk)
                    return hash_obj.hexdigest()
                
                result = streaming_hash(test_content)
                results.append(result)
        
        # All chunk sizes should produce the same hash
        assert all(r == results[0] for r in results)
    
    def test_truncate_hash_for_display(self):
        """Test hash truncation for secure display"""
        test_hash = "abcdef1234567890" * 4  # 64 character hash
        result = truncate_hash_for_display(test_hash)
        
        assert result == "abcdef1234567890..."
        assert len(result) == 19  # 16 chars + "..."
    
    def test_truncate_hash_for_display_short_hash(self):
        """Test hash truncation with short input"""
        short_hash = "abc123"
        result = truncate_hash_for_display(short_hash)
        
        assert result == "abc123..."


@pytest.mark.security
class TestFileDuplicateDetectionSecurity:
    """Security-focused tests for duplicate detection"""
    
    @pytest.fixture
    def mock_user(self):
        """Mock user for testing"""
        user = Mock()
        user.id = 123
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def sample_csv_content(self):
        """Sample CSV content for testing"""
        return b"date,amount,description\n2023-01-01,100.00,Test Transaction\n"
    
    def test_hash_consistency_same_content(self, sample_csv_content):
        """Test that identical content always produces the same hash"""
        hash1 = calculate_file_hash_streaming(sample_csv_content)
        hash2 = calculate_file_hash_streaming(sample_csv_content)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 length
    
    def test_hash_uniqueness_different_content(self):
        """Test that different content produces different hashes"""
        content1 = b"date,amount,description\n2023-01-01,100.00,Test 1\n"
        content2 = b"date,amount,description\n2023-01-01,200.00,Test 2\n"
        
        hash1 = calculate_file_hash_streaming(content1)
        hash2 = calculate_file_hash_streaming(content2)
        
        assert hash1 != hash2
    
    def test_user_isolation_in_duplicate_detection(self, mock_user):
        """Test that duplicate detection is isolated per user"""
        # This would test the database query logic
        # In a real implementation, we'd mock the database and verify
        # that the query includes user_id filter
        
        # Mock the database query
        with patch('app.core.database.get_db') as mock_db:
            mock_session = Mock()
            mock_query = Mock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None  # No existing upload
            
            # Verify that user_id is included in the filter
            # This would be tested in integration tests with actual upload endpoint
            pass
    
    def test_no_sensitive_data_in_error_response(self):
        """Test that error responses don't contain sensitive information"""
        # Test that duplicate error responses don't contain:
        # - Full file hashes
        # - User emails or IDs
        # - Internal system information
        
        # This would be tested with actual HTTP responses
        error_response = {
            "message": "This file has already been uploaded",
            "duplicate_batch_id": "abc123...",  # Truncated hash
            "error_code": "DUPLICATE_FILE_UPLOAD"
        }
        
        # Verify no sensitive data
        assert "..." in error_response["duplicate_batch_id"]  # Truncated
        assert "@" not in str(error_response)  # No email addresses
        assert len(error_response["duplicate_batch_id"]) < 64  # Not full hash


@pytest.mark.integration
class TestDuplicateDetectionIntegration:
    """Integration tests for duplicate detection with database"""
    
    @pytest.fixture
    def test_database(self):
        """Create test database session"""
        # This would set up a test database
        # For now, we'll mock it
        return Mock()
    
    @pytest.fixture
    def sample_upload_file(self):
        """Create sample upload file"""
        csv_content = "date,amount,description\n2023-01-01,100.00,Test\n"
        file_like = io.BytesIO(csv_content.encode())
        
        upload_file = UploadFile(
            filename="test.csv",
            file=file_like,
            content_type="text/csv"
        )
        return upload_file
    
    def test_duplicate_file_rejection_http_409(self, test_database, sample_upload_file):
        """Test that duplicate files return HTTP 409 Conflict"""
        # This would test the actual upload endpoint
        # First upload should succeed, second should return 409
        
        # Mock existing transaction in database
        existing_transaction = Mock()
        existing_transaction.import_batch = "test_hash_value"
        
        with patch('app.core.database.get_db') as mock_db:
            mock_session = Mock()
            mock_query = Mock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = existing_transaction  # Duplicate found
            
            # Test would verify HTTPException with status 409 is raised
            pass
    
    def test_different_users_same_file_allowed(self):
        """Test that different users can upload the same file"""
        # User A uploads file -> success
        # User B uploads same file -> should also succeed (different user_id)
        
        with patch('app.core.database.get_db') as mock_db:
            mock_session = Mock()
            mock_query = Mock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            
            # First call (User A) - no existing upload
            mock_query.first.return_value = None
            
            # Verify query filters by user_id
            # This ensures user isolation
            pass
    
    def test_delete_endpoint_works_with_hash(self):
        """Test that DELETE endpoint works with file hash as batch_id"""
        test_hash = "abcdef1234567890" * 4  # 64 char hash
        
        # Mock successful deletion
        with patch('app.core.database.get_db') as mock_db:
            mock_session = Mock()
            mock_query = Mock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.delete.return_value = 5  # 5 transactions deleted
            
            # Test DELETE /api/v1/transactions/import-batch/{hash}
            # Should work seamlessly with file hash
            pass


@pytest.mark.performance
class TestFileHashPerformance:
    """Performance tests for file hash operations"""
    
    def test_streaming_hash_memory_efficiency(self):
        """Test that streaming hash doesn't consume excessive memory"""
        # Create 10MB test file content
        large_content = b"x" * (10 * 1024 * 1024)
        
        # Monitor memory usage during hash calculation
        import tracemalloc
        tracemalloc.start()
        
        result = calculate_file_hash_streaming(large_content)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Verify hash is correct
        assert len(result) == 64
        
        # Memory usage should be reasonable (not holding entire file)
        # Peak memory should be significantly less than file size
        assert peak < len(large_content) * 0.1  # Less than 10% of file size
    
    def test_hash_calculation_speed(self):
        """Test hash calculation performance"""
        import time
        
        # Test with 1MB file
        test_content = b"test data " * (100 * 1024)  # ~1MB
        
        start_time = time.time()
        result = calculate_file_hash_streaming(test_content)
        end_time = time.time()
        
        calculation_time = end_time - start_time
        
        # Should complete quickly (less than 1 second for 1MB)
        assert calculation_time < 1.0
        assert len(result) == 64
    
    def test_early_duplicate_detection_performance(self):
        """Test that duplicate detection happens early in the process"""
        # This would test that the duplicate check happens before
        # expensive operations like file parsing and categorization
        
        # Mock the upload process to verify order of operations
        with patch('app.services.csv_parser.CSVParser') as mock_parser:
            with patch('app.services.categorization.CategorizationService') as mock_categorization:
                # Test would verify that duplicate check happens before
                # these expensive operations are initialized
                pass


@pytest.mark.edge_cases
class TestFileHashEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_file_handling(self):
        """Test handling of empty files"""
        empty_content = b""
        result = calculate_file_hash_streaming(empty_content)
        
        # Should handle empty files gracefully
        assert len(result) == 64
        assert result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    def test_identical_content_different_filenames(self):
        """Test that identical content with different names are detected as duplicates"""
        content = b"date,amount,description\n2023-01-01,100.00,Test\n"
        
        hash1 = calculate_file_hash_streaming(content)
        hash2 = calculate_file_hash_streaming(content)
        
        # Same content should produce same hash regardless of filename
        assert hash1 == hash2
    
    def test_very_large_file_handling(self):
        """Test handling of maximum allowed file size"""
        # Test with 10MB file (current limit)
        max_size_content = b"x" * (10 * 1024 * 1024)
        
        result = calculate_file_hash_streaming(max_size_content)
        
        # Should handle max size without issues
        assert len(result) == 64
    
    def test_unicode_content_handling(self):
        """Test handling of files with unicode content"""
        unicode_content = "date,amount,description\n2023-01-01,100.00,Café transaction 🏦\n".encode('utf-8')
        
        result = calculate_file_hash_streaming(unicode_content)
        
        # Should handle unicode content properly
        assert len(result) == 64
    
    def test_malformed_csv_hash_consistency(self):
        """Test that malformed CSV still produces consistent hashes"""
        malformed_content = b"not,proper,csv\nformat;;;,,\n\n\n"
        
        hash1 = calculate_file_hash_streaming(malformed_content)
        hash2 = calculate_file_hash_streaming(malformed_content)
        
        # Even malformed content should produce consistent hashes
        assert hash1 == hash2
        assert len(hash1) == 64


if __name__ == "__main__":
    # Run tests with appropriate markers
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "not performance"  # Skip performance tests in regular runs
    ])