'use client'

import React, { useState } from 'react'
import RateLimitHandler from '@/components/RateLimitHandler'
import FeedbackForm from '@/components/FeedbackForm'

export default function RateLimitFeedbackDemo() {
  const [showRateLimitDemo, setShowRateLimitDemo] = useState(false)
  const [showFeedbackDemo, setShowFeedbackDemo] = useState(false)
  const [mockRateLimitError, setMockRateLimitError] = useState<any>(null)
  const [feedbackResults, setFeedbackResults] = useState<any[]>([])

  const simulateRateLimitError = (type: 'export' | 'auto-improvement' | 'feedback' | 'bulk') => {
    const errors = {
      export: {
        response: {
          status: 429,
          data: {
            message: 'Export rate limit exceeded',
            retry_after: 300,
            limit: 5,
            reset_time: new Date(Date.now() + 300000).toISOString()
          }
        }
      },
      'auto-improvement': {
        response: {
          status: 429,
          data: {
            message: 'Auto-improvement rate limit exceeded',
            retry_after: 180,
            limit: 50,
            reset_time: new Date(Date.now() + 180000).toISOString()
          }
        }
      },
      feedback: {
        response: {
          status: 429,
          data: {
            message: 'Feedback rate limit exceeded',
            retry_after: 60,
            limit: 1000,
            reset_time: new Date(Date.now() + 60000).toISOString()
          }
        }
      },
      bulk: {
        response: {
          status: 429,
          data: {
            message: 'Bulk operation rate limit exceeded',
            retry_after: 120,
            limit: 100,
            reset_time: new Date(Date.now() + 120000).toISOString()
          }
        }
      }
    }
    
    setMockRateLimitError(errors[type])
    setShowRateLimitDemo(true)
  }

  const handleFeedbackSubmitted = (result: any) => {
    setFeedbackResults(prev => [...prev, result])
  }

  const handleRateLimitRetry = () => {
    console.log('Rate limit retry attempted')
    setMockRateLimitError(null)
    setShowRateLimitDemo(false)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Rate Limit & Feedback Demo</h1>
          <p className="mt-2 text-gray-600">
            Test rate limit handling and feedback submission functionality
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Rate Limit Demo */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Rate Limit Handling</h2>
              <p className="text-sm text-gray-600 mb-4">
                Test different types of rate limit errors and see how they're handled.
              </p>
              
              <div className="space-y-3">
                <button
                  onClick={() => simulateRateLimitError('export')}
                  className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
                >
                  Simulate Export Rate Limit
                </button>
                
                <button
                  onClick={() => simulateRateLimitError('auto-improvement')}
                  className="w-full px-4 py-2 text-sm font-medium text-white bg-orange-600 hover:bg-orange-700 rounded-md transition-colors"
                >
                  Simulate Auto-Improvement Rate Limit
                </button>
                
                <button
                  onClick={() => simulateRateLimitError('feedback')}
                  className="w-full px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md transition-colors"
                >
                  Simulate Feedback Rate Limit
                </button>
                
                <button
                  onClick={() => simulateRateLimitError('bulk')}
                  className="w-full px-4 py-2 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 rounded-md transition-colors"
                >
                  Simulate Bulk Operation Rate Limit
                </button>
              </div>
            </div>

            {/* Rate Limit Handler Display */}
            {showRateLimitDemo && mockRateLimitError && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Rate Limit Handler</h3>
                <RateLimitHandler
                  error={mockRateLimitError}
                  onRetry={handleRateLimitRetry}
                  onDismiss={() => {
                    setMockRateLimitError(null)
                    setShowRateLimitDemo(false)
                  }}
                />
              </div>
            )}
          </div>

          {/* Feedback Demo */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Feedback Submission</h2>
              <p className="text-sm text-gray-600 mb-4">
                Test the feedback form with different feedback types.
              </p>
              
              <button
                onClick={() => setShowFeedbackDemo(!showFeedbackDemo)}
                className="w-full px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md transition-colors"
              >
                {showFeedbackDemo ? 'Hide Feedback Form' : 'Show Feedback Form'}
              </button>
            </div>

            {/* Feedback Form Display */}
            {showFeedbackDemo && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Feedback Form</h3>
                <FeedbackForm
                  transactionId={1}
                  currentCategory="Food & Dining"
                  currentSubcategory="Restaurants"
                  onFeedbackSubmitted={handleFeedbackSubmitted}
                  onCancel={() => setShowFeedbackDemo(false)}
                />
              </div>
            )}

            {/* Feedback Results */}
            {feedbackResults.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Feedback Results</h3>
                <div className="space-y-3">
                  {feedbackResults.map((result, index) => (
                    <div key={index} className="p-3 bg-green-50 rounded-lg border border-green-200">
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-medium text-green-900">
                            {result.feedback_type.replace('_', ' ')}
                          </span>
                          <span className="text-sm text-green-700 ml-2">
                            (ID: {result.feedback_id})
                          </span>
                        </div>
                        <span className="text-xs text-green-600">
                          {result.ml_learning ? 'ML Learning' : 'Recorded'}
                        </span>
                      </div>
                      <p className="text-sm text-green-700 mt-1">
                        Impact: {result.impact.replace('_', ' ')}
                      </p>
                    </div>
                  ))}
                </div>
                
                <button
                  onClick={() => setFeedbackResults([])}
                  className="mt-4 px-3 py-1 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors"
                >
                  Clear Results
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-8 bg-blue-50 rounded-lg border border-blue-200 p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-3">How to Test</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-blue-900 mb-2">Rate Limit Handling:</h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Click any rate limit simulation button</li>
                <li>• Observe the countdown timer and retry functionality</li>
                <li>• Test the dismiss and retry actions</li>
                <li>• Notice the different icons and messages for each type</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-blue-900 mb-2">Feedback System:</h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Show the feedback form and test different feedback types</li>
                <li>• Try submitting feedback with and without comments</li>
                <li>• Test the "suggest alternative" option</li>
                <li>• Observe the success messages and ML learning status</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
