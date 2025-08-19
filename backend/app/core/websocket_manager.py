"""
WebSocket Manager for Real-time Upload Progress Tracking

This module provides comprehensive WebSocket connection management and progress
tracking for file uploads in the FinGood application.

Features:
- Connection pooling and management
- User authentication and authorization
- Progress message broadcasting
- Connection cleanup and error handling
- Rate limiting and security measures
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Union, Any, Callable
import uuid
import weakref
from contextlib import asynccontextmanager
from enum import Enum
from dataclasses import dataclass, asdict
import threading
import time

from fastapi import WebSocket, WebSocketDisconnect, HTTPException, status
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import InvalidTokenError
import redis

from app.core.config import settings
from app.models.user import User
from app.core.audit_logger import security_audit_logger


logger = logging.getLogger(__name__)


# Enhanced message types and status enums
class MessageType(str, Enum):
    """Types of WebSocket messages"""
    PROGRESS_UPDATE = "progress_update"
    JOB_STATUS = "job_status"
    BATCH_UPDATE = "batch_update"
    SYSTEM_STATUS = "system_status"
    CONNECTION_STATUS = "connection_status"
    ERROR_NOTIFICATION = "error_notification"
    HEARTBEAT = "heartbeat"
    QUEUE_STATS = "queue_stats"

class ProgressStatus(str, Enum):
    """Progress status values"""
    QUEUED = "queued"
    STARTING = "starting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class ProgressStage(str, Enum):
    """Upload processing stages"""
    INITIALIZATION = "initialization"
    VALIDATION = "validation"
    SCANNING = "scanning"
    PARSING = "parsing"
    DATABASE = "database"
    CATEGORIZATION = "categorization"
    COMPLETION = "completion"
    CLEANUP = "cleanup"

@dataclass
class ProgressDetails:
    """Structured progress details"""
    processed_items: Optional[int] = None
    total_items: Optional[int] = None
    errors_count: Optional[int] = None
    warnings_count: Optional[int] = None
    current_file: Optional[str] = None
    processing_rate: Optional[float] = None  # items per second
    estimated_remaining: Optional[float] = None  # seconds
    retry_count: Optional[int] = None
    queue_position: Optional[int] = None
    additional_info: Optional[Dict[str, Any]] = None

class ProgressMessage:
    """Enhanced progress update message with comprehensive tracking."""
    
    def __init__(
        self,
        message_type: MessageType,
        batch_id: str,
        progress: float,
        status: ProgressStatus,
        stage: ProgressStage,
        message: str,
        details: Optional[ProgressDetails] = None,
        error: Optional[str] = None,
        job_id: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        self.message_type = message_type
        self.batch_id = batch_id
        self.job_id = job_id
        self.user_id = user_id
        self.progress = min(100.0, max(0.0, progress))  # Clamp between 0-100
        self.status = status
        self.stage = stage
        self.message = message
        self.details = details or ProgressDetails()
        self.error = error
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
        self.sequence_number = int(time.time() * 1000000)  # Microsecond precision for ordering
    
    def to_dict(self) -> Dict:
        """Convert message to dictionary for JSON serialization."""
        data = {
            "message_type": self.message_type.value,
            "batch_id": self.batch_id,
            "progress": self.progress,
            "status": self.status.value,
            "stage": self.stage.value,
            "message": self.message,
            "details": asdict(self.details) if self.details else {},
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "sequence_number": self.sequence_number
        }
        
        if self.job_id:
            data["job_id"] = self.job_id
        if self.user_id:
            data["user_id"] = self.user_id
        if self.error:
            data["error"] = self.error
            
        return data
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def create_progress_update(
        cls,
        batch_id: str,
        progress: float,
        stage: ProgressStage,
        message: str,
        user_id: str,
        details: Optional[ProgressDetails] = None,
        job_id: Optional[str] = None
    ) -> 'ProgressMessage':
        """Factory method for progress updates"""
        status = ProgressStatus.COMPLETED if progress >= 100.0 else ProgressStatus.PROCESSING
        return cls(
            message_type=MessageType.PROGRESS_UPDATE,
            batch_id=batch_id,
            progress=progress,
            status=status,
            stage=stage,
            message=message,
            details=details,
            job_id=job_id,
            user_id=user_id
        )
    
    @classmethod
    def create_error_notification(
        cls,
        batch_id: str,
        stage: ProgressStage,
        error_message: str,
        user_id: str,
        job_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> 'ProgressMessage':
        """Factory method for error notifications"""
        return cls(
            message_type=MessageType.ERROR_NOTIFICATION,
            batch_id=batch_id,
            progress=0.0,
            status=ProgressStatus.ERROR,
            stage=stage,
            message="An error occurred during processing",
            error=error_message,
            job_id=job_id,
            user_id=user_id,
            correlation_id=correlation_id
        )
    
    @classmethod
    def create_heartbeat(
        cls,
        connection_id: str,
        user_id: str,
        stats: Optional[Dict[str, Any]] = None
    ) -> 'ProgressMessage':
        """Factory method for heartbeat messages"""
        details = ProgressDetails(additional_info=stats or {})
        return cls(
            message_type=MessageType.HEARTBEAT,
            batch_id=connection_id,
            progress=0.0,
            status=ProgressStatus.PROCESSING,
            stage=ProgressStage.INITIALIZATION,
            message="Connection heartbeat",
            details=details,
            user_id=user_id
        )


class WebSocketConnection:
    """Represents a WebSocket connection with metadata."""
    
    def __init__(self, websocket: WebSocket, user_id: str, connection_id: str):
        self.websocket = websocket
        self.user_id = user_id
        self.connection_id = connection_id
        self.connected_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.subscribed_batches: Set[str] = set()
        self.is_active = True
    
    async def send_message(self, message: ProgressMessage) -> bool:
        """Send a message to the client. Returns True if successful."""
        if not self.is_active:
            return False
        
        try:
            await self.websocket.send_text(message.to_json())
            self.last_activity = datetime.utcnow()
            return True
        except Exception as e:
            logger.warning(f"Failed to send message to connection {self.connection_id}: {e}")
            self.is_active = False
            return False
    
    def subscribe_to_batch(self, batch_id: str):
        """Subscribe to progress updates for a specific batch."""
        self.subscribed_batches.add(batch_id)
    
    def unsubscribe_from_batch(self, batch_id: str):
        """Unsubscribe from progress updates for a batch."""
        self.subscribed_batches.discard(batch_id)
    
    async def close(self):
        """Close the WebSocket connection."""
        if self.is_active:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.warning(f"Error closing connection {self.connection_id}: {e}")
            finally:
                self.is_active = False


class WebSocketManager:
    """Manages WebSocket connections for real-time progress tracking."""
    
    def __init__(self):
        # Connection storage: connection_id -> WebSocketConnection
        self.connections: Dict[str, WebSocketConnection] = {}
        
        # User to connections mapping: user_id -> set of connection_ids
        self.user_connections: Dict[str, Set[str]] = {}
        
        # Batch to connections mapping: batch_id -> set of connection_ids
        self.batch_connections: Dict[str, Set[str]] = {}
        
        # Connection limits per user
        self.max_connections_per_user = settings.MAX_WEBSOCKET_CONNECTIONS_PER_USER
        
        # Cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        self.cleanup_interval = 300  # 5 minutes
        
        # Rate limiting
        self.message_rate_limit = 10  # messages per second per connection
        self.rate_limit_windows: Dict[str, List[float]] = {}
        
        logger.info("WebSocket manager initialized")
    
    async def start(self):
        """Start the WebSocket manager and background tasks."""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_inactive_connections())
        logger.info("WebSocket manager started")
    
    async def stop(self):
        """Stop the WebSocket manager and close all connections."""
        # Cancel cleanup task
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        for connection in list(self.connections.values()):
            await connection.close()
        
        self.connections.clear()
        self.user_connections.clear()
        self.batch_connections.clear()
        
        logger.info("WebSocket manager stopped")
    
    def _authenticate_websocket(self, token: str, db: Session) -> Optional[User]:
        """Authenticate WebSocket connection using JWT token."""
        try:
            # Decode JWT token
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            # Get user from database
            user = db.query(User).filter(User.id == user_id).first()
            return user
            
        except InvalidTokenError:
            return None
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            return None
    
    def _check_rate_limit(self, connection_id: str) -> bool:
        """Check if connection is within rate limits."""
        now = datetime.utcnow().timestamp()
        window_start = now - 1.0  # 1 second window
        
        # Get or create rate limit window for connection
        if connection_id not in self.rate_limit_windows:
            self.rate_limit_windows[connection_id] = []
        
        timestamps = self.rate_limit_windows[connection_id]
        
        # Remove old timestamps
        timestamps[:] = [ts for ts in timestamps if ts > window_start]
        
        # Check if under limit
        if len(timestamps) >= self.message_rate_limit:
            return False
        
        # Add current timestamp
        timestamps.append(now)
        return True
    
    async def connect(
        self,
        websocket: WebSocket,
        batch_id: str,
        token: str,
        db: Session
    ) -> bool:
        """
        Accept a new WebSocket connection with authentication and authorization.
        
        Returns True if connection was accepted, False otherwise.
        """
        try:
            # Authenticate user
            user = self._authenticate_websocket(token, db)
            if not user:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                logger.warning("WebSocket connection rejected: Authentication failed")
                return False
            
            # Check connection limits
            user_id = str(user.id)
            if user_id in self.user_connections:
                if len(self.user_connections[user_id]) >= self.max_connections_per_user:
                    await websocket.close(code=status.WS_1013_TRY_AGAIN_LATER)
                    logger.warning(f"WebSocket connection rejected: User {user_id} exceeded connection limit")
                    return False
            
            # Accept connection
            await websocket.accept()
            
            # Create connection
            connection_id = str(uuid.uuid4())
            connection = WebSocketConnection(websocket, user_id, connection_id)
            connection.subscribe_to_batch(batch_id)
            
            # Store connection
            self.connections[connection_id] = connection
            
            # Update user connections mapping
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            # Update batch connections mapping
            if batch_id not in self.batch_connections:
                self.batch_connections[batch_id] = set()
            self.batch_connections[batch_id].add(connection_id)
            
            # Log connection
            security_audit_logger.log_websocket_connection(
                user_id=user_id,
                connection_id=connection_id,
                batch_id=batch_id,
                action="connected"
            )
            
            logger.info(f"WebSocket connected: user={user_id}, batch={batch_id}, connection={connection_id}")
            
            # Send initial connection confirmation
            initial_message = ProgressMessage(
                batch_id=batch_id,
                progress=0.0,
                status="connected",
                stage="initialization",
                message="Connected to upload progress tracking"
            )
            await connection.send_message(initial_message)
            
            return True
            
        except Exception as e:
            logger.error(f"Error establishing WebSocket connection: {e}")
            try:
                await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            except:
                pass
            return False
    
    async def disconnect(self, connection_id: str):
        """Disconnect and cleanup a WebSocket connection."""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        user_id = connection.user_id
        
        # Close the connection
        await connection.close()
        
        # Remove from connections
        del self.connections[connection_id]
        
        # Clean up user connections mapping
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Clean up batch connections mapping
        for batch_id in connection.subscribed_batches:
            if batch_id in self.batch_connections:
                self.batch_connections[batch_id].discard(connection_id)
                if not self.batch_connections[batch_id]:
                    del self.batch_connections[batch_id]
        
        # Clean up rate limiting
        if connection_id in self.rate_limit_windows:
            del self.rate_limit_windows[connection_id]
        
        # Log disconnection
        security_audit_logger.log_websocket_connection(
            user_id=user_id,
            connection_id=connection_id,
            batch_id=",".join(connection.subscribed_batches),
            action="disconnected"
        )
        
        logger.info(f"WebSocket disconnected: user={user_id}, connection={connection_id}")
    
    async def broadcast_progress(
        self,
        batch_id: str,
        progress: float,
        status: str,
        stage: str,
        message: str,
        details: Optional[Dict] = None,
        error: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Broadcast progress update to all subscribed connections."""
        if batch_id not in self.batch_connections:
            return
        
        progress_message = ProgressMessage(
            batch_id=batch_id,
            progress=progress,
            status=status,
            stage=stage,
            message=message,
            details=details,
            error=error
        )
        
        # Get connections for this batch
        connection_ids = list(self.batch_connections[batch_id])
        
        # Send to each connection
        failed_connections = []
        for connection_id in connection_ids:
            if connection_id not in self.connections:
                continue
            
            connection = self.connections[connection_id]
            
            # If user_id is specified, only send to that user's connections
            if user_id and connection.user_id != user_id:
                continue
            
            # Check rate limiting
            if not self._check_rate_limit(connection_id):
                logger.warning(f"Rate limit exceeded for connection {connection_id}")
                continue
            
            # Send message
            success = await connection.send_message(progress_message)
            if not success:
                failed_connections.append(connection_id)
        
        # Clean up failed connections
        for connection_id in failed_connections:
            await self.disconnect(connection_id)
        
        logger.debug(f"Progress broadcast: batch={batch_id}, stage={stage}, progress={progress}%")
    
    async def _cleanup_inactive_connections(self):
        """Background task to clean up inactive connections."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                now = datetime.utcnow()
                inactive_connections = []
                
                for connection_id, connection in self.connections.items():
                    # Check if connection is inactive (no activity for 30 minutes)
                    if (now - connection.last_activity).total_seconds() > 1800:
                        inactive_connections.append(connection_id)
                    # Check if connection is closed
                    elif not connection.is_active:
                        inactive_connections.append(connection_id)
                
                # Clean up inactive connections
                for connection_id in inactive_connections:
                    await self.disconnect(connection_id)
                
                if inactive_connections:
                    logger.info(f"Cleaned up {len(inactive_connections)} inactive WebSocket connections")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket cleanup task: {e}")
    
    def get_connection_stats(self) -> Dict:
        """Get statistics about current connections."""
        return {
            "total_connections": len(self.connections),
            "unique_users": len(self.user_connections),
            "active_batches": len(self.batch_connections),
            "connections_by_user": {
                user_id: len(conn_ids) 
                for user_id, conn_ids in self.user_connections.items()
            }
        }
    
    async def handle_websocket_disconnect(self, websocket: WebSocket, connection_id: str):
        """Handle WebSocket disconnection event."""
        try:
            await websocket.close()
        except:
            pass
        await self.disconnect(connection_id)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


@asynccontextmanager
async def get_websocket_manager():
    """Get the global WebSocket manager instance."""
    await websocket_manager.start()
    try:
        yield websocket_manager
    finally:
        # Don't stop here as manager should persist across requests
        pass


# Convenience functions for progress tracking
async def emit_upload_progress(
    batch_id: str,
    progress: float,
    stage: str,
    message: str,
    user_id: str,
    details: Optional[Dict] = None,
    error: Optional[str] = None
):
    """Emit progress update for file upload."""
    status = "error" if error else ("completed" if progress >= 100 else "processing")
    
    await websocket_manager.broadcast_progress(
        batch_id=batch_id,
        progress=progress,
        status=status,
        stage=stage,
        message=message,
        details=details,
        error=error,
        user_id=user_id
    )


# Stage-specific progress emitters
async def emit_validation_progress(batch_id: str, progress: float, message: str, user_id: str, details: Optional[Dict] = None):
    """Emit validation stage progress."""
    await emit_upload_progress(batch_id, progress, "validation", message, user_id, details)


async def emit_scanning_progress(batch_id: str, progress: float, message: str, user_id: str, details: Optional[Dict] = None):
    """Emit malware scanning stage progress."""
    await emit_upload_progress(batch_id, progress, "scanning", message, user_id, details)


async def emit_parsing_progress(batch_id: str, progress: float, message: str, user_id: str, details: Optional[Dict] = None):
    """Emit CSV parsing stage progress."""
    await emit_upload_progress(batch_id, progress, "parsing", message, user_id, details)


async def emit_database_progress(batch_id: str, progress: float, message: str, user_id: str, details: Optional[Dict] = None):
    """Emit database insertion stage progress."""
    await emit_upload_progress(batch_id, progress, "database", message, user_id, details)


async def emit_categorization_progress(batch_id: str, progress: float, message: str, user_id: str, details: Optional[Dict] = None):
    """Emit categorization stage progress."""
    await emit_upload_progress(batch_id, progress, "categorization", message, user_id, details)