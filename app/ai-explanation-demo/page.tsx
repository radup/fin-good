'use client'

import React, { useState } from 'react'
import { Brain } from 'lucide-react'
import AdvancedAIExplanation from '@/components/AdvancedAIExplanation'
import AILearningInterface from '@/components/AILearningInterface'
import DrSigmundSpendAvatar from '@/components/DrSigmundSpendAvatar'

// Sample AI reasoning data
const sampleAIReasoning = {
  id: 'reasoning_001',
  category: 'Food & Dining',
  confidence: 87,
  reasoning: [
    'Transaction description contains "STARBUCKS" which is a known coffee chain',
    'Amount ($4.50) is typical for a coffee purchase',
    'Previous transactions with this vendor were categorized as Food & Dining',
    'Time of transaction (9:30 AM) is consistent with morning coffee purchases',
    'Location data shows transaction occurred near a Starbucks location'
  ],
  factors: [
    {
      name: 'Vendor Name',
      weight: 35,
      description: 'Starbucks is a well-known coffee chain with high confidence mapping',
      impact: 'positive' as const
    },
    {
      name: 'Transaction Amount',
      weight: 25,
      description: '$4.50 is within typical coffee price range ($3-7)',
      impact: 'positive' as const
    },
    {
      name: 'Time Pattern',
      weight: 20,
      description: 'Morning transaction aligns with coffee consumption patterns',
      impact: 'positive' as const
    },
    {
      name: 'Historical Data',
      weight: 15,
      description: 'Previous Starbucks transactions were correctly categorized',
      impact: 'positive' as const
    },
    {
      name: 'Location Data',
      weight: 5,
      description: 'GPS coordinates match known Starbucks location',
      impact: 'neutral' as const
    }
  ],
  alternatives: [
    {
      category: 'Entertainment',
      confidence: 8,
      reasoning: 'Could be a purchase at a Starbucks with entertainment venue'
    },
    {
      category: 'Transportation',
      confidence: 3,
      reasoning: 'Unlikely given vendor type and amount'
    },
    {
      category: 'Shopping',
      confidence: 2,
      reasoning: 'Could be merchandise, but amount suggests beverage'
    }
  ],
  learningData: {
    userCorrections: 12,
    accuracy: 94.2,
    lastUpdated: new Date('2024-01-15')
  }
}

// Sample model performance data
const sampleModelPerformance = {
  accuracy: 94.2,
  precision: 92.8,
  recall: 95.1,
  f1Score: 93.9,
  trainingExamples: 15420,
  lastTrainingDate: new Date('2024-01-15T14:30:00'),
  improvementRate: 2.3
}

// Sample training sessions
const sampleTrainingSessions = [
  {
    id: 'session_001',
    startTime: new Date('2024-01-15T10:00:00'),
    endTime: new Date('2024-01-15T14:30:00'),
    status: 'completed' as const,
    progress: 100,
    examplesProcessed: 15420,
    accuracyGain: 2.3,
    errors: []
  },
  {
    id: 'session_002',
    startTime: new Date('2024-01-14T09:00:00'),
    endTime: new Date('2024-01-14T12:15:00'),
    status: 'completed' as const,
    progress: 100,
    examplesProcessed: 12850,
    accuracyGain: 1.8,
    errors: []
  },
  {
    id: 'session_003',
    startTime: new Date('2024-01-13T15:00:00'),
    status: 'running' as const,
    progress: 65,
    examplesProcessed: 8500,
    accuracyGain: 1.2,
    errors: []
  }
]

// Sample user feedback analytics
const sampleUserFeedback = {
  totalFeedback: 1247,
  positiveFeedback: 1173,
  negativeFeedback: 58,
  partialFeedback: 16,
  averageConfidence: 89.4,
  topCorrections: [
    {
      category: 'Entertainment',
      count: 12,
      commonReason: 'Confused with dining establishments that have entertainment'
    },
    {
      category: 'Healthcare',
      count: 8,
      commonReason: 'Medical purchases at retail locations'
    },
    {
      category: 'Transportation',
      count: 6,
      commonReason: 'Ride-sharing services with food delivery'
    }
  ],
  recentImprovements: [
    {
      date: new Date('2024-01-15T14:30:00'),
      accuracyGain: 2.3,
      description: 'Improved recognition of coffee shop chains'
    },
    {
      date: new Date('2024-01-14T12:15:00'),
      accuracyGain: 1.8,
      description: 'Better handling of entertainment vs dining categories'
    },
    {
      date: new Date('2024-01-13T10:00:00'),
      accuracyGain: 1.5,
      description: 'Enhanced medical expense categorization'
    }
  ]
}

export default function AIExplanationDemo() {
  const [currentReasoning, setCurrentReasoning] = useState(sampleAIReasoning)
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)
  const [isTraining, setIsTraining] = useState(false)

  const handleFeedback = (feedback: any) => {
    console.log('User feedback received:', feedback)
    setFeedbackSubmitted(true)
    
    // Simulate AI learning from feedback
    setTimeout(() => {
      setFeedbackSubmitted(false)
      // Update the reasoning with improved confidence
      setCurrentReasoning(prev => ({
        ...prev,
        confidence: Math.min(100, prev.confidence + (feedback.type === 'correct' ? 1 : -2))
      }))
    }, 3000)
  }

  const handleConfidenceAdjust = (newConfidence: number) => {
    console.log('Confidence adjusted to:', newConfidence)
    setCurrentReasoning(prev => ({
      ...prev,
      confidence: newConfidence
    }))
  }

  const handleStartTraining = () => {
    setIsTraining(true)
    console.log('Starting AI training...')
    
    // Simulate training completion
    setTimeout(() => {
      setIsTraining(false)
    }, 5000)
  }

  const handleStopTraining = () => {
    setIsTraining(false)
    console.log('Stopping AI training...')
  }

  const handleResetModel = () => {
    console.log('Resetting AI model...')
    setCurrentReasoning(sampleAIReasoning)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center gap-4">
              <DrSigmundSpendAvatar 
                size="md" 
                mood="analytical"
                message="Let me explain how I think!"
                showMessage={true}
              />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Advanced AI Explanation</h1>
                <p className="text-gray-600">Transparent AI reasoning and interactive learning</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* AI Explanation Interface */}
          <div className="space-y-6">
            <div className="card therapeutic-transition">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Brain className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">AI Reasoning Display</h2>
                  <p className="text-gray-600">See how the AI categorizes transactions</p>
                </div>
              </div>
              
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 mb-4">
                <h3 className="font-medium text-gray-900 mb-2">Sample Transaction</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Description:</span>
                    <span className="font-medium">STARBUCKS #1234</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Amount:</span>
                    <span className="font-medium">$4.50</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Date:</span>
                    <span className="font-medium">2024-01-15 09:30 AM</span>
                  </div>
                </div>
              </div>
            </div>

            <AdvancedAIExplanation
              reasoning={currentReasoning}
              onFeedback={handleFeedback}
              onConfidenceAdjust={handleConfidenceAdjust}
              showLearning={true}
            />
          </div>

          {/* AI Learning Interface */}
          <div className="space-y-6">
            <div className="card therapeutic-transition">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Brain className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">AI Learning Interface</h2>
                  <p className="text-gray-600">Monitor and control AI model training</p>
                </div>
              </div>
            </div>

            <AILearningInterface
              modelPerformance={sampleModelPerformance}
              trainingSessions={sampleTrainingSessions}
              userFeedback={sampleUserFeedback}
              onStartTraining={handleStartTraining}
              onStopTraining={handleStopTraining}
              onResetModel={handleResetModel}
            />
          </div>
        </div>

        {/* Feedback Status */}
        {feedbackSubmitted && (
          <div className="fixed bottom-4 right-4 bg-green-50 border border-green-200 rounded-lg p-4 shadow-lg">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-green-600 rounded-full animate-pulse"></div>
              <div>
                <h4 className="font-medium text-green-900">AI Learning in Progress</h4>
                <p className="text-sm text-green-700">Your feedback is being processed...</p>
              </div>
            </div>
          </div>
        )}

        {/* Training Status */}
        {isTraining && (
          <div className="fixed bottom-4 left-4 bg-blue-50 border border-blue-200 rounded-lg p-4 shadow-lg">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
              <div>
                <h4 className="font-medium text-blue-900">Model Training Active</h4>
                <p className="text-sm text-blue-700">Processing new data and improving accuracy...</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
