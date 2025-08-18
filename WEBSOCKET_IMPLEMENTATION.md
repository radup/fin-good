# WebSocket Real-time Upload Progress Implementation

This document outlines the complete WebSocket implementation for real-time upload progress tracking in the FinGood application.

## Architecture Overview

The implementation consists of several interconnected components that provide real-time progress updates during file uploads:

1. **Backend WebSocket Manager** - Handles connections and message broadcasting
2. **WebSocket Endpoint** - FastAPI WebSocket route for client connections
3. **Progress Tracking Integration** - Upload endpoint emits progress events
4. **Frontend WebSocket Hook** - React hook for WebSocket connectivity
5. **Progress UI Components** - Visual progress display components
6. **Authentication System** - Secure WebSocket token-based auth

## Backend Components

### 1. WebSocket Manager (`backend/app/core/websocket_manager.py`)

**Features:**
- Connection pooling and management
- User authentication via JWT tokens
- Rate limiting (10 messages/second per connection)
- Automatic cleanup of inactive connections
- Message broadcasting to specific users/batches
- Error handling and reconnection support

**Key Classes:**
- `ProgressMessage`: Structured progress message format
- `WebSocketConnection`: Individual connection wrapper
- `WebSocketManager`: Main manager for all connections

**Security Features:**
- JWT token validation for WebSocket connections
- Connection limits per user (5 max)
- Rate limiting to prevent spam
- Audit logging of connection events

### 2. WebSocket Endpoint (`backend/main.py`)

**Endpoint:** `/ws/upload-progress/{batch_id}?token={jwt_token}`

**Features:**
- Authentication required via JWT token
- Batch-specific progress tracking
- Ping/pong keepalive mechanism
- Automatic connection cleanup
- Error handling and graceful disconnection

### 3. Upload Progress Integration (`backend/app/api/v1/endpoints/upload.py`)

**Progress Stages:**
- **Validation (0-20%):** File format and security validation
- **Scanning (20-40%):** Malware and threat scanning
- **Parsing (40-60%):** CSV parsing and data validation
- **Database (60-80%):** Transaction insertion with progress
- **Categorization (80-100%):** ML-based transaction categorization

**Progress Events:**
```python
await emit_validation_progress(batch_id, progress, message, user_id, details)
await emit_scanning_progress(batch_id, progress, message, user_id, details)
await emit_parsing_progress(batch_id, progress, message, user_id, details)
await emit_database_progress(batch_id, progress, message, user_id, details)
await emit_categorization_progress(batch_id, progress, message, user_id, details)
```

### 4. Authentication Token Endpoint (`backend/app/api/v1/endpoints/auth.py`)

**Endpoint:** `POST /api/v1/auth/websocket-token`

**Features:**
- Generates temporary WebSocket tokens (5-minute expiry)
- Secure token validation
- Single-use tokens for security
- Required because WebSocket can't access HttpOnly cookies

## Frontend Components

### 1. WebSocket Hook (`hooks/useWebSocket.ts`)

**Features:**
- Automatic connection management
- Exponential backoff reconnection
- Message rate limiting
- Heartbeat/keepalive mechanism
- Error handling and recovery
- TypeScript type safety

**Hook Usage:**
```typescript
const uploadProgress = useUploadProgress(batchId, token)
// Returns: { isConnected, progress, status, stage, message, details, error }
```

### 2. Progress Component (`components/UploadProgress.tsx`)

**Features:**
- Real-time progress bar
- Stage-by-stage progress indicators
- Connection status display
- Error handling and retry buttons
- Detailed progress information
- Responsive design with Tailwind CSS

**Visual Elements:**
- Progress bar with stage-specific colors
- Stage icons with animations
- Connection status indicator
- Detailed metrics display
- Error messages and retry functionality

### 3. Upload Modal Integration (`components/UploadModal.tsx`)

**Features:**
- WebSocket token fetching
- Batch ID generation and management
- Progress display during upload
- Connection state management
- Cleanup on modal close
- Fallback to original upload status

## Message Format

WebSocket messages follow this JSON structure:

```json
{
  "batch_id": "uuid-string",
  "progress": 45.5,
  "status": "processing|completed|error|connected",
  "stage": "validation|scanning|parsing|database|categorization",
  "message": "Processing transactions...",
  "details": {
    "processed": 150,
    "total": 500,
    "errors": 2,
    "filename": "transactions.csv",
    "size": 1024000
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "error": "optional error message"
}
```

## Security Implementation

### 1. Authentication
- JWT tokens for WebSocket authentication
- Token validation on connection
- User-specific connection limits
- Audit logging of connections

### 2. Rate Limiting
- Message rate limiting per connection
- Connection limits per user
- Automatic cleanup of inactive connections
- Protection against WebSocket abuse

### 3. Authorization
- Users can only access their own upload progress
- Batch-specific access control
- Token-based authorization
- Secure error handling

## Configuration

### Backend Settings (`backend/app/core/config.py`)

```python
# WebSocket Configuration
ENABLE_WEBSOCKETS: bool = True
MAX_WEBSOCKET_CONNECTIONS_PER_USER: int = 5
WEBSOCKET_HEARTBEAT_INTERVAL: int = 30  # seconds
WEBSOCKET_CONNECTION_TIMEOUT: int = 300  # seconds (5 minutes)
WEBSOCKET_MESSAGE_RATE_LIMIT: int = 10  # messages per second
WEBSOCKET_MAX_MESSAGE_SIZE: int = 1024  # bytes
```

### Frontend Configuration

WebSocket URL is automatically determined based on environment:
- Development: `ws://localhost:8000`
- Production: `wss://your-domain.com`

## API Endpoints

### WebSocket
- `WS /ws/upload-progress/{batch_id}?token={jwt_token}` - Real-time progress updates

### HTTP
- `POST /api/v1/auth/websocket-token` - Get WebSocket authentication token
- `POST /api/v1/upload/csv` - Upload CSV with optional batch_id
- `GET /api/v1/websocket/status` - WebSocket manager status

## Testing

### Backend Testing
Run the WebSocket test script:
```bash
python test-websocket.py
```

### Frontend Testing
1. Start the backend server: `python backend/main.py`
2. Start the frontend: `npm run dev`
3. Open the upload modal and test file upload
4. Monitor WebSocket messages in browser dev tools

### Manual Testing Steps
1. **Authentication Test**: Verify WebSocket token generation
2. **Connection Test**: Establish WebSocket connection
3. **Progress Test**: Upload a CSV file and monitor progress
4. **Error Test**: Test error handling and reconnection
5. **Security Test**: Verify unauthorized access is blocked

## Performance Considerations

1. **Connection Management**: Automatic cleanup prevents memory leaks
2. **Rate Limiting**: Prevents WebSocket abuse
3. **Message Throttling**: Efficient progress updates
4. **Reconnection**: Exponential backoff prevents connection storms
5. **Memory Usage**: WeakRef patterns for garbage collection

## Error Handling

1. **Connection Errors**: Automatic reconnection with backoff
2. **Authentication Errors**: Token refresh and re-authentication
3. **Network Errors**: Graceful degradation to traditional upload
4. **Rate Limiting**: Client-side throttling and queuing
5. **Server Errors**: Error messages and recovery options

## Monitoring and Logging

1. **Connection Metrics**: Track active connections and usage
2. **Performance Metrics**: Message latency and throughput
3. **Error Tracking**: WebSocket errors and failures
4. **Security Audit**: Authentication attempts and violations
5. **Usage Analytics**: Upload progress completion rates

## Future Enhancements

1. **Multi-file Upload**: Progress tracking for multiple files
2. **Resume Capability**: Resume interrupted uploads
3. **Real-time Notifications**: Push notifications for completed uploads
4. **Progress History**: Store and replay progress information
5. **Advanced Analytics**: Progress patterns and optimization

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check WebSocket token validity
2. **No Progress Updates**: Verify batch_id matches between upload and WebSocket
3. **Connection Drops**: Check network stability and server load
4. **Authentication Errors**: Refresh WebSocket token
5. **Rate Limiting**: Reduce message frequency

### Debug Steps

1. Check WebSocket connection in browser dev tools
2. Verify WebSocket token in localStorage/session
3. Monitor backend logs for WebSocket events
4. Test with curl/postman for HTTP endpoints
5. Use WebSocket test script for backend verification