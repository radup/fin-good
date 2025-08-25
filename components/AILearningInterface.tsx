'use client'

import React, { useState, useEffect } from 'react'
import { Brain, TrendingUp, TrendingDown, Target, BarChart3, RefreshCw, CheckCircle, XCircle, HelpCircle, Info, Zap, BookOpen, Users, Star, Settings, Play, Pause, RotateCcw } from 'lucide-react'

interface ModelPerformance {
  accuracy: number
  precision: number
  recall: number
  f1Score: number
  trainingExamples: number
  lastTrainingDate: Date
  improvementRate: number
}

interface TrainingSession {
  id: string
  startTime: Date
  endTime?: Date
  status: 'running' | 'completed' | 'failed'
  progress: number
  examplesProcessed: number
  accuracyGain: number
  errors: string[]
}

interface UserFeedbackAnalytics {
  totalFeedback: number
  positiveFeedback: number
  negativeFeedback: number
  partialFeedback: number
  averageConfidence: number
  topCorrections: {
    category: string
    count: number
    commonReason: string
  }[]
  recentImprovements: {
    date: Date
    accuracyGain: number
    description: string
  }[]
}

interface AILearningInterfaceProps {
  modelPerformance: ModelPerformance
  trainingSessions: TrainingSession[]
  userFeedback: UserFeedbackAnalytics
  onStartTraining?: () => void
  onStopTraining?: () => void
  onResetModel?: () => void
  className?: string
}

export default function AILearningInterface({
  modelPerformance,
  trainingSessions,
  userFeedback,
  onStartTraining,
  onStopTraining,
  onResetModel,
  className = ''
}: AILearningInterfaceProps) {
  const [activeTab, setActiveTab] = useState<'performance' | 'training' | 'feedback' | 'settings'>('performance')
  const [showResetConfirmation, setShowResetConfirmation] = useState(false)
  const [expandedMetrics, setExpandedMetrics] = useState<string[]>([])

  const currentTraining = trainingSessions.find(session => session.status === 'running')

  const toggleMetric = (metric: string) => {
    setExpandedMetrics(prev => 
      prev.includes(metric) 
        ? prev.filter(m => m !== metric)
        : [...prev, metric]
    )
  }

  const getPerformanceColor = (value: number, threshold: number) => {
    if (value >= threshold) return 'text-green-600'
    if (value >= threshold * 0.8) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getPerformanceIcon = (value: number, threshold: number) => {
    if (value >= threshold) return <TrendingUp className="w-4 h-4 text-green-600" />
    if (value >= threshold * 0.8) return <Target className="w-4 h-4 text-yellow-600" />
    return <TrendingDown className="w-4 h-4 text-red-600" />
  }

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="card therapeutic-transition">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Brain className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">AI Learning Interface</h3>
              <p className="text-sm text-gray-600">Monitor and improve AI model performance</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {currentTraining && (
              <div className="flex items-center gap-2 px-3 py-1 bg-blue-100 rounded-full">
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-blue-700">Training...</span>
              </div>
            )}
            <button
              onClick={() => setActiveTab('settings')}
              className="p-2 text-gray-400 hover:text-gray-600 therapeutic-transition"
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
        {[
          { id: 'performance', label: 'Performance', icon: <BarChart3 className="w-4 h-4" /> },
          { id: 'training', label: 'Training', icon: <Play className="w-4 h-4" /> },
          { id: 'feedback', label: 'Feedback', icon: <Users className="w-4 h-4" /> },
          { id: 'settings', label: 'Settings', icon: <Settings className="w-4 h-4" /> }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === tab.id
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Performance Tab */}
      {activeTab === 'performance' && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card therapeutic-transition">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">Accuracy</h4>
                {getPerformanceIcon(modelPerformance.accuracy, 90)}
              </div>
              <p className={`text-2xl font-bold ${getPerformanceColor(modelPerformance.accuracy, 90)}`}>
                {modelPerformance.accuracy.toFixed(1)}%
              </p>
              <p className="text-sm text-gray-600">Overall accuracy</p>
            </div>

            <div className="card therapeutic-transition">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">Precision</h4>
                {getPerformanceIcon(modelPerformance.precision, 85)}
              </div>
              <p className={`text-2xl font-bold ${getPerformanceColor(modelPerformance.precision, 85)}`}>
                {modelPerformance.precision.toFixed(1)}%
              </p>
              <p className="text-sm text-gray-600">Correct predictions</p>
            </div>

            <div className="card therapeutic-transition">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">Recall</h4>
                {getPerformanceIcon(modelPerformance.recall, 85)}
              </div>
              <p className={`text-2xl font-bold ${getPerformanceColor(modelPerformance.recall, 85)}`}>
                {modelPerformance.recall.toFixed(1)}%
              </p>
              <p className="text-sm text-gray-600">Complete detection</p>
            </div>

            <div className="card therapeutic-transition">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">F1 Score</h4>
                {getPerformanceIcon(modelPerformance.f1Score, 85)}
              </div>
              <p className={`text-2xl font-bold ${getPerformanceColor(modelPerformance.f1Score, 85)}`}>
                {modelPerformance.f1Score.toFixed(1)}%
              </p>
              <p className="text-sm text-gray-600">Balanced measure</p>
            </div>
          </div>

          {/* Training Progress */}
          <div className="card therapeutic-transition">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Training Progress</h3>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Improvement Rate:</span>
                <span className={`text-sm font-medium ${modelPerformance.improvementRate >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {modelPerformance.improvementRate >= 0 ? '+' : ''}{modelPerformance.improvementRate.toFixed(2)}%
                </span>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Training Examples</span>
                <span className="text-sm font-medium text-gray-900">
                  {modelPerformance.trainingExamples.toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Last Training</span>
                <span className="text-sm font-medium text-gray-900">
                  {formatDate(modelPerformance.lastTrainingDate)}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Training Tab */}
      {activeTab === 'training' && (
        <div className="space-y-6">
          {/* Training Controls */}
          <div className="card therapeutic-transition">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Training Controls</h3>
              <div className="flex gap-2">
                {currentTraining ? (
                  <button
                    onClick={onStopTraining}
                    className="btn-secondary therapeutic-transition"
                  >
                    <Pause className="w-4 h-4 mr-2" />
                    Stop Training
                  </button>
                ) : (
                  <button
                    onClick={onStartTraining}
                    className="btn-primary therapeutic-transition"
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Start Training
                  </button>
                )}
                <button
                  onClick={() => setShowResetConfirmation(true)}
                  className="btn-secondary therapeutic-transition"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Reset Model
                </button>
              </div>
            </div>

            {currentTraining && (
              <div className="p-4 bg-brand-primary-lightest rounded-lg border border-brand-primary-light">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-brand-primary-dark">Current Training Session</h4>
                  <span className="text-sm text-brand-primary">Progress: {currentTraining.progress}%</span>
                </div>
                <div className="w-full bg-brand-primary-light rounded-full h-2 mb-2">
                  <div 
                    className="bg-brand-primary h-2 rounded-full transition-all duration-300"
                    style={{ width: `${currentTraining.progress}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-sm text-brand-primary-dark">
                  <span>Examples processed: {currentTraining.examplesProcessed.toLocaleString()}</span>
                  <span>Accuracy gain: +{currentTraining.accuracyGain.toFixed(2)}%</span>
                </div>
              </div>
            )}
          </div>

          {/* Training History */}
          <div className="card therapeutic-transition">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Training History</h3>
            <div className="space-y-3">
              {trainingSessions.slice(0, 5).map(session => (
                <div key={session.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${
                      session.status === 'completed' ? 'bg-emerald-500' :
                      session.status === 'running' ? 'bg-brand-primary' : 'bg-red-500'
                    }`} />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        Training Session {session.id.slice(-6)}
                      </p>
                      <p className="text-xs text-gray-600">
                        {formatDate(session.startTime)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">
                      {session.examplesProcessed.toLocaleString()} examples
                    </p>
                    <p className="text-xs text-gray-600">
                      +{session.accuracyGain.toFixed(2)}% accuracy
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Feedback Tab */}
      {activeTab === 'feedback' && (
        <div className="space-y-6">
          {/* Feedback Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card therapeutic-transition">
              <div className="flex items-center gap-2 mb-2">
                <Users className="w-5 h-5 text-brand-primary" />
                <h4 className="font-medium text-gray-900">Total Feedback</h4>
              </div>
              <p className="text-2xl font-bold text-gray-900">{userFeedback.totalFeedback}</p>
              <p className="text-sm text-gray-600">User interactions</p>
            </div>

            <div className="card therapeutic-transition">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="w-5 h-5 text-emerald-600" />
                <h4 className="font-medium text-gray-900">Positive</h4>
              </div>
              <p className="text-2xl font-bold text-emerald-600">{userFeedback.positiveFeedback}</p>
              <p className="text-sm text-gray-600">Correct predictions</p>
            </div>

            <div className="card therapeutic-transition">
              <div className="flex items-center gap-2 mb-2">
                <XCircle className="w-5 h-5 text-red-600" />
                <h4 className="font-medium text-gray-900">Negative</h4>
              </div>
              <p className="text-2xl font-bold text-red-600">{userFeedback.negativeFeedback}</p>
              <p className="text-sm text-gray-600">Incorrect predictions</p>
            </div>

            <div className="card therapeutic-transition">
              <div className="flex items-center gap-2 mb-2">
                <HelpCircle className="w-5 h-5 text-yellow-600" />
                <h4 className="font-medium text-gray-900">Partial</h4>
              </div>
              <p className="text-2xl font-bold text-yellow-600">{userFeedback.partialFeedback}</p>
              <p className="text-sm text-gray-600">Partially correct</p>
            </div>
          </div>

          {/* Top Corrections */}
          <div className="card therapeutic-transition">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Top Categories Needing Improvement</h3>
            <div className="space-y-3">
              {userFeedback.topCorrections.map((correction, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{correction.category}</p>
                    <p className="text-sm text-gray-600">{correction.commonReason}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-red-600">{correction.count}</p>
                    <p className="text-xs text-gray-600">corrections</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Improvements */}
          <div className="card therapeutic-transition">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Improvements</h3>
            <div className="space-y-3">
              {userFeedback.recentImprovements.map((improvement, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                  <div>
                    <p className="font-medium text-green-900">{improvement.description}</p>
                    <p className="text-sm text-green-700">{formatDate(improvement.date)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-green-600">+{improvement.accuracyGain.toFixed(2)}%</p>
                    <p className="text-xs text-green-600">accuracy gain</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <div className="space-y-6">
          <div className="card therapeutic-transition">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Model Settings</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Auto-training Threshold
                </label>
                <input
                  type="range"
                  min="50"
                  max="95"
                  defaultValue="80"
                  className="w-full"
                />
                <p className="text-sm text-gray-600 mt-1">
                  Start training when accuracy drops below this threshold
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Learning Rate
                </label>
                <select className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option value="0.001">Conservative (0.001)</option>
                  <option value="0.01" selected>Balanced (0.01)</option>
                  <option value="0.1">Aggressive (0.1)</option>
                </select>
                <p className="text-sm text-gray-600 mt-1">
                  How quickly the model adapts to new data
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Feedback Weight
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="2.0"
                  step="0.1"
                  defaultValue="1.0"
                  className="w-full"
                />
                <p className="text-sm text-gray-600 mt-1">
                  How much user feedback influences training
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reset Confirmation Modal */}
      {showResetConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Reset AI Model?</h3>
            <p className="text-gray-600 mb-6">
              This will reset the AI model to its initial state. All learned patterns and improvements will be lost. This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  onResetModel?.()
                  setShowResetConfirmation(false)
                }}
                className="btn-danger therapeutic-transition"
              >
                Reset Model
              </button>
              <button
                onClick={() => setShowResetConfirmation(false)}
                className="btn-secondary therapeutic-transition"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
