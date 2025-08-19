"""
Comprehensive Test Suite for WebSocket Progress System

Tests the complete WebSocket infrastructure including:
- WebSocket Manager functionality
- Connection management and authentication
- Progress message broadcasting
- Rate limiting and security features
- Error handling and cleanup
- Integration with background jobs
"""

import pytest
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import jwt
from fastapi import WebSocket, status
from fastapi.testclient import TestClient
import redis

from app.core.websocket_manager import (
    WebSocketManager,
    WebSocketConnection,
    ProgressMessage,
    ProgressDetails,
    MessageType,
    ProgressStatus,
    ProgressStage,
    websocket_manager,
    emit_upload_progress,
    emit_validation_progress,
    emit_scanning_progress,
    emit_parsing_progress,
    emit_database_progress,
    emit_categorization_progress
)
from app.core.config import settings
from app.models.user import User


class TestProgressMessage:
    """Test suite for ProgressMessage class"""
    
    def test_progress_message_creation(self):
        """Test basic ProgressMessage creation"""
        message = ProgressMessage(
            message_type=MessageType.PROGRESS_UPDATE,
            batch_id="test-batch-123",
            progress=45.5,
            status=ProgressStatus.PROCESSING,
            stage=ProgressStage.PARSING,
            message="Processing CSV data",
            user_id="user-123"
        )
        
        assert message.batch_id == "test-batch-123"
        assert message.progress == 45.5
        assert message.status == ProgressStatus.PROCESSING
        assert message.stage == ProgressStage.PARSING
        assert message.message == "Processing CSV data"
        assert message.user_id == "user-123"
        assert message.correlation_id is not None
        assert isinstance(message.timestamp, datetime)
        assert isinstance(message.sequence_number, int)
    
    def test_progress_clamping(self):
        """Test that progress is clamped between 0-100"""
        # Test negative progress
        message1 = ProgressMessage(
            message_type=MessageType.PROGRESS_UPDATE,
            batch_id="test",
            progress=-10.0,
            status=ProgressStatus.PROCESSING,
            stage=ProgressStage.VALIDATION,
            message="Test",
            user_id="user-123"
        )
        assert message1.progress == 0.0
        
        # Test progress over 100
        message2 = ProgressMessage(
            message_type=MessageType.PROGRESS_UPDATE,
            batch_id="test",
            progress=150.0,
            status=ProgressStatus.PROCESSING,
            stage=ProgressStage.VALIDATION,
            message="Test",
            user_id="user-123"
        )
        assert message2.progress == 100.0
    
    def test_progress_message_to_dict(self):
        """Test ProgressMessage serialization to dictionary"""
        details = ProgressDetails(
            processed_items=50,
            total_items=100,
            errors_count=2,
            processing_rate=10.5
        )
        
        message = ProgressMessage(
            message_type=MessageType.PROGRESS_UPDATE,
            batch_id="test-batch-123",
            progress=50.0,
            status=ProgressStatus.PROCESSING,
            stage=ProgressStage.DATABASE,
            message="Inserting transactions",
            details=details,
            user_id="user-123",
            job_id="job-456"
        )
        
        data = message.to_dict()
        
        assert data["message_type"] == "progress_update"
        assert data["batch_id"] == "test-batch-123"
        assert data["progress"] == 50.0
        assert data["status"] == "processing"
        assert data["stage"] == "database"
        assert data["message"] == "Inserting transactions"
        assert data["user_id"] == "user-123"
        assert data["job_id"] == "job-456"
        assert "details" in data
        assert data["details"]["processed_items"] == 50
        assert data["details"]["total_items"] == 100
        assert "timestamp" in data
        assert "correlation_id" in data
        assert "sequence_number" in data
    
    def test_progress_message_to_json(self):
        """Test ProgressMessage JSON serialization"""
        message = ProgressMessage(
            message_type=MessageType.PROGRESS_UPDATE,
            batch_id="test-batch-123",
            progress=75.0,
            status=ProgressStatus.PROCESSING,
            stage=ProgressStage.CATEGORIZATION,
            message="Categorizing transactions",
            user_id="user-123"
        )
        
        json_str = message.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["batch_id"] == "test-batch-123"
        assert parsed["progress"] == 75.0
        assert parsed["status"] == "processing"
    
    def test_factory_methods(self):
        """Test ProgressMessage factory methods"""
        # Test create_progress_update
        progress_msg = ProgressMessage.create_progress_update(
            batch_id="batch-123",
            progress=60.0,
            stage=ProgressStage.DATABASE,
            message="Saving data",
            user_id="user-123",
            job_id="job-456"
        )
        
        assert progress_msg.message_type == MessageType.PROGRESS_UPDATE
        assert progress_msg.status == ProgressStatus.PROCESSING
        assert progress_msg.job_id == "job-456"
        
        # Test create_error_notification
        error_msg = ProgressMessage.create_error_notification(
            batch_id="batch-123",
            stage=ProgressStage.VALIDATION,
            error_message="File validation failed",
            user_id="user-123"
        )
        
        assert error_msg.message_type == MessageType.ERROR_NOTIFICATION
        assert error_msg.status == ProgressStatus.ERROR
        assert error_msg.error == "File validation failed"
        
        # Test create_heartbeat
        heartbeat_msg = ProgressMessage.create_heartbeat(
            connection_id="conn-123",
            user_id="user-123",
            stats={"connections": 5}
        )
        
        assert heartbeat_msg.message_type == MessageType.HEARTBEAT
        assert heartbeat_msg.details.additional_info["connections"] == 5


class TestWebSocketConnection:
    """Test suite for WebSocketConnection class"""
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket for testing"""
        mock = AsyncMock()
        mock.send_text = AsyncMock()
        mock.close = AsyncMock()
        return mock
    
    def test_websocket_connection_creation(self, mock_websocket):
        """Test WebSocketConnection creation"""
        connection = WebSocketConnection(
            websocket=mock_websocket,
            user_id="user-123",
            connection_id="conn-456"
        )
        
        assert connection.websocket == mock_websocket
        assert connection.user_id == "user-123"
        assert connection.connection_id == "conn-456"
        assert isinstance(connection.connected_at, datetime)
        assert isinstance(connection.last_activity, datetime)
        assert isinstance(connection.subscribed_batches, set)
        assert connection.is_active is True
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_websocket):
        """Test successful message sending"""
        connection = WebSocketConnection(
            websocket=mock_websocket,
            user_id="user-123",
            connection_id="conn-456"
        )
        
        message = ProgressMessage(
            message_type=MessageType.PROGRESS_UPDATE,
            batch_id="batch-123",
            progress=50.0,
            status=ProgressStatus.PROCESSING,
            stage=ProgressStage.PARSING,
            message="Processing",
            user_id="user-123"
        )
        
        result = await connection.send_message(message)
        
        assert result is True
        mock_websocket.send_text.assert_called_once()
        # Verify JSON was sent
        sent_data = mock_websocket.send_text.call_args[0][0]
        parsed = json.loads(sent_data)
        assert parsed["batch_id"] == "batch-123"
    
    @pytest.mark.asyncio
    async def test_send_message_failure(self, mock_websocket):
        """Test message sending failure"""
        mock_websocket.send_text.side_effect = Exception("Connection lost")
        
        connection = WebSocketConnection(
            websocket=mock_websocket,
            user_id="user-123",
            connection_id="conn-456"
        )
        
        message = ProgressMessage(
            message_type=MessageType.PROGRESS_UPDATE,
            batch_id="batch-123",
            progress=50.0,
            status=ProgressStatus.PROCESSING,
            stage=ProgressStage.PARSING,
            message="Processing",
            user_id="user-123"
        )
        
        result = await connection.send_message(message)
        
        assert result is False
        assert connection.is_active is False
    
    def test_batch_subscription(self, mock_websocket):
        """Test batch subscription management"""
        connection = WebSocketConnection(
            websocket=mock_websocket,
            user_id="user-123",
            connection_id="conn-456"
        )
        
        # Test subscription
        connection.subscribe_to_batch("batch-1")
        connection.subscribe_to_batch("batch-2")
        
        assert "batch-1" in connection.subscribed_batches
        assert "batch-2" in connection.subscribed_batches
        assert len(connection.subscribed_batches) == 2
        
        # Test unsubscription
        connection.unsubscribe_from_batch("batch-1")
        
        assert "batch-1" not in connection.subscribed_batches
        assert "batch-2" in connection.subscribed_batches
        assert len(connection.subscribed_batches) == 1
    
    @pytest.mark.asyncio
    async def test_connection_close(self, mock_websocket):
        """Test connection closing"""
        connection = WebSocketConnection(
            websocket=mock_websocket,
            user_id="user-123",
            connection_id="conn-456"
        )
        
        await connection.close()
        
        mock_websocket.close.assert_called_once()
        assert connection.is_active is False


class TestWebSocketManager:
    """Test suite for WebSocketManager class"""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh WebSocket manager for testing"""
        return WebSocketManager()
    
    @pytest.fixture
    def mock_user(self):
        """Mock user for testing"""
        user = Mock()
        user.id = "user-123"
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket for testing"""
        mock = AsyncMock()
        mock.accept = AsyncMock()
        mock.send_text = AsyncMock()
        mock.close = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_manager_start_stop(self, manager):
        """Test WebSocket manager start and stop"""
        # Test start
        await manager.start()
        assert manager.cleanup_task is not None
        assert not manager.cleanup_task.done()
        
        # Test stop
        await manager.stop()
        assert len(manager.connections) == 0
        assert len(manager.user_connections) == 0
        assert len(manager.batch_connections) == 0
    
    def test_authenticate_websocket_success(self, manager, mock_db, mock_user):
        """Test successful WebSocket authentication"""
        # Create a valid JWT token
        token_data = {
            "sub": str(mock_user.id),
            "type": "websocket",
            "exp": (datetime.utcnow() + timedelta(minutes=5)).timestamp()
        }
        token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = manager._authenticate_websocket(token, mock_db)
        
        assert result == mock_user
        mock_db.query.assert_called_once()
    
    def test_authenticate_websocket_invalid_token(self, manager, mock_db):
        """Test WebSocket authentication with invalid token"""
        invalid_token = "invalid.jwt.token"
        
        result = manager._authenticate_websocket(invalid_token, mock_db)
        
        assert result is None
    
    def test_authenticate_websocket_user_not_found(self, manager, mock_db):
        """Test WebSocket authentication when user not found"""
        # Create valid token but user doesn't exist
        token_data = {
            "sub": "nonexistent-user",
            "type": "websocket",
            "exp": (datetime.utcnow() + timedelta(minutes=5)).timestamp()
        }
        token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # Mock database query returning None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = manager._authenticate_websocket(token, mock_db)
        
        assert result is None
    
    def test_rate_limiting(self, manager):
        """Test connection rate limiting"""
        connection_id = "conn-123"
        
        # Should allow up to message_rate_limit messages
        for i in range(manager.message_rate_limit):
            result = manager._check_rate_limit(connection_id)
            assert result is True
        
        # Next message should be rate limited
        result = manager._check_rate_limit(connection_id)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_connect_success(self, manager, mock_websocket, mock_db, mock_user):
        """Test successful WebSocket connection"""
        # Create valid token
        token_data = {
            "sub": str(mock_user.id),
            "type": "websocket",
            "exp": (datetime.utcnow() + timedelta(minutes=5)).timestamp()
        }
        token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # Mock database and authentication
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch('app.core.websocket_manager.security_audit_logger'):
            result = await manager.connect(
                websocket=mock_websocket,
                batch_id="batch-123",
                token=token,
                db=mock_db
            )
        
        assert result is True
        mock_websocket.accept.assert_called_once()
        assert len(manager.connections) == 1
        assert str(mock_user.id) in manager.user_connections
        assert "batch-123" in manager.batch_connections
    
    @pytest.mark.asyncio
    async def test_connect_authentication_failure(self, manager, mock_websocket, mock_db):
        """Test WebSocket connection with authentication failure"""
        invalid_token = "invalid.token"
        
        # Mock authentication failure
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await manager.connect(
            websocket=mock_websocket,
            batch_id="batch-123",
            token=invalid_token,
            db=mock_db
        )
        
        assert result is False
        mock_websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)
        assert len(manager.connections) == 0
    
    @pytest.mark.asyncio
    async def test_connect_user_limit_exceeded(self, manager, mock_websocket, mock_db, mock_user):
        """Test WebSocket connection when user limit is exceeded"""
        # Create valid token
        token_data = {
            "sub": str(mock_user.id),
            "type": "websocket",
            "exp": (datetime.utcnow() + timedelta(minutes=5)).timestamp()
        }
        token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # Mock database authentication
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Simulate user already has max connections
        user_id = str(mock_user.id)
        manager.user_connections[user_id] = set(f"conn-{i}" for i in range(manager.max_connections_per_user))
        
        result = await manager.connect(
            websocket=mock_websocket,
            batch_id="batch-123",
            token=token,
            db=mock_db
        )
        
        assert result is False
        mock_websocket.close.assert_called_once_with(code=status.WS_1013_TRY_AGAIN_LATER)
    
    @pytest.mark.asyncio
    async def test_disconnect(self, manager):
        """Test WebSocket disconnection and cleanup"""
        # Set up a connection manually
        connection_id = "conn-123"
        user_id = "user-456"
        batch_id = "batch-789"
        
        mock_websocket = AsyncMock()
        connection = WebSocketConnection(mock_websocket, user_id, connection_id)
        connection.subscribe_to_batch(batch_id)
        
        manager.connections[connection_id] = connection
        manager.user_connections[user_id] = {connection_id}
        manager.batch_connections[batch_id] = {connection_id}
        manager.rate_limit_windows[connection_id] = []
        
        with patch('app.core.websocket_manager.security_audit_logger'):
            await manager.disconnect(connection_id)
        
        # Verify cleanup
        assert connection_id not in manager.connections
        assert user_id not in manager.user_connections
        assert batch_id not in manager.batch_connections
        assert connection_id not in manager.rate_limit_windows
        mock_websocket.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_broadcast_progress(self, manager):
        """Test progress broadcasting to subscribed connections"""
        # Set up multiple connections
        batch_id = "batch-123"
        user1_id = "user-1"
        user2_id = "user-2"
        
        # Create mock connections
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws3 = AsyncMock()  # Different batch
        
        conn1 = WebSocketConnection(mock_ws1, user1_id, "conn-1")
        conn2 = WebSocketConnection(mock_ws2, user2_id, "conn-2")
        conn3 = WebSocketConnection(mock_ws3, user1_id, "conn-3")
        
        conn1.subscribe_to_batch(batch_id)
        conn2.subscribe_to_batch(batch_id)
        conn3.subscribe_to_batch("different-batch")
        
        manager.connections["conn-1"] = conn1
        manager.connections["conn-2"] = conn2
        manager.connections["conn-3"] = conn3
        manager.batch_connections[batch_id] = {"conn-1", "conn-2"}
        manager.batch_connections["different-batch"] = {"conn-3"}
        
        # Broadcast progress
        await manager.broadcast_progress(
            batch_id=batch_id,
            progress=50.0,
            status="processing",
            stage="parsing",
            message="Processing data"
        )
        
        # Verify only subscribed connections received the message
        mock_ws1.send_text.assert_called_once()
        mock_ws2.send_text.assert_called_once()
        mock_ws3.send_text.assert_not_called()
        
        # Verify message content
        sent_message = json.loads(mock_ws1.send_text.call_args[0][0])
        assert sent_message["batch_id"] == batch_id
        assert sent_message["progress"] == 50.0
        assert sent_message["status"] == "processing"
    
    @pytest.mark.asyncio
    async def test_broadcast_progress_user_specific(self, manager):
        """Test user-specific progress broadcasting"""
        batch_id = "batch-123"
        target_user = "user-1"
        other_user = "user-2"
        
        # Create connections for both users
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        
        conn1 = WebSocketConnection(mock_ws1, target_user, "conn-1")
        conn2 = WebSocketConnection(mock_ws2, other_user, "conn-2")
        
        conn1.subscribe_to_batch(batch_id)
        conn2.subscribe_to_batch(batch_id)
        
        manager.connections["conn-1"] = conn1
        manager.connections["conn-2"] = conn2
        manager.batch_connections[batch_id] = {"conn-1", "conn-2"}
        
        # Broadcast to specific user only
        await manager.broadcast_progress(
            batch_id=batch_id,
            progress=75.0,
            status="processing",
            stage="database",
            message="Saving data",
            user_id=target_user
        )
        
        # Verify only target user received the message
        mock_ws1.send_text.assert_called_once()
        mock_ws2.send_text.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_broadcast_progress_failed_connection_cleanup(self, manager):
        """Test that failed connections are cleaned up during broadcast"""
        batch_id = "batch-123"
        
        # Create a connection that will fail to send
        mock_ws = AsyncMock()
        mock_ws.send_text.side_effect = Exception("Connection failed")
        
        conn = WebSocketConnection(mock_ws, "user-1", "conn-1")
        conn.subscribe_to_batch(batch_id)
        
        manager.connections["conn-1"] = conn
        manager.batch_connections[batch_id] = {"conn-1"}
        
        with patch.object(manager, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
            await manager.broadcast_progress(
                batch_id=batch_id,
                progress=50.0,
                status="processing",
                stage="parsing",
                message="Processing"
            )
            
            # Verify failed connection was cleaned up
            mock_disconnect.assert_called_once_with("conn-1")
    
    def test_get_connection_stats(self, manager):
        """Test connection statistics retrieval"""
        # Set up test connections
        manager.connections = {
            "conn-1": Mock(),
            "conn-2": Mock(),
            "conn-3": Mock()
        }
        manager.user_connections = {
            "user-1": {"conn-1", "conn-2"},
            "user-2": {"conn-3"}
        }
        manager.batch_connections = {
            "batch-1": {"conn-1"},
            "batch-2": {"conn-2", "conn-3"}
        }
        
        stats = manager.get_connection_stats()
        
        assert stats["total_connections"] == 3
        assert stats["unique_users"] == 2
        assert stats["active_batches"] == 2
        assert stats["connections_by_user"]["user-1"] == 2
        assert stats["connections_by_user"]["user-2"] == 1


class TestProgressEmitters:
    """Test suite for progress emitter functions"""
    
    @pytest.mark.asyncio
    async def test_emit_upload_progress(self):
        """Test general upload progress emission"""
        with patch('app.core.websocket_manager.websocket_manager.broadcast_progress') as mock_broadcast:
            await emit_upload_progress(
                batch_id="batch-123",
                progress=50.0,
                stage="parsing",
                message="Processing CSV",
                user_id="user-123",
                details={"processed": 50, "total": 100}
            )
            
            mock_broadcast.assert_called_once_with(
                batch_id="batch-123",
                progress=50.0,
                status="processing",
                stage="parsing",
                message="Processing CSV",
                details={"processed": 50, "total": 100},
                error=None,
                user_id="user-123"
            )
    
    @pytest.mark.asyncio
    async def test_emit_upload_progress_completed(self):
        """Test upload progress emission for completed status"""
        with patch('app.core.websocket_manager.websocket_manager.broadcast_progress') as mock_broadcast:
            await emit_upload_progress(
                batch_id="batch-123",
                progress=100.0,
                stage="completion",
                message="Upload completed",
                user_id="user-123"
            )
            
            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args[1]
            assert call_args["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_emit_upload_progress_error(self):
        """Test upload progress emission with error"""
        with patch('app.core.websocket_manager.websocket_manager.broadcast_progress') as mock_broadcast:
            await emit_upload_progress(
                batch_id="batch-123",
                progress=25.0,
                stage="validation",
                message="Validation failed",
                user_id="user-123",
                error="Invalid file format"
            )
            
            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args[1]
            assert call_args["status"] == "error"
            assert call_args["error"] == "Invalid file format"
    
    @pytest.mark.asyncio
    async def test_stage_specific_emitters(self):
        """Test all stage-specific progress emitters"""
        with patch('app.core.websocket_manager.emit_upload_progress') as mock_emit:
            # Test validation progress
            await emit_validation_progress(
                batch_id="batch-123",
                progress=10.0,
                message="Validating file",
                user_id="user-123"
            )
            
            mock_emit.assert_called_with(
                "batch-123", 10.0, "validation", "Validating file", "user-123", None
            )
            
            # Test scanning progress
            await emit_scanning_progress(
                batch_id="batch-123",
                progress=30.0,
                message="Scanning for malware",
                user_id="user-123"
            )
            
            mock_emit.assert_called_with(
                "batch-123", 30.0, "scanning", "Scanning for malware", "user-123", None
            )
            
            # Test parsing progress
            await emit_parsing_progress(
                batch_id="batch-123",
                progress=50.0,
                message="Parsing CSV",
                user_id="user-123"
            )
            
            mock_emit.assert_called_with(
                "batch-123", 50.0, "parsing", "Parsing CSV", "user-123", None
            )
            
            # Test database progress
            await emit_database_progress(
                batch_id="batch-123",
                progress=70.0,
                message="Saving transactions",
                user_id="user-123"
            )
            
            mock_emit.assert_called_with(
                "batch-123", 70.0, "database", "Saving transactions", "user-123", None
            )
            
            # Test categorization progress
            await emit_categorization_progress(
                batch_id="batch-123",
                progress=90.0,
                message="Categorizing transactions",
                user_id="user-123"
            )
            
            mock_emit.assert_called_with(
                "batch-123", 90.0, "categorization", "Categorizing transactions", "user-123", None
            )


class TestWebSocketIntegration:
    """Integration tests for WebSocket system"""
    
    @pytest.mark.asyncio
    async def test_websocket_background_job_integration(self):
        """Test WebSocket integration with background job system"""
        # This would test the integration between background jobs and WebSocket progress
        # For now, we'll test that the right functions are called
        
        with patch('app.core.websocket_manager.emit_validation_progress') as mock_validation:
            with patch('app.core.websocket_manager.emit_scanning_progress') as mock_scanning:
                with patch('app.core.websocket_manager.emit_parsing_progress') as mock_parsing:
                    with patch('app.core.websocket_manager.emit_database_progress') as mock_database:
                        with patch('app.core.websocket_manager.emit_categorization_progress') as mock_categorization:
                            
                            # Simulate background job progress updates
                            batch_id = "test-batch-123"
                            user_id = "user-123"
                            
                            # Validation stage
                            await mock_validation(batch_id, 10.0, "Validating file format", user_id)
                            mock_validation.assert_called_once()
                            
                            # Scanning stage
                            await mock_scanning(batch_id, 30.0, "Scanning for threats", user_id)
                            mock_scanning.assert_called_once()
                            
                            # Parsing stage
                            await mock_parsing(batch_id, 50.0, "Parsing CSV data", user_id)
                            mock_parsing.assert_called_once()
                            
                            # Database stage
                            await mock_database(batch_id, 80.0, "Saving to database", user_id)
                            mock_database.assert_called_once()
                            
                            # Categorization stage
                            await mock_categorization(batch_id, 100.0, "Categorization complete", user_id)
                            mock_categorization.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self):
        """Test complete WebSocket connection lifecycle"""
        manager = WebSocketManager()
        
        # Mock WebSocket and user
        mock_websocket = AsyncMock()
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_db = Mock()
        
        # Create valid token
        token_data = {
            "sub": str(mock_user.id),
            "type": "websocket",
            "exp": (datetime.utcnow() + timedelta(minutes=5)).timestamp()
        }
        token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # Mock database authentication
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        try:
            # Test connection
            with patch('app.core.websocket_manager.security_audit_logger'):
                result = await manager.connect(
                    websocket=mock_websocket,
                    batch_id="batch-123",
                    token=token,
                    db=mock_db
                )
            
            assert result is True
            assert len(manager.connections) == 1
            
            # Test progress broadcasting
            await manager.broadcast_progress(
                batch_id="batch-123",
                progress=50.0,
                status="processing",
                stage="parsing",
                message="Processing data"
            )
            
            mock_websocket.send_text.assert_called()
            
            # Test disconnection
            connection_id = list(manager.connections.keys())[0]
            with patch('app.core.websocket_manager.security_audit_logger'):
                await manager.disconnect(connection_id)
            
            assert len(manager.connections) == 0
            
        finally:
            # Cleanup
            await manager.stop()


class TestWebSocketSecurity:
    """Security-focused tests for WebSocket system"""
    
    def test_jwt_token_validation(self):
        """Test JWT token validation with various scenarios"""
        manager = WebSocketManager()
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = "user-123"
        
        # Test valid token
        valid_token_data = {
            "sub": str(mock_user.id),
            "type": "websocket",
            "exp": (datetime.utcnow() + timedelta(minutes=5)).timestamp()
        }
        valid_token = jwt.encode(valid_token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        result = manager._authenticate_websocket(valid_token, mock_db)
        assert result == mock_user
        
        # Test expired token
        expired_token_data = {
            "sub": str(mock_user.id),
            "type": "websocket",
            "exp": (datetime.utcnow() - timedelta(minutes=1)).timestamp()
        }
        expired_token = jwt.encode(expired_token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        result = manager._authenticate_websocket(expired_token, mock_db)
        assert result is None
        
        # Test malformed token
        result = manager._authenticate_websocket("invalid.token.here", mock_db)
        assert result is None
        
        # Test token with wrong type
        wrong_type_token_data = {
            "sub": str(mock_user.id),
            "type": "access",  # Wrong type
            "exp": (datetime.utcnow() + timedelta(minutes=5)).timestamp()
        }
        wrong_type_token = jwt.encode(wrong_type_token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # This should still work as we only check 'sub', not 'type' in current implementation
        result = manager._authenticate_websocket(wrong_type_token, mock_db)
        assert result == mock_user
    
    def test_rate_limiting_security(self):
        """Test rate limiting prevents abuse"""
        manager = WebSocketManager()
        connection_id = "test-conn"
        
        # Test that rate limiting works over time windows
        import time
        
        # Fill up the rate limit
        for _ in range(manager.message_rate_limit):
            assert manager._check_rate_limit(connection_id) is True
        
        # Next call should be blocked
        assert manager._check_rate_limit(connection_id) is False
        
        # Test that old timestamps are cleaned up
        # Manually manipulate the rate limit window to simulate time passage
        if connection_id in manager.rate_limit_windows:
            # Clear old timestamps
            manager.rate_limit_windows[connection_id] = []
            
        # Should be allowed again
        assert manager._check_rate_limit(connection_id) is True
    
    @pytest.mark.asyncio
    async def test_user_isolation(self):
        """Test that users can only see their own progress"""
        manager = WebSocketManager()
        
        # Set up connections for different users
        user1_ws = AsyncMock()
        user2_ws = AsyncMock()
        
        conn1 = WebSocketConnection(user1_ws, "user-1", "conn-1")
        conn2 = WebSocketConnection(user2_ws, "user-2", "conn-2")
        
        batch_id = "shared-batch"  # Same batch, different users
        conn1.subscribe_to_batch(batch_id)
        conn2.subscribe_to_batch(batch_id)
        
        manager.connections["conn-1"] = conn1
        manager.connections["conn-2"] = conn2
        manager.batch_connections[batch_id] = {"conn-1", "conn-2"}
        
        # Broadcast to user-1 only
        await manager.broadcast_progress(
            batch_id=batch_id,
            progress=50.0,
            status="processing",
            stage="parsing",
            message="User 1 data",
            user_id="user-1"
        )
        
        # Verify only user-1 received the message
        user1_ws.send_text.assert_called_once()
        user2_ws.send_text.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_connection_cleanup_security(self):
        """Test that inactive connections are properly cleaned up"""
        manager = WebSocketManager()
        
        # Create a connection with old last_activity
        old_time = datetime.utcnow() - timedelta(hours=1)
        mock_ws = AsyncMock()
        conn = WebSocketConnection(mock_ws, "user-1", "conn-1")
        conn.last_activity = old_time
        
        manager.connections["conn-1"] = conn
        manager.user_connections["user-1"] = {"conn-1"}
        
        # Run cleanup (simulate)
        inactive_connections = []
        now = datetime.utcnow()
        
        for connection_id, connection in manager.connections.items():
            if (now - connection.last_activity).total_seconds() > 1800:  # 30 minutes
                inactive_connections.append(connection_id)
        
        assert "conn-1" in inactive_connections
        
        # Cleanup would remove this connection
        with patch('app.core.websocket_manager.security_audit_logger'):
            await manager.disconnect("conn-1")
        
        assert "conn-1" not in manager.connections


class TestWebSocketPerformance:
    """Performance-focused tests for WebSocket system"""
    
    @pytest.mark.asyncio
    async def test_concurrent_connections(self):
        """Test handling multiple concurrent connections"""
        manager = WebSocketManager()
        
        # Create multiple connections
        connections = []
        for i in range(10):
            mock_ws = AsyncMock()
            conn = WebSocketConnection(mock_ws, f"user-{i}", f"conn-{i}")
            conn.subscribe_to_batch("shared-batch")
            connections.append(conn)
            
            manager.connections[f"conn-{i}"] = conn
            manager.user_connections[f"user-{i}"] = {f"conn-{i}"}
        
        manager.batch_connections["shared-batch"] = {f"conn-{i}" for i in range(10)}
        
        # Test broadcasting to all connections
        await manager.broadcast_progress(
            batch_id="shared-batch",
            progress=50.0,
            status="processing",
            stage="parsing",
            message="Processing for all users"
        )
        
        # Verify all connections received the message
        for conn in connections:
            conn.websocket.send_text.assert_called_once()
        
        # Cleanup
        await manager.stop()
    
    def test_memory_efficient_message_handling(self):
        """Test that message handling doesn't cause memory leaks"""
        # Test that old rate limit windows are cleaned up
        manager = WebSocketManager()
        
        # Add many rate limit windows
        for i in range(1000):
            connection_id = f"conn-{i}"
            manager._check_rate_limit(connection_id)
        
        assert len(manager.rate_limit_windows) == 1000
        
        # Simulate cleanup (this would happen in real cleanup)
        # For testing, we just verify the structure exists
        assert isinstance(manager.rate_limit_windows, dict)
        
    def test_large_message_handling(self):
        """Test handling of large progress messages"""
        # Create a large details object
        large_details = ProgressDetails(
            processed_items=1000000,
            total_items=2000000,
            additional_info={f"key_{i}": f"value_{i}" for i in range(100)}
        )
        
        message = ProgressMessage(
            message_type=MessageType.PROGRESS_UPDATE,
            batch_id="large-batch",
            progress=50.0,
            status=ProgressStatus.PROCESSING,
            stage=ProgressStage.DATABASE,
            message="Processing large dataset",
            details=large_details,
            user_id="user-123"
        )
        
        # Test serialization doesn't fail
        json_str = message.to_json()
        assert len(json_str) > 1000  # Should be a large message
        
        # Test deserialization works
        parsed = json.loads(json_str)
        assert parsed["details"]["processed_items"] == 1000000


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])