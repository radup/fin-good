'use client'

import React, { useState, useEffect } from 'react'
import { 
  AlertTriangle, 
  Clock, 
  RefreshCw, 
  CheckCircle,
  XCircle,
  Info,
  Zap,
  TrendingUp
} from 'lucide-react'
import type { RateLimitInfo } from '@/lib/api'

interface RateLimitHandlerProps {
  error: any
  onRetry?: () => void
  onDismiss?: () => void
  className?: string
}

export default function RateLimitHandler({ 
  error, 
  onRetry, 
  onDismiss,
  className = '' 
}: RateLimitHandlerProps) {
  const [rateLimitInfo, setRateLimitInfo] = useState<RateLimitInfo | null>(null)
  const [timeRemaining, setTimeRemaining] = useState<number>(0)
  const [isRetrying, setIsRetrying] = useState(false)

  useEffect(() => {
    if (error?.response?.status === 429) {
      const data = error.response.data
      if (data) {
        setRateLimitInfo({
          retry_after: data.retry_after || 60,
          limit: data.limit || 100,
          reset_time: data.reset_time || new Date(Date.now() + 60000).toISOString(),
          message: data.message || 'Rate limit exceeded'
        })
        setTimeRemaining(data.retry_after || 60)
      }
    }
  }, [error])

  useEffect(() => {
    if (timeRemaining > 0) {
      const timer = setTimeout(() => {
        setTimeRemaining(prev => Math.max(0, prev - 1))
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [timeRemaining])

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  const getRateLimitType = () => {
    if (!rateLimitInfo) return 'unknown'
    
    // Determine rate limit type based on endpoint or message
    const message = rateLimitInfo.message.toLowerCase()
    if (message.includes('export')) return 'export'
    if (message.includes('auto-improvement') || message.includes('auto_improvement')) return 'auto-improvement'
    if (message.includes('feedback')) return 'feedback'
    if (message.includes('bulk')) return 'bulk'
    return 'general'
  }

  const getRateLimitIcon = (type: string) => {
    switch (type) {
      case 'export': return <TrendingUp className="w-5 h-5" />
      case 'auto-improvement': return <Zap className="w-5 h-5" />
      case 'feedback': return <CheckCircle className="w-5 h-5" />
      case 'bulk': return <RefreshCw className="w-5 h-5" />
      default: return <AlertTriangle className="w-5 h-5" />
    }
  }

  const getRateLimitTitle = (type: string) => {
    switch (type) {
      case 'export': return 'Export Rate Limit Exceeded'
      case 'auto-improvement': return 'Auto-Improvement Rate Limit Exceeded'
      case 'feedback': return 'Feedback Rate Limit Exceeded'
      case 'bulk': return 'Bulk Operation Rate Limit Exceeded'
      default: return 'Rate Limit Exceeded'
    }
  }

  const getRateLimitDescription = (type: string) => {
    switch (type) {
      case 'export':
        return 'You have exceeded the export limit. Please wait before trying again or consider upgrading your plan for higher limits.'
      case 'auto-improvement':
        return 'Auto-improvement operations are limited to prevent system overload. Please wait before running another improvement.'
      case 'feedback':
        return 'You have submitted too much feedback recently. Please wait before submitting more feedback.'
      case 'bulk':
        return 'Bulk operations are limited to prevent system overload. Please wait before performing another bulk operation.'
      default:
        return 'You have exceeded the rate limit for this operation. Please wait before trying again.'
    }
  }

  const handleRetry = async () => {
    if (timeRemaining > 0) return
    
    setIsRetrying(true)
    try {
      if (onRetry) {
        await onRetry()
      }
    } finally {
      setIsRetrying(false)
    }
  }

  if (error?.response?.status !== 429) {
    return null
  }

  const rateLimitType = getRateLimitType()

  return (
    <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-start">
        <div className="flex-shrink-0 text-red-500">
          {getRateLimitIcon(rateLimitType)}
        </div>
        
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-900">
            {getRateLimitTitle(rateLimitType)}
          </h3>
          
          <div className="mt-2 text-sm text-red-700">
            <p>{getRateLimitDescription(rateLimitType)}</p>
            
            {rateLimitInfo && (
              <div className="mt-3 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-medium">Time Remaining:</span>
                  <div className="flex items-center">
                    <Clock className="w-4 h-4 mr-1" />
                    <span className="font-mono">
                      {timeRemaining > 0 ? formatTime(timeRemaining) : 'Ready'}
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="font-medium">Limit:</span>
                  <span>{rateLimitInfo.limit} requests per hour</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="font-medium">Reset Time:</span>
                  <span className="text-xs">
                    {new Date(rateLimitInfo.reset_time).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            )}
          </div>
          
          <div className="mt-4 flex items-center space-x-3">
            <button
              onClick={handleRetry}
              disabled={timeRemaining > 0 || isRetrying}
              className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                timeRemaining > 0 || isRetrying
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-red-600 text-white hover:bg-red-700'
              }`}
            >
              {isRetrying ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-1 animate-spin inline" />
                  Retrying...
                </>
              ) : timeRemaining > 0 ? (
                <>
                  <Clock className="w-4 h-4 mr-1 inline" />
                  Wait {formatTime(timeRemaining)}
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4 mr-1 inline" />
                  Try Again
                </>
              )}
            </button>
            
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="px-3 py-2 text-sm font-medium text-red-700 hover:text-red-800 hover:bg-red-100 rounded-md transition-colors"
              >
                Dismiss
              </button>
            )}
          </div>
          
          {/* Helpful Tips */}
          <div className="mt-4 p-3 bg-red-100 rounded-md">
            <div className="flex items-start">
              <Info className="w-4 h-4 text-red-600 mt-0.5 mr-2 flex-shrink-0" />
              <div className="text-xs text-red-700">
                <p className="font-medium mb-1">Tips to avoid rate limits:</p>
                <ul className="space-y-1">
                  <li>• Space out your requests over time</li>
                  <li>• Use bulk operations instead of individual requests</li>
                  <li>• Consider upgrading your plan for higher limits</li>
                  <li>• Check the reset time to know when limits refresh</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
