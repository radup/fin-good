'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * WebSocket Progress Message Interface
 */
export interface ProgressMessage {
  batch_id: string
  progress: number
  status: 'processing' | 'completed' | 'error' | 'connected'
  stage: 'initialization' | 'validation' | 'scanning' | 'parsing' | 'database' | 'categorization'
  message: string
  details?: {
    processed?: number
    total?: number
    errors?: number
    filename?: string
    size?: number
    threat_level?: string
    [key: string]: any
  }
  error?: string
  timestamp: string
}

/**
 * WebSocket Hook Configuration
 */
export interface UseWebSocketConfig {
  batchId: string
  token: string
  onProgress?: (message: ProgressMessage) => void
  onError?: (error: Error) => void
  onComplete?: (message: ProgressMessage) => void
  autoReconnect?: boolean
  maxReconnectAttempts?: number
  reconnectDelay?: number
}

/**
 * WebSocket Connection State
 */
export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error'

/**
 * WebSocket Hook Return Type
 */
export interface UseWebSocketReturn {
  isConnected: boolean
  connectionState: ConnectionState
  lastMessage: ProgressMessage | null
  error: string | null
  connect: () => void
  disconnect: () => void
  reconnect: () => void
}

/**
 * Custom hook for WebSocket connection to track upload progress
 */
export function useWebSocket(config: UseWebSocketConfig): UseWebSocketReturn {
  const {
    batchId,
    token,
    onProgress,
    onError,
    onComplete,
    autoReconnect = true,
    maxReconnectAttempts = 5,
    reconnectDelay = 2000
  } = config

  // State
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')
  const [lastMessage, setLastMessage] = useState<ProgressMessage | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Refs
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = process.env.NODE_ENV === 'development' 
      ? 'localhost:8000' 
      : window.location.host
    return `${protocol}//${host}/ws/upload-progress/${batchId}?token=${encodeURIComponent(token)}`
  }, [batchId, token])

  // Clear timeouts and intervals
  const clearTimeouts = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = null
    }
  }, [])

  // Start heartbeat
  const startHeartbeat = useCallback(() => {
    clearTimeouts()
    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping')
      }
    }, 30000) // Send ping every 30 seconds
  }, [clearTimeouts])

  // Handle WebSocket message
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      // Handle pong messages
      if (event.data === 'pong') {
        return
      }

      const message: ProgressMessage = JSON.parse(event.data)
      setLastMessage(message)
      setError(null)

      // Call progress callback
      if (onProgress) {
        onProgress(message)
      }

      // Call completion callback if upload is complete
      if (message.status === 'completed' && onComplete) {
        onComplete(message)
      }

      // Handle error messages
      if (message.status === 'error' && message.error) {
        const errorMessage = `Upload failed: ${message.error}`
        setError(errorMessage)
        if (onError) {
          onError(new Error(errorMessage))
        }
      }
    } catch (err) {
      const errorMessage = 'Failed to parse WebSocket message'
      console.error(errorMessage, err)
      setError(errorMessage)
      if (onError) {
        onError(new Error(errorMessage))
      }
    }
  }, [onProgress, onComplete, onError])

  // Handle WebSocket error
  const handleError = useCallback((event: Event) => {
    const errorMessage = 'WebSocket connection error occurred'
    console.error(errorMessage, event)
    setError(errorMessage)
    setConnectionState('error')
    
    if (onError) {
      onError(new Error(errorMessage))
    }
  }, [onError])

  // Handle WebSocket close
  const handleClose = useCallback((event: CloseEvent) => {
    console.log('WebSocket connection closed:', event.code, event.reason)
    setConnectionState('disconnected')
    clearTimeouts()

    // Attempt reconnection if enabled and not a policy violation
    if (autoReconnect && 
        reconnectAttemptsRef.current < maxReconnectAttempts &&
        event.code !== 1008) { // Not a policy violation (auth failure)
      
      reconnectAttemptsRef.current += 1
      const delay = reconnectDelay * Math.pow(1.5, reconnectAttemptsRef.current - 1) // Exponential backoff
      
      console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`)
      
      reconnectTimeoutRef.current = setTimeout(() => {
        connect()
      }, delay)
    } else if (event.code === 1008) {
      setError('Authentication failed - please refresh the page')
    }
  }, [autoReconnect, maxReconnectAttempts, reconnectDelay])

  // Connect to WebSocket
  const connect = useCallback(() => {
    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close()
    }

    setConnectionState('connecting')
    setError(null)

    try {
      const ws = new WebSocket(getWebSocketUrl())
      
      ws.onopen = () => {
        console.log('WebSocket connected')
        setConnectionState('connected')
        setError(null)
        reconnectAttemptsRef.current = 0 // Reset reconnect attempts on successful connection
        startHeartbeat()
      }

      ws.onmessage = handleMessage
      ws.onerror = handleError
      ws.onclose = handleClose

      wsRef.current = ws
    } catch (err) {
      const errorMessage = 'Failed to create WebSocket connection'
      console.error(errorMessage, err)
      setError(errorMessage)
      setConnectionState('error')
      
      if (onError) {
        onError(new Error(errorMessage))
      }
    }
  }, [getWebSocketUrl, handleMessage, handleError, handleClose, startHeartbeat, onError])

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    clearTimeouts()
    reconnectAttemptsRef.current = maxReconnectAttempts // Prevent reconnection
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected') // Normal closure
      wsRef.current = null
    }
    
    setConnectionState('disconnected')
  }, [clearTimeouts, maxReconnectAttempts])

  // Manually reconnect
  const reconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0 // Reset reconnect attempts
    clearTimeouts()
    connect()
  }, [connect, clearTimeouts])

  // Effect to handle cleanup on unmount and batch_id changes
  useEffect(() => {
    // Reconnect if batch_id changes
    if (batchId && token && wsRef.current?.readyState !== WebSocket.CONNECTING) {
      connect()
    }
    
    return () => {
      clearTimeouts()
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [batchId, token, connect, clearTimeouts])

  // Derived state
  const isConnected = connectionState === 'connected'

  return {
    isConnected,
    connectionState,
    lastMessage,
    error,
    connect,
    disconnect,
    reconnect
  }
}

/**
 * Hook specifically for upload progress tracking
 */
export function useUploadProgress(batchId: string, token: string) {
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState<string>('connecting')
  const [stage, setStage] = useState<string>('initialization')
  const [message, setMessage] = useState<string>('Connecting to progress tracking...')
  const [details, setDetails] = useState<any>(null)
  const [isComplete, setIsComplete] = useState(false)
  const [hasError, setHasError] = useState(false)

  const handleProgress = useCallback((progressMessage: ProgressMessage) => {
    setProgress(progressMessage.progress)
    setStatus(progressMessage.status)
    setStage(progressMessage.stage)
    setMessage(progressMessage.message)
    setDetails(progressMessage.details || null)
    
    if (progressMessage.status === 'completed') {
      setIsComplete(true)
    }
    
    if (progressMessage.status === 'error') {
      setHasError(true)
    }
  }, [])

  const handleError = useCallback((error: Error) => {
    setHasError(true)
    setStatus('error')
    setMessage(error.message)
  }, [])

  const handleComplete = useCallback((message: ProgressMessage) => {
    setIsComplete(true)
    setProgress(100)
    setStatus('completed')
  }, [])

  const webSocket = useWebSocket({
    batchId,
    token,
    onProgress: handleProgress,
    onError: handleError,
    onComplete: handleComplete
  })

  return {
    ...webSocket,
    progress,
    status,
    stage,
    message,
    details,
    isComplete,
    hasError
  }
}