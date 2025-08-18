'use client'

// Example file demonstrating enhanced ErrorBoundary usage in financial applications
// This file shows how to integrate the new error boundaries with existing components

import React, { useState } from 'react'
import { 
  TransactionErrorBoundary, 
  UploadErrorBoundary, 
  AuthErrorBoundary,
  CriticalFinancialBoundary,
  withFinancialErrorBoundary,
  recoveryUtils,
  EnhancedError
} from './ErrorBoundary'
import { TransactionTable } from './TransactionTable'
import { UploadModal } from './UploadModal'

// Example 1: Wrapping TransactionTable with transaction-specific error handling
export function EnhancedTransactionTable({ transactions }: { transactions: any[] }) {
  const [preservedTransactions, setPreservedTransactions] = useState<any[]>([])
  
  // Handle data loss by preserving transaction state
  const handleDataLoss = (lostData: any[]) => {
    setPreservedTransactions(lostData)
    console.log('Transaction data preserved:', lostData.length, 'transactions')
  }

  return (
    <TransactionErrorBoundary 
      transactionData={transactions}
      onDataLoss={handleDataLoss}
    >
      <TransactionTable 
        transactions={preservedTransactions.length > 0 ? preservedTransactions : transactions} 
        isLoading={false} 
      />
      
      {/* Show recovery notification if data was preserved */}
      {preservedTransactions.length > 0 && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
          <p className="text-sm text-blue-800">
            {preservedTransactions.length} transactions were recovered from a previous session.
          </p>
        </div>
      )}
    </TransactionErrorBoundary>
  )
}

// Example 2: Upload component with enhanced error handling and resume capability
export function EnhancedUploadModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [uploadBatchId, setUploadBatchId] = useState<string>()
  const [failedUploads, setFailedUploads] = useState<Record<string, EnhancedError>>({})

  const handleUploadFailure = (batchId: string, error: EnhancedError) => {
    setFailedUploads(prev => ({ ...prev, [batchId]: error }))
    console.log('Upload failed for batch:', batchId, 'Error:', error.message)
  }

  const handleUploadStart = (batchId: string) => {
    setUploadBatchId(batchId)
  }

  return (
    <UploadErrorBoundary 
      batchId={uploadBatchId}
      onUploadFailure={handleUploadFailure}
    >
      <UploadModal 
        isOpen={isOpen} 
        onClose={onClose}
        onUploadSuccess={() => {
          // Clear any previous failures on success
          setFailedUploads({})
          setUploadBatchId(undefined)
        }}
      />
      
      {/* Show upload failure recovery options */}
      {Object.keys(failedUploads).length > 0 && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
          <p className="text-sm text-yellow-800 mb-2">
            Some uploads failed but can be resumed:
          </p>
          {Object.entries(failedUploads).map(([batchId, error]) => (
            <div key={batchId} className="flex items-center justify-between text-xs">
              <span>Batch: {batchId.slice(-8)}</span>
              <button 
                className="text-blue-600 hover:text-blue-800"
                onClick={() => {
                  // Resume upload logic
                  console.log('Resuming upload for batch:', batchId)
                }}
              >
                Resume
              </button>
            </div>
          ))}
        </div>
      )}
    </UploadErrorBoundary>
  )
}

// Example 3: Authentication wrapper for entire app sections
export function AuthenticatedSection({ children }: { children: React.ReactNode }) {
  const handleAuthFailure = () => {
    console.log('Authentication failed - redirecting to login with recovery context')
    // The ErrorBoundary will automatically preserve the current context
    window.location.href = '/login?recovery=true'
  }

  return (
    <AuthErrorBoundary onAuthFailure={handleAuthFailure}>
      {children}
    </AuthErrorBoundary>
  )
}

// Example 4: Critical financial operations (payments, bulk updates, etc.)
export function PaymentProcessor({ amount, recipientId }: { amount: number; recipientId: string }) {
  const [isProcessing, setIsProcessing] = useState(false)

  const handleCriticalFailure = (operation: string, error: EnhancedError) => {
    console.error('CRITICAL PAYMENT FAILURE:', operation, error)
    // Immediately notify user and support team
    alert(`Payment processing failed: ${error.userMessage}. Support has been notified.`)
  }

  const processPayment = async () => {
    setIsProcessing(true)
    try {
      // Simulate payment processing that might fail
      await new Promise((resolve, reject) => {
        setTimeout(() => {
          if (Math.random() > 0.8) {
            reject(new Error('Payment gateway timeout'))
          } else {
            resolve(true)
          }
        }, 2000)
      })
    } catch (error) {
      throw error
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <CriticalFinancialBoundary 
      operation="payment-processing"
      onCriticalFailure={handleCriticalFailure}
    >
      <div className="p-4 border rounded">
        <h3>Process Payment</h3>
        <p>Amount: ${amount}</p>
        <p>Recipient: {recipientId}</p>
        <button 
          onClick={processPayment}
          disabled={isProcessing}
          className="mt-2 px-4 py-2 bg-green-600 text-white rounded disabled:opacity-50"
        >
          {isProcessing ? 'Processing...' : 'Process Payment'}
        </button>
      </div>
    </CriticalFinancialBoundary>
  )
}

// Example 5: Using the HOC wrapper for automatic error boundaries
const AutoProtectedTransactionTable = withFinancialErrorBoundary(TransactionTable, {
  type: 'transaction',
  name: 'TransactionTable',
  onError: (error) => console.log('Transaction table error:', error.message)
})

const AutoProtectedUploadModal = withFinancialErrorBoundary(UploadModal, {
  type: 'upload',
  name: 'UploadModal'
})

// Example 6: Recovery management component
export function RecoveryManager() {
  const [recoveryData, setRecoveryData] = useState<any>(null)
  const [showRecovery, setShowRecovery] = useState(false)

  React.useEffect(() => {
    // Check for recovery data on component mount
    if (recoveryUtils.hasRecoveryData()) {
      const data = recoveryUtils.getRecoveryData()
      setRecoveryData(data)
      setShowRecovery(true)
    }
  }, [])

  const handleRestore = () => {
    if (recoveryData) {
      recoveryUtils.restoreData(recoveryData)
      recoveryUtils.clearRecoveryData()
      setShowRecovery(false)
      setRecoveryData(null)
    }
  }

  const handleDismiss = () => {
    recoveryUtils.clearRecoveryData()
    setShowRecovery(false)
    setRecoveryData(null)
  }

  if (!showRecovery || !recoveryData) {
    return null
  }

  return (
    <div className="fixed top-4 right-4 max-w-md bg-blue-50 border border-blue-200 rounded-lg p-4 shadow-lg z-50">
      <h4 className="font-medium text-blue-900 mb-2">Data Recovery Available</h4>
      <p className="text-sm text-blue-800 mb-3">
        We found unsaved data from a previous session. Would you like to restore it?
      </p>
      
      {recoveryData.transactions?.length > 0 && (
        <p className="text-xs text-blue-700 mb-1">
          • {recoveryData.transactions.length} transactions
        </p>
      )}
      
      {Object.keys(recoveryData.unsavedChanges || {}).length > 0 && (
        <p className="text-xs text-blue-700 mb-1">
          • {Object.keys(recoveryData.unsavedChanges).length} unsaved changes
        </p>
      )}
      
      <div className="flex gap-2 mt-3">
        <button
          onClick={handleRestore}
          className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
        >
          Restore
        </button>
        <button
          onClick={handleDismiss}
          className="px-3 py-1 bg-gray-300 text-gray-700 text-sm rounded hover:bg-gray-400"
        >
          Dismiss
        </button>
      </div>
    </div>
  )
}

// Example 7: Integration with existing layout
export function FinancialAppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthenticatedSection>
      <div className="min-h-screen bg-gray-50">
        <RecoveryManager />
        
        <main className="container mx-auto py-6">
          <TransactionErrorBoundary transactionData={[]}>
            {children}
          </TransactionErrorBoundary>
        </main>
      </div>
    </AuthenticatedSection>
  )
}

// Example usage in a page component
export function ExampleFinancialDashboard() {
  const [transactions] = useState([
    { id: 1, date: '2024-01-15', description: 'Sample Transaction', amount: 100, is_income: false, is_categorized: true },
    { id: 2, date: '2024-01-16', description: 'Another Transaction', amount: 50, is_income: true, is_categorized: false }
  ])

  return (
    <FinancialAppLayout>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Financial Dashboard</h1>
        
        {/* Automatically protected transaction table */}
        <EnhancedTransactionTable transactions={transactions} />
        
        {/* Payment processing with critical error handling */}
        <PaymentProcessor amount={250.00} recipientId="vendor-123" />
        
        {/* Auto-protected components using HOC */}
        <AutoProtectedTransactionTable transactions={transactions} isLoading={false} />
      </div>
    </FinancialAppLayout>
  )
}