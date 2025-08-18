'use client'

import { useState } from 'react'
import { CpuChipIcon, CheckCircleIcon, ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline'
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar'

interface ProcessingNotificationProps {
  fileId: string
  filename: string
  status: 'processing' | 'categorizing' | 'complete' | 'error'
  progress: number
  processedTransactions: number
  totalTransactions: number
  error?: string
  onDismiss: (fileId: string) => void
}

export function ProcessingNotification({
  fileId,
  filename,
  status,
  progress,
  processedTransactions,
  totalTransactions,
  error,
  onDismiss
}: ProcessingNotificationProps) {
  const [isHovered, setIsHovered] = useState(false)

  const getStatusIcon = () => {
    switch (status) {
      case 'processing':
        return <CpuChipIcon className="w-4 h-4 text-blue-600 animate-pulse" />
      case 'categorizing':
        return <CpuChipIcon className="w-4 h-4 text-purple-600 animate-pulse" />
      case 'complete':
        return <CheckCircleIcon className="w-4 h-4 text-green-600" />
      case 'error':
        return <ExclamationTriangleIcon className="w-4 h-4 text-red-600" />
      default:
        return <CpuChipIcon className="w-4 h-4 text-gray-600" />
    }
  }

  const getStatusColor = () => {
    switch (status) {
      case 'processing':
        return 'bg-blue-50 border-blue-200 text-blue-800'
      case 'categorizing':
        return 'bg-purple-50 border-purple-200 text-purple-800'
      case 'complete':
        return 'bg-green-50 border-green-200 text-green-800'
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800'
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800'
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'processing':
        return 'Processing file...'
      case 'categorizing':
        return 'AI categorizing...'
      case 'complete':
        return 'Processing complete!'
      case 'error':
        return 'Processing failed'
      default:
        return 'Processing...'
    }
  }

  const getProgressText = () => {
    if (status === 'complete') {
      return `${totalTransactions} transactions processed`
    }
    if (status === 'error') {
      return error || 'An error occurred'
    }
    if (totalTransactions > 0) {
      return `${processedTransactions} of ${totalTransactions} transactions processed`
    }
    return `${Math.round(progress)}% complete`
  }

  return (
    <div 
      className="relative"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Main Notification */}
      <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border therapeutic-transition ${getStatusColor()}`}>
        {getStatusIcon()}
        <span className="text-sm font-medium">{getStatusText()}</span>
        <button
          onClick={() => onDismiss(fileId)}
          className="ml-2 text-gray-400 hover:text-gray-600 therapeutic-transition"
        >
          <XMarkIcon className="w-4 h-4" />
        </button>
      </div>

      {/* Hover Details */}
      {isHovered && (
        <div className="absolute top-full right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 p-4 z-50">
          <div className="flex items-start gap-3">
            <DrSigmundSpendAvatar 
              size="sm" 
              mood={status === 'complete' ? 'celebrating' : status === 'error' ? 'protective' : 'analytical'}
              showMessage={false}
            />
            <div className="flex-1">
              <h4 className="font-medium text-gray-900 mb-1">{filename}</h4>
              <p className="text-sm text-gray-600 mb-3">{getProgressText()}</p>
              
              {/* Progress Bar */}
              {status !== 'complete' && status !== 'error' && (
                <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                  <div 
                    className="bg-blue-600 h-2 rounded-full therapeutic-transition"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
              )}

              {/* Status Details */}
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-500">Status:</span>
                  <span className="font-medium capitalize">{status}</span>
                </div>
                {totalTransactions > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Transactions:</span>
                    <span className="font-medium">{processedTransactions} / {totalTransactions}</span>
                  </div>
                )}
                {progress > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Progress:</span>
                    <span className="font-medium">{Math.round(progress)}%</span>
                  </div>
                )}
              </div>

              {/* Status-specific message */}
              {status === 'processing' && (
                <p className="text-xs text-blue-600 mt-2">
                  Parsing your financial data and preparing for AI analysis...
                </p>
              )}
              {status === 'categorizing' && (
                <p className="text-xs text-purple-600 mt-2">
                  AI is learning from your spending patterns and categorizing transactions...
                </p>
              )}
              {status === 'complete' && (
                <p className="text-xs text-green-600 mt-2">
                  All transactions have been processed and categorized successfully!
                </p>
              )}
              {status === 'error' && (
                <p className="text-xs text-red-600 mt-2">
                  {error || 'Something went wrong during processing. Please try again.'}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
