'use client'

import React, { useState, useEffect } from 'react'
import { Brain, Lightbulb, TrendingUp, TrendingDown, Target, BarChart3, RefreshCw, CheckCircle, XCircle, HelpCircle, Info, Zap, BookOpen, Users, Star } from 'lucide-react'

interface AIReasoning {
  id: string
  category: string
  confidence: number
  reasoning: string[]
  factors: {
    name: string
    weight: number
    description: string
    impact: 'positive' | 'negative' | 'neutral'
  }[]
  alternatives: {
    category: string
    confidence: number
    reasoning: string
  }[]
  learningData: {
    userCorrections: number
    accuracy: number
    lastUpdated: Date
  }
}

interface UserFeedback {
  type: 'correct' | 'incorrect' | 'partial'
  explanation?: string
  suggestedCategory?: string
  confidence?: number
  timestamp: Date
}

interface AdvancedAIExplanationProps {
  reasoning: AIReasoning
  onFeedback?: (feedback: UserFeedback) => void
  onConfidenceAdjust?: (newConfidence: number) => void
  showLearning?: boolean
  className?: string
}

const CONFIDENCE_LEVELS = {
  very_high: { min: 90, label: 'Very High', color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200' },
  high: { min: 75, label: 'High', color: 'text-brand-primary', bg: 'bg-brand-primary-lightest', border: 'border-brand-primary-light' },
  medium: { min: 60, label: 'Medium', color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200' },
  low: { min: 40, label: 'Low', color: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200' },
  very_low: { min: 0, label: 'Very Low', color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' }
}

export default function AdvancedAIExplanation({
  reasoning,
  onFeedback,
  onConfidenceAdjust,
  showLearning = true,
  className = ''
}: AdvancedAIExplanationProps) {
  const [expandedSections, setExpandedSections] = useState({
    reasoning: true,
    factors: false,
    alternatives: false,
    learning: false
  })
  const [userFeedback, setUserFeedback] = useState<UserFeedback | null>(null)
  const [showFeedbackForm, setShowFeedbackForm] = useState(false)
  const [feedbackType, setFeedbackType] = useState<'correct' | 'incorrect' | 'partial'>('correct')
  const [feedbackExplanation, setFeedbackExplanation] = useState('')
  const [suggestedCategory, setSuggestedCategory] = useState('')
  const [confidenceAdjustment, setConfidenceAdjustment] = useState(reasoning.confidence)

  const getConfidenceLevel = (confidence: number) => {
    if (confidence >= 90) return CONFIDENCE_LEVELS.very_high
    if (confidence >= 75) return CONFIDENCE_LEVELS.high
    if (confidence >= 60) return CONFIDENCE_LEVELS.medium
    if (confidence >= 40) return CONFIDENCE_LEVELS.low
    return CONFIDENCE_LEVELS.very_low
  }

  const confidenceLevel = getConfidenceLevel(reasoning.confidence)

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  const handleFeedbackSubmit = () => {
    const feedback: UserFeedback = {
      type: feedbackType,
      explanation: feedbackExplanation || undefined,
      suggestedCategory: suggestedCategory || undefined,
      confidence: confidenceAdjustment,
      timestamp: new Date()
    }

    setUserFeedback(feedback)
    setShowFeedbackForm(false)
    onFeedback?.(feedback)
  }

  const handleConfidenceAdjust = () => {
    onConfidenceAdjust?.(confidenceAdjustment)
  }

  const getFactorIcon = (impact: 'positive' | 'negative' | 'neutral') => {
    switch (impact) {
      case 'positive': return <TrendingUp className="w-4 h-4 text-emerald-600" />
      case 'negative': return <TrendingDown className="w-4 h-4 text-red-600" />
      case 'neutral': return <Target className="w-4 h-4 text-gray-600" />
    }
  }

  const getFactorColor = (impact: 'positive' | 'negative' | 'neutral') => {
    switch (impact) {
      case 'positive': return 'border-l-emerald-500 bg-emerald-50'
      case 'negative': return 'border-l-red-500 bg-red-50'
      case 'neutral': return 'border-l-gray-500 bg-gray-50'
    }
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Main AI Explanation Header */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-brand-primary-lightest rounded-lg">
              <Brain className="w-5 h-5 text-brand-primary" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-gray-900">AI Reasoning</h3>
              <p className="text-xs text-gray-600">How I categorized this transaction</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${confidenceLevel.bg} ${confidenceLevel.color} ${confidenceLevel.border}`}>
              {confidenceLevel.label} Confidence
            </span>
            <span className="text-xl font-bold text-gray-900">{reasoning.confidence}%</span>
          </div>
        </div>

        {/* Category Display */}
        <div className="mb-3 p-3 bg-brand-primary-lightest rounded-lg border border-brand-primary-light">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-medium text-brand-primary text-xs">Suggested Category</h4>
              <p className="text-base font-semibold text-brand-primary">{reasoning.category}</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowFeedbackForm(true)}
                className="px-3 py-1 text-xs bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <HelpCircle className="w-3 h-3 mr-1 inline" />
                Provide Feedback
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Reasoning Breakdown */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
        <div
          className="flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors rounded-lg p-2 -m-2"
          onClick={() => toggleSection('reasoning')}
        >
          <div className="flex items-center gap-3">
            <Lightbulb className="w-4 h-4 text-brand-primary" />
            <h3 className="text-base font-medium text-gray-900">Reasoning Breakdown</h3>
          </div>
          <span className="text-xs text-gray-500">
            {expandedSections.reasoning ? 'Hide' : 'Show'} ({reasoning.reasoning.length} points)
          </span>
        </div>

        {expandedSections.reasoning && (
          <div className="mt-3 space-y-2">
            {reasoning.reasoning.map((point, index) => (
              <div key={index} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                <div className="flex-shrink-0 w-5 h-5 bg-brand-primary-lightest rounded-full flex items-center justify-center">
                  <span className="text-xs font-medium text-brand-primary">{index + 1}</span>
                </div>
                <p className="text-xs text-gray-700">{point}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Decision Factors */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
        <div
          className="flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors rounded-lg p-2 -m-2"
          onClick={() => toggleSection('factors')}
        >
          <div className="flex items-center gap-3">
            <BarChart3 className="w-4 h-4 text-brand-primary" />
            <h3 className="text-base font-medium text-gray-900">Decision Factors</h3>
          </div>
          <span className="text-xs text-gray-500">
            {expandedSections.factors ? 'Hide' : 'Show'} ({reasoning.factors.length} factors)
          </span>
        </div>

        {expandedSections.factors && (
          <div className="mt-3 space-y-2">
            {reasoning.factors.map((factor, index) => (
              <div key={index} className={`p-3 rounded-lg border-l-4 ${getFactorColor(factor.impact)}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getFactorIcon(factor.impact)}
                    <h4 className="font-medium text-gray-900 text-xs">{factor.name}</h4>
                  </div>
                  <span className="text-xs font-medium text-gray-600">
                    Weight: {factor.weight}%
                  </span>
                </div>
                <p className="text-xs text-gray-700">{factor.description}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Alternative Categories */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
        <div
          className="flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors rounded-lg p-2 -m-2"
          onClick={() => toggleSection('alternatives')}
        >
          <div className="flex items-center gap-3">
            <RefreshCw className="w-4 h-4 text-emerald-600" />
            <h3 className="text-base font-medium text-gray-900">Alternative Categories</h3>
          </div>
          <span className="text-xs text-gray-500">
            {expandedSections.alternatives ? 'Hide' : 'Show'} ({reasoning.alternatives.length} alternatives)
          </span>
        </div>

        {expandedSections.alternatives && (
          <div className="mt-3 space-y-2">
            {reasoning.alternatives.map((alt, index) => (
              <div key={index} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900 text-xs">{alt.category}</h4>
                  <span className="text-xs font-medium text-gray-600">
                    {alt.confidence}% confidence
                  </span>
                </div>
                <p className="text-xs text-gray-700">{alt.reasoning}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Learning Data */}
      {showLearning && (
        <div className="card therapeutic-transition">
          <div
            className="flex items-center justify-between cursor-pointer therapeutic-hover"
            onClick={() => toggleSection('learning')}
          >
            <div className="flex items-center gap-3">
              <BookOpen className="w-5 h-5 text-indigo-600" />
              <h3 className="text-lg font-medium text-gray-900">Learning Data</h3>
            </div>
            <span className="text-sm text-gray-500">
              {expandedSections.learning ? 'Hide' : 'Show'}
            </span>
          </div>

          {expandedSections.learning && (
            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                <div className="flex items-center gap-2 mb-2">
                  <Users className="w-4 h-4 text-indigo-600" />
                  <h4 className="font-medium text-indigo-900">User Corrections</h4>
                </div>
                <p className="text-2xl font-bold text-indigo-800">{reasoning.learningData.userCorrections}</p>
                <p className="text-sm text-indigo-600">Total corrections received</p>
              </div>

              <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="w-4 h-4 text-green-600" />
                  <h4 className="font-medium text-green-900">Accuracy</h4>
                </div>
                <p className="text-2xl font-bold text-green-800">{reasoning.learningData.accuracy}%</p>
                <p className="text-sm text-green-600">Current accuracy rate</p>
              </div>

              <div className="p-4 bg-brand-primary-lightest rounded-lg border border-brand-primary-light">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-4 h-4 text-brand-primary" />
                  <h4 className="font-medium text-brand-primary">Last Updated</h4>
                </div>
                <p className="text-sm font-medium text-brand-primary">
                  {reasoning.learningData.lastUpdated.toLocaleDateString()}
                </p>
                <p className="text-sm text-brand-primary">Model training date</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* User Feedback Form */}
      {showFeedbackForm && (
        <div className="card therapeutic-transition">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Provide Feedback</h3>
            <button
              onClick={() => setShowFeedbackForm(false)}
              className="text-gray-400 hover:text-gray-600 therapeutic-transition"
            >
              ×
            </button>
          </div>

          <div className="space-y-4">
            {/* Feedback Type Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                How accurate was this categorization?
              </label>
              <div className="grid grid-cols-3 gap-3">
                <button
                  onClick={() => setFeedbackType('correct')}
                  className={`p-3 rounded-lg border-2 therapeutic-transition ${
                    feedbackType === 'correct'
                      ? 'border-green-500 bg-green-50 text-green-700'
                      : 'border-gray-200 hover:border-green-300'
                  }`}
                >
                  <CheckCircle className="w-5 h-5 mx-auto mb-1" />
                  <span className="text-sm font-medium">Correct</span>
                </button>
                <button
                  onClick={() => setFeedbackType('partial')}
                  className={`p-3 rounded-lg border-2 therapeutic-transition ${
                    feedbackType === 'partial'
                      ? 'border-yellow-500 bg-yellow-50 text-yellow-700'
                      : 'border-gray-200 hover:border-yellow-300'
                  }`}
                >
                  <HelpCircle className="w-5 h-5 mx-auto mb-1" />
                  <span className="text-sm font-medium">Partially</span>
                </button>
                <button
                  onClick={() => setFeedbackType('incorrect')}
                  className={`p-3 rounded-lg border-2 therapeutic-transition ${
                    feedbackType === 'incorrect'
                      ? 'border-red-500 bg-red-50 text-red-700'
                      : 'border-gray-200 hover:border-red-300'
                  }`}
                >
                  <XCircle className="w-5 h-5 mx-auto mb-1" />
                  <span className="text-sm font-medium">Incorrect</span>
                </button>
              </div>
            </div>

            {/* Additional Feedback */}
            {(feedbackType === 'partial' || feedbackType === 'incorrect') && (
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    What should the correct category be?
                  </label>
                  <input
                    type="text"
                    value={suggestedCategory}
                    onChange={(e) => setSuggestedCategory(e.target.value)}
                    placeholder="Enter the correct category..."
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Additional explanation (optional)
                  </label>
                  <textarea
                    value={feedbackExplanation}
                    onChange={(e) => setFeedbackExplanation(e.target.value)}
                    placeholder="Help me understand why this categorization was wrong..."
                    rows={3}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            )}

            {/* Confidence Adjustment */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Adjust confidence level for similar transactions
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={confidenceAdjustment}
                  onChange={(e) => setConfidenceAdjustment(Number(e.target.value))}
                  className="flex-1"
                />
                <span className="text-lg font-medium text-gray-900 w-16 text-center">
                  {confidenceAdjustment}%
                </span>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                This will help calibrate confidence for future similar transactions
              </p>
            </div>

            {/* Submit Buttons */}
            <div className="flex gap-3 pt-4">
              <button
                onClick={handleFeedbackSubmit}
                className="btn-primary therapeutic-transition"
              >
                Submit Feedback
              </button>
              <button
                onClick={() => setShowFeedbackForm(false)}
                className="btn-secondary therapeutic-transition"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Feedback Confirmation */}
      {userFeedback && (
        <div className="card therapeutic-transition">
          <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg border border-green-200">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <div>
              <h4 className="font-medium text-green-900">Thank you for your feedback!</h4>
              <p className="text-sm text-green-700">
                Your input helps improve the AI's accuracy for future categorizations.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
