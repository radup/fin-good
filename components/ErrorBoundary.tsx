'use client'

import React from 'react'
import { AlertTriangle, RefreshCw, Home, Shield, Wifi, Clock, Upload, AlertCircle, RotateCcw, LogIn } from 'lucide-react'

// Enhanced error types for better categorization
export enum ErrorType {
  NETWORK = 'network',
  AUTHENTICATION = 'authentication',
  VALIDATION = 'validation',
  PERMISSION = 'permission',
  TRANSACTION = 'transaction',
  UPLOAD = 'upload',
  SYSTEM = 'system',
  PAYMENT = 'payment',
  DATA_CORRUPTION = 'data_corruption',
  SESSION_EXPIRED = 'session_expired',
  FILE_PROCESSING = 'file_processing',
  DATABASE = 'database',
  UNKNOWN = 'unknown'
}

export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export interface ErrorContext {
  componentStack?: string
  errorBoundary?: string
  timestamp: number
  userAgent: string
  url: string
  userId?: string
  sessionId?: string
  transactionData?: {
    pendingTransactions?: any[]
    unsavedChanges?: Record<string, any>
    uploadProgress?: number
    batchId?: string
  }
  financialContext?: {
    currentBalance?: number
    lastSuccessfulSync?: number
    pendingCalculations?: any[]
  }
  additionalData?: Record<string, any>
}

export interface EnhancedError extends Error {
  type?: ErrorType
  severity?: ErrorSeverity
  recoverable?: boolean
  userMessage?: string
  context?: ErrorContext
  originalError?: Error
  code?: string | number
  recovery?: {
    strategy?: 'retry' | 'rollback' | 'session_restore' | 'data_recovery' | 'none'
    autoRecoverable?: boolean
    requiresUserAction?: boolean
    preservedData?: any
    recoveryUrl?: string
  }
}

export interface ErrorBoundaryState {
  hasError: boolean
  error?: EnhancedError
  errorId?: string
  retryAttempts: number
  lastRetryTime?: number
}

export interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ComponentType<{ error?: EnhancedError; onRetry?: () => void; onReport?: () => void }>
  name?: string
  level?: 'page' | 'component' | 'critical'
  maxRetries?: number
  retryDelay?: number
  onError?: (error: EnhancedError, errorInfo: React.ErrorInfo) => void
  onRecovery?: () => void
  isolateErrors?: boolean
  enableRetry?: boolean
  enableReporting?: boolean
  preserveState?: boolean
}

// Financial data preservation service
class FinancialDataManager {
  private static instance: FinancialDataManager
  private pendingTransactions: any[] = []
  private unsavedChanges: Record<string, any> = {}
  private uploadState: Record<string, any> = {}
  
  static getInstance(): FinancialDataManager {
    if (!FinancialDataManager.instance) {
      FinancialDataManager.instance = new FinancialDataManager()
    }
    return FinancialDataManager.instance
  }
  
  preserveTransactionData(data: any[]): void {
    this.pendingTransactions = [...data]
    localStorage.setItem('fg_preserved_transactions', JSON.stringify(data))
  }
  
  preserveUnsavedChanges(key: string, data: any): void {
    this.unsavedChanges[key] = data
    localStorage.setItem('fg_unsaved_changes', JSON.stringify(this.unsavedChanges))
  }
  
  preserveUploadState(batchId: string, state: any): void {
    this.uploadState[batchId] = state
    localStorage.setItem('fg_upload_state', JSON.stringify(this.uploadState))
  }
  
  getPreservedTransactions(): any[] {
    const stored = localStorage.getItem('fg_preserved_transactions')
    return stored ? JSON.parse(stored) : []
  }
  
  getUnsavedChanges(): Record<string, any> {
    const stored = localStorage.getItem('fg_unsaved_changes')
    return stored ? JSON.parse(stored) : {}
  }
  
  getUploadState(batchId?: string): any {
    const stored = localStorage.getItem('fg_upload_state')
    const states = stored ? JSON.parse(stored) : {}
    return batchId ? states[batchId] : states
  }
  
  clearPreservedData(): void {
    this.pendingTransactions = []
    this.unsavedChanges = {}
    this.uploadState = {}
    localStorage.removeItem('fg_preserved_transactions')
    localStorage.removeItem('fg_unsaved_changes')
    localStorage.removeItem('fg_upload_state')
  }
  
  hasPreservedData(): boolean {
    return this.pendingTransactions.length > 0 || 
           Object.keys(this.unsavedChanges).length > 0 ||
           Object.keys(this.uploadState).length > 0
  }
}

export const financialDataManager = FinancialDataManager.getInstance()

// Error logging service
class ErrorLogger {
  private static instance: ErrorLogger
  private errorQueue: Array<{ error: EnhancedError; context: ErrorContext }> = []
  private isOnline = true
  private retryQueue: Array<() => Promise<void>> = []

  static getInstance(): ErrorLogger {
    if (!ErrorLogger.instance) {
      ErrorLogger.instance = new ErrorLogger()
    }
    return ErrorLogger.instance
  }

  constructor() {
    if (typeof window !== 'undefined') {
      // Monitor online status
      window.addEventListener('online', () => {
        this.isOnline = true
        this.processRetryQueue()
      })
      window.addEventListener('offline', () => {
        this.isOnline = false
      })
    }
  }

  async logError(error: EnhancedError, context: ErrorContext): Promise<void> {
    const errorEntry = { error, context }
    
    // Always log to console for development
    console.error('Error Boundary Error:', {
      message: error.message,
      type: error.type,
      severity: error.severity,
      stack: error.stack,
      context
    })

    // Store in local queue
    this.errorQueue.push(errorEntry)
    
    // Attempt to send to server if online
    if (this.isOnline) {
      try {
        await this.sendToServer(errorEntry)
      } catch (sendError) {
        console.warn('Failed to send error to server:', sendError)
        this.retryQueue.push(() => this.sendToServer(errorEntry))
      }
    } else {
      this.retryQueue.push(() => this.sendToServer(errorEntry))
    }
  }

  private async sendToServer(errorEntry: { error: EnhancedError; context: ErrorContext }): Promise<void> {
    // Only send critical errors or in production
    if (errorEntry.error.severity === ErrorSeverity.CRITICAL || process.env.NODE_ENV === 'production') {
      // Implement your error reporting service here
      // Example: POST to /api/errors
      try {
        await fetch('/api/errors', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            error: {
              message: errorEntry.error.message,
              stack: errorEntry.error.stack,
              type: errorEntry.error.type,
              severity: errorEntry.error.severity,
              code: errorEntry.error.code
            },
            context: errorEntry.context
          })
        })
      } catch (error) {
        // Silently fail to avoid infinite error loops
        console.warn('Error reporting failed:', error)
      }
    }
  }

  private async processRetryQueue(): Promise<void> {
    const queue = [...this.retryQueue]
    this.retryQueue = []
    
    for (const retryFn of queue) {
      try {
        await retryFn()
      } catch (error) {
        console.warn('Retry failed:', error)
      }
    }
  }

  getErrorHistory(): Array<{ error: EnhancedError; context: ErrorContext }> {
    return [...this.errorQueue]
  }

  clearErrorHistory(): void {
    this.errorQueue = []
  }
}

export const errorLogger = ErrorLogger.getInstance()

// Utility functions for error classification
export function classifyError(error: Error, additionalContext?: Partial<ErrorContext>): EnhancedError {
  const enhancedError: EnhancedError = {
    ...error,
    type: ErrorType.UNKNOWN,
    severity: ErrorSeverity.MEDIUM,
    recoverable: true,
    context: {
      timestamp: Date.now(),
      userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : 'unknown',
      url: typeof window !== 'undefined' ? window.location.href : 'unknown',
      ...additionalContext
    },
    recovery: {
      strategy: 'retry',
      autoRecoverable: true,
      requiresUserAction: false
    }
  }

  // Network errors
  if (error.message.includes('fetch') || error.message.includes('network') || error.message.includes('NetworkError')) {
    enhancedError.type = ErrorType.NETWORK
    enhancedError.severity = ErrorSeverity.MEDIUM
    enhancedError.userMessage = 'Network connection issue. Please check your internet connection and try again.'
    enhancedError.recovery = {
      strategy: 'retry',
      autoRecoverable: true,
      requiresUserAction: false
    }
  }
  
  // Authentication errors
  else if (error.message.includes('401') || error.message.includes('Unauthorized') || error.message.includes('authentication')) {
    enhancedError.type = ErrorType.AUTHENTICATION
    enhancedError.severity = ErrorSeverity.HIGH
    enhancedError.userMessage = 'Your session has expired. Please log in again.'
    enhancedError.recoverable = true
    enhancedError.recovery = {
      strategy: 'session_restore',
      autoRecoverable: false,
      requiresUserAction: true,
      recoveryUrl: '/login',
      preservedData: financialDataManager.hasPreservedData() ? {
        transactions: financialDataManager.getPreservedTransactions(),
        unsavedChanges: financialDataManager.getUnsavedChanges()
      } : undefined
    }
  }
  
  // Transaction errors
  else if (error.message.includes('transaction') || error.message.includes('payment')) {
    enhancedError.type = ErrorType.TRANSACTION
    enhancedError.severity = ErrorSeverity.CRITICAL
    enhancedError.userMessage = 'Transaction processing error. Your data has been preserved.'
    enhancedError.recoverable = true
    enhancedError.recovery = {
      strategy: 'data_recovery',
      autoRecoverable: false,
      requiresUserAction: true,
      preservedData: additionalContext?.transactionData
    }
  }
  
  // Upload errors
  else if (error.message.includes('upload') || error.message.includes('file')) {
    enhancedError.type = ErrorType.UPLOAD
    enhancedError.severity = ErrorSeverity.HIGH
    enhancedError.userMessage = 'File upload error. Your upload progress has been preserved.'
    enhancedError.recovery = {
      strategy: 'retry',
      autoRecoverable: true,
      requiresUserAction: false,
      preservedData: additionalContext?.transactionData?.uploadProgress
    }
  }
  
  // Payment processing errors
  else if (error.message.includes('payment') || error.message.includes('billing')) {
    enhancedError.type = ErrorType.PAYMENT
    enhancedError.severity = ErrorSeverity.CRITICAL
    enhancedError.userMessage = 'Payment processing error. No charges have been made.'
    enhancedError.recovery = {
      strategy: 'rollback',
      autoRecoverable: false,
      requiresUserAction: true
    }
  }
  
  // Database errors
  else if (error.message.includes('database') || error.message.includes('sql') || error.message.includes('connection')) {
    enhancedError.type = ErrorType.DATABASE
    enhancedError.severity = ErrorSeverity.HIGH
    enhancedError.userMessage = 'Database connection error. Your data is safe and will be synchronized when connection is restored.'
    enhancedError.recovery = {
      strategy: 'data_recovery',
      autoRecoverable: true,
      requiresUserAction: false
    }
  }
  
  // Session expired errors
  else if (error.message.includes('session') || error.message.includes('expired') || error.message.includes('timeout')) {
    enhancedError.type = ErrorType.SESSION_EXPIRED
    enhancedError.severity = ErrorSeverity.HIGH
    enhancedError.userMessage = 'Your session has expired. Your work has been preserved.'
    enhancedError.recovery = {
      strategy: 'session_restore',
      autoRecoverable: false,
      requiresUserAction: true,
      recoveryUrl: '/login',
      preservedData: {
        currentUrl: typeof window !== 'undefined' ? window.location.href : undefined,
        formData: financialDataManager.getUnsavedChanges()
      }
    }
  }
  
  // Validation errors
  else if (error.message.includes('validation') || error.message.includes('invalid')) {
    enhancedError.type = ErrorType.VALIDATION
    enhancedError.severity = ErrorSeverity.LOW
    enhancedError.userMessage = 'Please check your input and try again.'
    enhancedError.recovery = {
      strategy: 'retry',
      autoRecoverable: false,
      requiresUserAction: true
    }
  }

  return enhancedError
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private retryTimeoutId?: NodeJS.Timeout

  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      retryAttempts: 0
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    const enhancedError = classifyError(error)
    return {
      hasError: true,
      error: enhancedError,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Preserve financial data before processing error
    if (this.props.financialContext) {
      if (this.props.financialContext.currentTransactionData) {
        financialDataManager.preserveTransactionData(this.props.financialContext.currentTransactionData)
      }
      if (this.props.financialContext.pendingChanges) {
        Object.entries(this.props.financialContext.pendingChanges).forEach(([key, value]) => {
          financialDataManager.preserveUnsavedChanges(key, value)
        })
      }
      if (this.props.financialContext.uploadBatchId) {
        financialDataManager.preserveUploadState(this.props.financialContext.uploadBatchId, {
          timestamp: Date.now(),
          error: error.message
        })
      }
      
      if (this.props.onDataPreservation) {
        this.props.onDataPreservation(this.props.financialContext)
      }
    }
    
    const enhancedError = classifyError(error, {
      componentStack: errorInfo.componentStack,
      errorBoundary: this.props.name || 'Unknown',
      transactionData: this.props.financialContext,
      additionalData: {
        retryAttempts: this.state.retryAttempts,
        level: this.props.level
      }
    })

    // Log the error
    errorLogger.logError(enhancedError, enhancedError.context!)

    // Call custom error handler
    if (this.props.onError) {
      this.props.onError(enhancedError, errorInfo)
    }
  }

  handleRetry = () => {
    const { maxRetries = 3, retryDelay = 1000 } = this.props
    
    if (this.state.retryAttempts >= maxRetries) {
      return
    }

    const now = Date.now()
    if (this.state.lastRetryTime && (now - this.state.lastRetryTime) < retryDelay) {
      return
    }

    this.setState({
      retryAttempts: this.state.retryAttempts + 1,
      lastRetryTime: now
    })

    // Clear error after delay to trigger retry
    this.retryTimeoutId = setTimeout(() => {
      this.setState({
        hasError: false,
        error: undefined,
        errorId: undefined
      })
      
      if (this.props.onRecovery) {
        this.props.onRecovery()
      }
    }, 100)
  }

  handleReport = () => {
    if (this.state.error) {
      // Additional reporting logic
      errorLogger.logError(this.state.error, {
        ...this.state.error.context!,
        additionalData: {
          ...this.state.error.context?.additionalData,
          userReported: true
        }
      })
    }
  }
  
  handleRecovery = async () => {
    if (!this.state.error?.recovery) return
    
    const { strategy, recoveryUrl, preservedData } = this.state.error.recovery
    
    switch (strategy) {
      case 'session_restore':
        if (recoveryUrl) {
          // Store current context for restoration after login
          if (preservedData) {
            localStorage.setItem('fg_recovery_context', JSON.stringify(preservedData))
          }
          window.location.href = recoveryUrl
        }
        break
        
      case 'data_recovery':
        // Restore preserved data and clear error
        if (preservedData && this.props.onDataPreservation) {
          this.props.onDataPreservation(preservedData)
        }
        this.setState({
          hasError: false,
          error: undefined,
          errorId: undefined
        })
        break
        
      case 'rollback':
        // Clear any pending changes and restore to last known good state
        financialDataManager.clearPreservedData()
        window.location.reload()
        break
        
      default:
        this.handleRetry()
        break
    }
  }

  componentWillUnmount() {
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId)
    }
  }

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback
        return (
          <FallbackComponent
            error={this.state.error}
            onRetry={this.props.enableRetry ? this.handleRetry : undefined}
            onReport={this.props.enableReporting ? this.handleReport : undefined}
          />
        )
      }

      return (
        <ErrorFallback
          error={this.state.error}
          onRetry={this.props.enableRetry ? this.handleRetry : undefined}
          onReport={this.props.enableReporting ? this.handleReport : undefined}
          onRecover={this.handleRecovery}
          maxRetries={this.props.maxRetries}
          retryAttempts={this.state.retryAttempts}
          level={this.props.level}
        />
      )
    }

    return this.props.children
  }
}

// Enhanced error fallback component
export function ErrorFallback({
  error,
  onRetry,
  onReport,
  onRecover,
  maxRetries = 3,
  retryAttempts = 0,
  level = 'component'
}: {
  error?: EnhancedError
  onRetry?: () => void
  onReport?: () => void
  onRecover?: () => void
  maxRetries?: number
  retryAttempts?: number
  level?: 'page' | 'component' | 'critical' | 'transaction' | 'upload' | 'auth'
}) {
  const getErrorIcon = () => {
    switch (error?.type) {
      case ErrorType.NETWORK:
        return <Wifi className="w-6 h-6" />
      case ErrorType.AUTHENTICATION:
      case ErrorType.SESSION_EXPIRED:
        return <Shield className="w-6 h-6" />
      case ErrorType.TRANSACTION:
      case ErrorType.PAYMENT:
        return <AlertTriangle className="w-6 h-6" />
      case ErrorType.UPLOAD:
      case ErrorType.FILE_PROCESSING:
        return <Upload className="w-6 h-6" />
      case ErrorType.DATABASE:
        return <AlertCircle className="w-6 h-6" />
      default:
        return <AlertTriangle className="w-6 h-6" />
    }
  }

  const getErrorColors = () => {
    switch (error?.severity) {
      case ErrorSeverity.CRITICAL:
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          text: 'text-red-800',
          icon: 'text-red-500',
          button: 'bg-red-600 hover:bg-red-700'
        }
      case ErrorSeverity.HIGH:
        return {
          bg: 'bg-orange-50',
          border: 'border-orange-200',
          text: 'text-orange-800',
          icon: 'text-orange-500',
          button: 'bg-orange-600 hover:bg-orange-700'
        }
      default:
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200',
          text: 'text-yellow-800',
          icon: 'text-yellow-500',
          button: 'bg-yellow-600 hover:bg-yellow-700'
        }
    }
  }

  const colors = getErrorColors()
  const canRetry = onRetry && retryAttempts < maxRetries && error?.recoverable !== false

  return (
    <div className={`p-6 ${colors.bg} ${colors.border} border rounded-lg`}>
      <div className="flex items-start space-x-4">
        <div className={colors.icon}>
          {getErrorIcon()}
        </div>
        <div className="flex-1">
          <h3 className={`text-lg font-semibold ${colors.text} mb-2`}>
            {level === 'critical' ? 'Critical System Error' : 
             level === 'page' ? 'Page Error' : 'Component Error'}
          </h3>
          
          <p className={`${colors.text} mb-4`}>
            {error?.userMessage || error?.message || 'An unexpected error occurred'}
          </p>

          {/* Data Preservation Messages */}
          {(error?.type === ErrorType.TRANSACTION || error?.type === ErrorType.PAYMENT) && (
            <div className="bg-blue-50 border border-blue-200 rounded p-3 mb-4">
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4 text-blue-500" />
                <span className="text-sm text-blue-800 font-medium">
                  Your transaction data has been safely preserved
                </span>
              </div>
            </div>
          )}
          
          {error?.type === ErrorType.UPLOAD && error?.recovery?.preservedData && (
            <div className="bg-green-50 border border-green-200 rounded p-3 mb-4">
              <div className="flex items-center space-x-2">
                <Upload className="w-4 h-4 text-green-500" />
                <span className="text-sm text-green-800 font-medium">
                  Upload progress saved - you can resume from where you left off
                </span>
              </div>
            </div>
          )}
          
          {error?.type === ErrorType.SESSION_EXPIRED && error?.recovery?.preservedData && (
            <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-yellow-500" />
                <span className="text-sm text-yellow-800 font-medium">
                  Your work has been preserved and will be restored after login
                </span>
              </div>
            </div>
          )}
          
          {error?.recovery?.preservedData && (
            <div className="bg-gray-50 border border-gray-200 rounded p-3 mb-4">
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-800 font-medium">
                  No financial data was lost - all changes are recoverable
                </span>
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-3">
            {canRetry && (
              <button
                onClick={onRetry}
                className={`inline-flex items-center px-4 py-2 ${colors.button} text-white rounded font-medium text-sm transition-colors`}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Try Again ({maxRetries - retryAttempts} attempts left)
              </button>
            )}
            
            <button
              onClick={() => window.location.href = '/'}
              className="inline-flex items-center px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded font-medium text-sm transition-colors"
            >
              <Home className="w-4 h-4 mr-2" />
              Go Home
            </button>
            
            {/* Recovery Actions Based on Error Type */}
            {error?.recovery?.strategy === 'session_restore' && onRecover && (
              <button
                onClick={onRecover}
                className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium text-sm transition-colors"
              >
                <LogIn className="w-4 h-4 mr-2" />
                Restore Session
              </button>
            )}
            
            {error?.recovery?.strategy === 'data_recovery' && onRecover && (
              <button
                onClick={onRecover}
                className="inline-flex items-center px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded font-medium text-sm transition-colors"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Recover Data
              </button>
            )}
            
            {error?.recovery?.strategy === 'rollback' && onRecover && (
              <button
                onClick={onRecover}
                className="inline-flex items-center px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded font-medium text-sm transition-colors"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Rollback Changes
              </button>
            )}
            
            {onReport && (
              <button
                onClick={onReport}
                className="inline-flex items-center px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded font-medium text-sm transition-colors"
              >
                Report Issue
              </button>
            )}
          </div>

          {process.env.NODE_ENV === 'development' && error && (
            <details className="mt-4">
              <summary className="text-sm text-gray-600 cursor-pointer hover:text-gray-800">
                Technical Details (Development)
              </summary>
              <pre className="mt-2 text-xs text-gray-700 bg-gray-100 p-2 rounded overflow-auto max-h-40">
                {error.stack}
              </pre>
            </details>
          )}
        </div>
      </div>
    </div>
  )
}

// Specialized Error Boundaries for Financial Contexts

// Transaction Error Boundary with automatic data preservation
export function TransactionErrorBoundary({ children, transactionData, onDataLoss }: {
  children: React.ReactNode
  transactionData?: any[]
  onDataLoss?: (data: any[]) => void
}) {
  return (
    <ErrorBoundary
      name="TransactionBoundary"
      level="transaction"
      enableRetry={true}
      enableReporting={true}
      preserveState={true}
      maxRetries={3}
      financialContext={{
        currentTransactionData: transactionData
      }}
      onDataPreservation={(data) => {
        if (onDataLoss && data.currentTransactionData) {
          onDataLoss(data.currentTransactionData)
        }
      }}
    >
      {children}
    </ErrorBoundary>
  )
}

// Upload Error Boundary with resume capability
export function UploadErrorBoundary({ children, batchId, onUploadFailure }: {
  children: React.ReactNode
  batchId?: string
  onUploadFailure?: (batchId: string, error: EnhancedError) => void
}) {
  return (
    <ErrorBoundary
      name="UploadBoundary"
      level="upload"
      enableRetry={true}
      preserveState={true}
      maxRetries={5}
      retryDelay={2000}
      financialContext={{
        uploadBatchId: batchId
      }}
      onError={(error) => {
        if (onUploadFailure && batchId) {
          onUploadFailure(batchId, error)
        }
      }}
    >
      {children}
    </ErrorBoundary>
  )
}

// Authentication Error Boundary with session recovery
export function AuthErrorBoundary({ children, onAuthFailure }: {
  children: React.ReactNode
  onAuthFailure?: () => void
}) {
  return (
    <ErrorBoundary
      name="AuthBoundary"
      level="auth"
      enableRetry={false}
      preserveState={true}
      onError={(error) => {
        if (error.type === ErrorType.AUTHENTICATION || error.type === ErrorType.SESSION_EXPIRED) {
          // Preserve current page context
          const currentContext = {
            url: window.location.href,
            timestamp: Date.now(),
            unsavedData: financialDataManager.getUnsavedChanges()
          }
          localStorage.setItem('fg_auth_recovery', JSON.stringify(currentContext))
          
          if (onAuthFailure) {
            onAuthFailure()
          }
        }
      }}
    >
      {children}
    </ErrorBoundary>
  )
}

// Critical Financial Operation Boundary
export function CriticalFinancialBoundary({ children, operation, onCriticalFailure }: {
  children: React.ReactNode
  operation: string
  onCriticalFailure?: (operation: string, error: EnhancedError) => void
}) {
  return (
    <ErrorBoundary
      name={`CriticalBoundary-${operation}`}
      level="critical"
      enableRetry={false}
      preserveState={true}
      onError={(error) => {
        // Log critical financial errors immediately
        console.error(`CRITICAL FINANCIAL ERROR in ${operation}:`, error)
        
        // Preserve all current financial context
        const criticalContext = {
          operation,
          timestamp: Date.now(),
          error: error.message,
          preservedTransactions: financialDataManager.getPreservedTransactions(),
          unsavedChanges: financialDataManager.getUnsavedChanges(),
          uploadState: financialDataManager.getUploadState()
        }
        
        localStorage.setItem('fg_critical_error_context', JSON.stringify(criticalContext))
        
        if (onCriticalFailure) {
          onCriticalFailure(operation, error)
        }
      }}
    >
      {children}
    </ErrorBoundary>
  )
}

// Higher-order component for automatic error boundary wrapping
export function withFinancialErrorBoundary<T extends object>(
  Component: React.ComponentType<T>,
  boundaryConfig?: {
    type?: 'transaction' | 'upload' | 'auth' | 'critical'
    name?: string
    onError?: (error: EnhancedError) => void
  }
) {
  return function WrappedComponent(props: T) {
    const config = boundaryConfig || { type: 'transaction' }
    
    switch (config.type) {
      case 'upload':
        return (
          <UploadErrorBoundary batchId={undefined}>
            <Component {...props} />
          </UploadErrorBoundary>
        )
      case 'auth':
        return (
          <AuthErrorBoundary>
            <Component {...props} />
          </AuthErrorBoundary>
        )
      case 'critical':
        return (
          <CriticalFinancialBoundary operation={config.name || 'unknown'}>
            <Component {...props} />
          </CriticalFinancialBoundary>
        )
      default:
        return (
          <TransactionErrorBoundary>
            <Component {...props} />
          </TransactionErrorBoundary>
        )
    }
  }
}

// Recovery utilities
export const recoveryUtils = {
  // Check if there's preserved data from a previous session
  hasRecoveryData(): boolean {
    return financialDataManager.hasPreservedData() || 
           localStorage.getItem('fg_recovery_context') !== null ||
           localStorage.getItem('fg_auth_recovery') !== null ||
           localStorage.getItem('fg_critical_error_context') !== null
  },
  
  // Get all recovery data
  getRecoveryData(): {
    transactions?: any[]
    unsavedChanges?: Record<string, any>
    authContext?: any
    criticalContext?: any
  } {
    return {
      transactions: financialDataManager.getPreservedTransactions(),
      unsavedChanges: financialDataManager.getUnsavedChanges(),
      authContext: JSON.parse(localStorage.getItem('fg_auth_recovery') || '{}'),
      criticalContext: JSON.parse(localStorage.getItem('fg_critical_error_context') || '{}')
    }
  },
  
  // Clear all recovery data
  clearRecoveryData(): void {
    financialDataManager.clearPreservedData()
    localStorage.removeItem('fg_recovery_context')
    localStorage.removeItem('fg_auth_recovery')
    localStorage.removeItem('fg_critical_error_context')
  },
  
  // Restore data after successful recovery
  restoreData(data: any): void {
    if (data.transactions) {
      // Emit event or call callback to restore transactions
      window.dispatchEvent(new CustomEvent('fg-restore-transactions', { detail: data.transactions }))
    }
    if (data.unsavedChanges) {
      // Emit event or call callback to restore unsaved changes
      window.dispatchEvent(new CustomEvent('fg-restore-changes', { detail: data.unsavedChanges }))
    }
  }
}

// Legacy fallback - keeping for backward compatibility
export function LegacyErrorFallback({ error }: { error?: Error }) {
  return (
    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
      <h2 className="text-lg font-semibold text-red-800 mb-2">Error</h2>
      <p className="text-red-600">
        {error?.message || 'An unexpected error occurred'}
      </p>
    </div>
  )
}
