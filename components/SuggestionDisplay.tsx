'use client'

import React, { useState, useEffect } from 'react'
import { 
  Lightbulb, 
  Brain, 
  Settings, 
  CheckCircle, 
  Clock,
  TrendingUp,
  Zap,
  Sparkles,
  Target,
  AlertCircle,
  RefreshCw
} from 'lucide-react'
import { transactionAPI } from '@/lib/api'
import type { CategorySuggestions, CategorySuggestion } from '@/lib/api'

interface SuggestionDisplayProps {
  transactionId: number
  currentCategory: string
  currentSubcategory?: string
  onSuggestionApplied?: (category: string, subcategory?: string) => void
  className?: string
}

export default function SuggestionDisplay({ 
  transactionId,
  currentCategory,
  currentSubcategory,
  onSuggestionApplied,
  className = ''
}: SuggestionDisplayProps) {
  const [suggestions, setSuggestions] = useState<CategorySuggestions | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showDetails, setShowDetails] = useState(false)

  const fetchSuggestions = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await transactionAPI.getCategorySuggestions(transactionId, {
        include_ml: true,
        include_rules: true
      })
      
      setSuggestions(response.data)
    } catch (err: any) {
      console.error('Failed to fetch suggestions:', err)
      
      // For development/testing, provide mock suggestions when API is not available
      if (process.env.NODE_ENV === 'development') {
        console.log('Using mock category suggestions for development')
        setSuggestions({
          transaction_id: transactionId,
          description: 'Sample Transaction',
          amount: 25.50,
          current_category: currentCategory,
          current_subcategory: currentSubcategory,
          suggestions: [
            {
              category: 'Food & Dining',
              subcategory: 'Restaurants',
              confidence: 0.85,
              source: 'ml',
              reasoning: 'High confidence based on merchant name and amount pattern'
            },
            {
              category: 'Food & Dining',
              subcategory: 'Coffee Shops',
              confidence: 0.72,
              source: 'rule',
              reasoning: 'Rule match: merchant contains "coffee" or "cafe"'
            },
            {
              category: 'Transportation',
              subcategory: 'Public Transit',
              confidence: 0.45,
              source: 'ml',
              reasoning: 'Lower confidence: could be transit fare'
            }
          ],
          rule_matches: [
            {
              category: 'Food & Dining',
              subcategory: 'Coffee Shops',
              confidence: 0.72,
              source: 'rule',
              reasoning: 'Rule match: merchant contains "coffee" or "cafe"'
            }
          ],
          ml_predictions: [
            {
              category: 'Food & Dining',
              subcategory: 'Restaurants',
              confidence: 0.85,
              source: 'ml',
              reasoning: 'High confidence based on merchant name and amount pattern'
            },
            {
              category: 'Transportation',
              subcategory: 'Public Transit',
              confidence: 0.45,
              source: 'ml',
              reasoning: 'Lower confidence: could be transit fare'
            }
          ],
          confidence_threshold: 0.6
        })
        return
      }
      
      // Handle specific error cases for production
      if (err.response?.status === 401) {
        setError('Authentication required. Please log in.')
      } else if (err.response?.status === 403) {
        setError('Access denied. You do not have permission to view suggestions.')
      } else if (err.response?.status === 404) {
        setError('Transaction not found.')
      } else if (err.response?.status === 429) {
        setError('Rate limit exceeded. Please try again later.')
      } else if (err.response?.status >= 500) {
        setError('Server error. Please try again later.')
      } else {
        setError(err.response?.data?.detail || 'Failed to load suggestions. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSuggestions()
  }, [transactionId])

  const handleApplySuggestion = (suggestion: CategorySuggestion) => {
    if (onSuggestionApplied) {
      onSuggestionApplied(suggestion.category, suggestion.subcategory)
    }
  }

  const formatConfidence = (confidence: number) => `${(confidence * 100).toFixed(0)}%`
  
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-50 border-green-200'
    if (confidence >= 0.6) return 'text-blue-600 bg-blue-50 border-blue-200'
    if (confidence >= 0.4) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    return 'text-gray-600 bg-gray-50 border-gray-200'
  }

  const getSourceIcon = (source: 'rule' | 'ml') => {
    return source === 'ml' ? <Brain className="w-4 h-4" /> : <Settings className="w-4 h-4" />
  }

  const getSourceLabel = (source: 'rule' | 'ml') => {
    return source === 'ml' ? 'ML Prediction' : 'Rule Match'
  }

  if (loading) {
    return (
      <div className={`p-4 bg-blue-50 rounded-lg border border-blue-200 ${className}`}>
        <div className="flex items-center">
          <Clock className="w-5 h-5 mr-3 animate-spin text-blue-600" />
          <span className="text-blue-700">Loading suggestions...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`p-4 bg-red-50 rounded-lg border border-red-200 ${className}`}>
        <div className="flex items-center">
          <AlertCircle className="w-5 h-5 mr-3 text-red-500" />
          <span className="text-red-700">{error}</span>
        </div>
      </div>
    )
  }

  if (!suggestions || suggestions.suggestions.length === 0) {
    return (
      <div className={`p-4 bg-gray-50 rounded-lg border border-gray-200 ${className}`}>
        <div className="flex items-center">
          <Lightbulb className="w-5 h-5 mr-3 text-gray-500" />
          <span className="text-gray-600">No suggestions available for this transaction.</span>
        </div>
      </div>
    )
  }

  const topSuggestions = suggestions.suggestions
    .filter(s => s.confidence >= suggestions.confidence_threshold)
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 3)

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Lightbulb className="w-5 h-5 mr-2 text-yellow-600" />
            <h3 className="font-medium text-gray-900">Category Suggestions</h3>
          </div>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-100 px-2 py-1 rounded transition-colors"
          >
            {showDetails ? 'Hide Details' : 'Show Details'}
          </button>
        </div>
        <p className="text-sm text-gray-600 mt-1">
          Based on transaction patterns and ML analysis
        </p>
      </div>

      <div className="p-4">
        {/* Top Suggestions */}
        <div className="space-y-3">
          {topSuggestions.map((suggestion, index) => (
            <div
              key={`${suggestion.category}-${suggestion.subcategory}-${index}`}
              className={`p-3 rounded-lg border ${getConfidenceColor(suggestion.confidence)}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-1">
                    {getSourceIcon(suggestion.source)}
                    <span className="text-xs font-medium ml-2">
                      {getSourceLabel(suggestion.source)}
                    </span>
                    <span className="text-xs ml-2 px-2 py-1 bg-white bg-opacity-50 rounded">
                      {formatConfidence(suggestion.confidence)}
                    </span>
                  </div>
                  <div className="font-medium">
                    {suggestion.category}
                    {suggestion.subcategory && (
                      <span className="text-sm font-normal text-gray-600 ml-1">
                        → {suggestion.subcategory}
                      </span>
                    )}
                  </div>
                  {suggestion.reasoning && (
                    <p className="text-xs text-gray-600 mt-1">{suggestion.reasoning}</p>
                  )}
                </div>
                <button
                  onClick={() => handleApplySuggestion(suggestion)}
                  className="ml-3 px-3 py-1 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-400 transition-colors"
                >
                  Apply
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Details Panel */}
        {showDetails && (
          <div className="mt-6 space-y-4">
            {/* ML Predictions */}
            {suggestions.ml_predictions.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
                  <Brain className="w-4 h-4 mr-2 text-purple-600" />
                  ML Predictions
                </h4>
                <div className="space-y-2">
                  {suggestions.ml_predictions.map((prediction, index) => (
                    <div
                      key={`ml-${index}`}
                      className="p-2 bg-purple-50 rounded border border-purple-200"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-medium">{prediction.category}</span>
                          {prediction.subcategory && (
                            <span className="text-sm text-gray-600 ml-1">
                              → {prediction.subcategory}
                            </span>
                          )}
                          <span className="text-xs text-purple-600 ml-2">
                            {formatConfidence(prediction.confidence)}
                          </span>
                        </div>
                        {prediction.reasoning && (
                          <span className="text-xs text-gray-600">{prediction.reasoning}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Rule Matches */}
            {suggestions.rule_matches.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
                  <Settings className="w-4 h-4 mr-2 text-blue-600" />
                  Rule Matches
                </h4>
                <div className="space-y-2">
                  {suggestions.rule_matches.map((rule, index) => (
                    <div
                      key={`rule-${index}`}
                      className="p-2 bg-blue-50 rounded border border-blue-200"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-medium">{rule.category}</span>
                          {rule.subcategory && (
                            <span className="text-sm text-gray-600 ml-1">
                              → {rule.subcategory}
                            </span>
                          )}
                          <span className="text-xs text-blue-600 ml-2">
                            {formatConfidence(rule.confidence)}
                          </span>
                        </div>
                        {rule.reasoning && (
                          <span className="text-xs text-gray-600">{rule.reasoning}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Current Category */}
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <h4 className="text-sm font-medium text-gray-900 mb-1">Current Category</h4>
              <div className="text-sm">
                <span className="font-medium">{suggestions.current_category}</span>
                {suggestions.current_subcategory && (
                  <span className="text-gray-600 ml-1">
                    → {suggestions.current_subcategory}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Refresh Button */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <button
            onClick={fetchSuggestions}
            className="w-full px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded-md transition-colors flex items-center justify-center"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh Suggestions
          </button>
        </div>
      </div>
    </div>
  )
}
