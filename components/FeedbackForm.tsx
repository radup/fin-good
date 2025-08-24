'use client'

import React, { useState } from 'react'
import { 
  MessageSquare, 
  CheckCircle, 
  XCircle, 
  Lightbulb,
  Send,
  Clock,
  AlertTriangle,
  Brain,
  Settings,
  Info
} from 'lucide-react'
import { transactionAPI } from '@/lib/api'
import type { FeedbackResult } from '@/lib/api'
import RateLimitHandler from './RateLimitHandler'

interface FeedbackFormProps {
  transactionId: number
  currentCategory: string
  currentSubcategory?: string
  onFeedbackSubmitted?: (result: FeedbackResult) => void
  onCancel?: () => void
  className?: string
}

export default function FeedbackForm({ 
  transactionId,
  currentCategory,
  currentSubcategory,
  onFeedbackSubmitted,
  onCancel,
  className = ''
}: FeedbackFormProps) {
  const [feedbackType, setFeedbackType] = useState<'correct' | 'incorrect' | 'suggest_alternative'>('correct')
  const [suggestedCategory, setSuggestedCategory] = useState('')
  const [suggestedSubcategory, setSuggestedSubcategory] = useState('')
  const [feedbackComment, setFeedbackComment] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<FeedbackResult | null>(null)

  const handleSubmit = async () => {
    if (feedbackType === 'suggest_alternative' && !suggestedCategory.trim()) {
      setError('Please provide a suggested category')
      return
    }

    try {
      setIsSubmitting(true)
      setError(null)

      const response = await transactionAPI.submitFeedback(transactionId, {
        feedback_type: feedbackType,
        suggested_category: feedbackType === 'suggest_alternative' ? suggestedCategory : undefined,
        suggested_subcategory: feedbackType === 'suggest_alternative' ? suggestedSubcategory : undefined,
        feedback_comment: feedbackComment.trim() || undefined
      })

      setSuccess(response.data)
      onFeedbackSubmitted?.(response.data)
    } catch (err: any) {
      console.error('Feedback submission failed:', err)
      setError(err.response?.data?.detail || 'Failed to submit feedback. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCancel = () => {
    setFeedbackType('correct')
    setSuggestedCategory('')
    setSuggestedSubcategory('')
    setFeedbackComment('')
    setError(null)
    setSuccess(null)
    onCancel?.()
  }

  const getFeedbackIcon = (type: string) => {
    switch (type) {
      case 'correct': return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'incorrect': return <XCircle className="w-5 h-5 text-red-600" />
      case 'suggest_alternative': return <Lightbulb className="w-5 h-5 text-yellow-600" />
      default: return <MessageSquare className="w-5 h-5 text-gray-600" />
    }
  }

  const getFeedbackTitle = (type: string) => {
    switch (type) {
      case 'correct': return 'Correct Categorization'
      case 'incorrect': return 'Incorrect Categorization'
      case 'suggest_alternative': return 'Suggest Alternative'
      default: return 'Provide Feedback'
    }
  }

  const getFeedbackDescription = (type: string) => {
    switch (type) {
      case 'correct':
        return 'This categorization is correct and helps improve our AI accuracy.'
      case 'incorrect':
        return 'This categorization is incorrect. Your feedback helps us learn and improve.'
      case 'suggest_alternative':
        return 'Suggest a better category for this transaction.'
      default:
        return 'Help us improve our categorization accuracy.'
    }
  }

  if (success) {
    return (
      <div className={`bg-green-50 border border-green-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-start">
          <CheckCircle className="w-6 h-6 text-green-600 mr-3 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-lg font-medium text-green-900">Feedback Submitted Successfully!</h3>
            <p className="text-sm text-green-700 mt-1">{success.message}</p>
            
            <div className="mt-3 space-y-2 text-sm text-green-700">
              <div className="flex items-center">
                <span className="font-medium mr-2">Impact:</span>
                <span className="capitalize">{success.impact.replace('_', ' ')}</span>
              </div>
              <div className="flex items-center">
                <span className="font-medium mr-2">ML Learning:</span>
                <span>{success.ml_learning ? 'Applied to ML model' : 'Recorded for analysis'}</span>
              </div>
            </div>

            <div className="mt-4 flex space-x-3">
              <button
                onClick={handleCancel}
                className="px-3 py-2 text-sm font-medium text-green-700 hover:text-green-800 hover:bg-green-100 rounded-md transition-colors"
              >
                Submit Another
              </button>
              {onCancel && (
                <button
                  onClick={onCancel}
                  className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
                >
                  Close
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center">
          {getFeedbackIcon(feedbackType)}
          <div className="ml-3">
            <h3 className="text-lg font-medium text-gray-900">
              {getFeedbackTitle(feedbackType)}
            </h3>
            <p className="text-sm text-gray-600">
              {getFeedbackDescription(feedbackType)}
            </p>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Current Category Display */}
        <div className="p-3 bg-gray-50 rounded-lg border">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Current Categorization</h4>
          <div className="text-sm">
            <span className="font-medium">{currentCategory}</span>
            {currentSubcategory && (
              <span className="text-gray-600 ml-1">
                → {currentSubcategory}
              </span>
            )}
          </div>
        </div>

        {/* Rate Limit Error */}
        {error && error.includes('429') && (
          <RateLimitHandler
            error={{ response: { status: 429, data: { message: error } } }}
            onRetry={handleSubmit}
            onDismiss={() => setError(null)}
          />
        )}

        {/* General Error */}
        {error && !error.includes('429') && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
              <span className="text-sm text-red-700">{error}</span>
            </div>
          </div>
        )}

        {/* Feedback Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Feedback Type
          </label>
          <div className="grid grid-cols-1 gap-3">
            <button
              onClick={() => setFeedbackType('correct')}
              className={`p-3 text-left rounded-lg border transition-colors ${
                feedbackType === 'correct'
                  ? 'border-green-300 bg-green-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center">
                <CheckCircle className="w-5 h-5 text-green-600 mr-3" />
                <div>
                  <div className="font-medium text-gray-900">Correct</div>
                  <div className="text-sm text-gray-600">This categorization is accurate</div>
                </div>
              </div>
            </button>

            <button
              onClick={() => setFeedbackType('incorrect')}
              className={`p-3 text-left rounded-lg border transition-colors ${
                feedbackType === 'incorrect'
                  ? 'border-red-300 bg-red-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center">
                <XCircle className="w-5 h-5 text-red-600 mr-3" />
                <div>
                  <div className="font-medium text-gray-900">Incorrect</div>
                  <div className="text-sm text-gray-600">This categorization is wrong</div>
                </div>
              </div>
            </button>

            <button
              onClick={() => setFeedbackType('suggest_alternative')}
              className={`p-3 text-left rounded-lg border transition-colors ${
                feedbackType === 'suggest_alternative'
                  ? 'border-yellow-300 bg-yellow-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center">
                <Lightbulb className="w-5 h-5 text-yellow-600 mr-3" />
                <div>
                  <div className="font-medium text-gray-900">Suggest Alternative</div>
                  <div className="text-sm text-gray-600">Propose a better category</div>
                </div>
              </div>
            </button>
          </div>
        </div>

        {/* Alternative Category Suggestion */}
        {feedbackType === 'suggest_alternative' && (
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Suggested Category *
              </label>
              <input
                type="text"
                value={suggestedCategory}
                onChange={(e) => setSuggestedCategory(e.target.value)}
                placeholder="e.g., Food & Dining"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Suggested Subcategory (Optional)
              </label>
              <input
                type="text"
                value={suggestedSubcategory}
                onChange={(e) => setSuggestedSubcategory(e.target.value)}
                placeholder="e.g., Restaurants"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        )}

        {/* Additional Comment */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Additional Comment (Optional)
          </label>
          <textarea
            value={feedbackComment}
            onChange={(e) => setFeedbackComment(e.target.value)}
            placeholder="Any additional context or explanation..."
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Info Box */}
        <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-start">
            <Info className="w-4 h-4 text-blue-500 mt-0.5 mr-2 flex-shrink-0" />
            <div className="text-xs text-blue-700">
              <p className="font-medium mb-1">How your feedback helps:</p>
              <ul className="space-y-1">
                <li>• Improves AI categorization accuracy</li>
                <li>• Updates rule-based categorization</li>
                <li>• Helps other users with similar transactions</li>
                <li>• Contributes to continuous system improvement</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <button
            onClick={handleCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
          >
            Cancel
          </button>

          <button
            onClick={handleSubmit}
            disabled={isSubmitting || (feedbackType === 'suggest_alternative' && !suggestedCategory.trim())}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center ${
              isSubmitting || (feedbackType === 'suggest_alternative' && !suggestedCategory.trim())
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-brand-gradient text-white transition-all duration-300 shadow-sm hover:shadow-lg transform hover:scale-105'
            }`}
          >
            {isSubmitting ? (
              <>
                <Clock className="w-4 h-4 mr-2 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Submit Feedback
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
