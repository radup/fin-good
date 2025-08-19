import React, { useState, useEffect } from 'react'
import { patternRecognitionAPI } from '@/lib/api'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { Search, TrendingUp, Target, Zap, BarChart3, Lightbulb, CheckCircle, AlertCircle } from 'lucide-react'

interface Pattern {
  pattern_id: string
  pattern_type: 'vendor' | 'amount' | 'frequency' | 'category' | 'time' | 'location' | 'description'
  confidence_score: number
  support_count: number
  pattern_data: {
    vendor?: string
    amount_range?: { min: number; max: number }
    frequency?: { count: number; period: string }
    category?: string
    time_pattern?: string
    location?: string
    description_keywords?: string[]
  }
  examples: Array<{
    transaction_id: number
    description: string
    amount: number
    date: string
    vendor: string
    category: string
  }>
  created_at: string
}

interface PatternAnalysisResponse {
  message: string
  analysis_id: string
  total_transactions_analyzed: number
  patterns_found: number
  analysis_duration: number
  algorithms_used: string[]
  confidence_threshold: number
}

interface PatternRuleGenerationResponse {
  message: string
  rule_id: string
  pattern_id: string
  generated_rule: {
    condition: string
    action: string
    confidence: number
    estimated_impact: number
  }
  created_at: string
}

export const PatternRecognition: React.FC = () => {
  const [patterns, setPatterns] = useState<Pattern[]>([])
  const [stats, setStats] = useState({
    total_patterns: 0,
    high_confidence_patterns: 0,
    active_rules: 0,
    accuracy_rate: 0
  })
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)
  const [selectedPattern, setSelectedPattern] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPatterns()
    fetchStats()
  }, [])

  const fetchPatterns = async () => {
    try {
      setLoading(true)
      const response = await patternRecognitionAPI.getRecognizedPatterns()
      setPatterns(response.data)
      setError(null)
    } catch (err) {
      console.error('Error fetching patterns:', err)
      setError('Error loading patterns')
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await patternRecognitionAPI.getPatternStats()
      setStats(response.data)
    } catch (err) {
      console.error('Error fetching pattern stats:', err)
    }
  }

  const handleScan = async () => {
    try {
      setScanning(true)
      setMessage(null)
      
      const response = await patternRecognitionAPI.analyzePatterns({
        confidence_threshold: 0.7,
        max_patterns: 50,
        include_examples: true
      })
      
      setMessage(`Analysis completed! Found ${response.data.patterns_found} patterns in ${response.data.analysis_duration.toFixed(1)}s`)
      
      // Refresh patterns after scan
      await fetchPatterns()
      await fetchStats()
    } catch (err) {
      console.error('Error during pattern analysis:', err)
      setError('Error during pattern analysis')
    } finally {
      setScanning(false)
    }
  }

  const handleGenerateRule = async (patternId: string) => {
    try {
      const response = await patternRecognitionAPI.generateRule(patternId)
      setMessage(`Rule generated successfully! Estimated impact: ${response.data.generated_rule.estimated_impact} transactions`)
      
      // Refresh stats after rule generation
      await fetchStats()
    } catch (err) {
      console.error('Error generating rule:', err)
      setError('Error generating rule')
    }
  }

  const getPatternIcon = (type: string) => {
    switch (type) {
      case 'vendor': return <Target className="w-4 h-4" />
      case 'amount': return <BarChart3 className="w-4 h-4" />
      case 'frequency': return <TrendingUp className="w-4 h-4" />
      case 'category': return <CheckCircle className="w-4 h-4" />
      case 'time': return <Zap className="w-4 h-4" />
      case 'location': return <Target className="w-4 h-4" />
      case 'description': return <Lightbulb className="w-4 h-4" />
      default: return <AlertCircle className="w-4 h-4" />
    }
  }

  const getPatternTypeLabel = (type: string) => {
    return type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600'
    if (confidence >= 0.7) return 'text-yellow-600'
    return 'text-red-600'
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-6"></div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="bg-white rounded-lg shadow">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-medium text-gray-900">Pattern Recognition</h2>
              <p className="text-sm text-gray-500">
                Discover intelligent patterns in your transaction data
              </p>
            </div>
            <button
              onClick={handleScan}
              disabled={scanning}
              className="btn-primary disabled:opacity-50 flex items-center gap-2"
            >
              <Search className="w-4 h-4" />
              {scanning ? 'Analyzing...' : 'Analyze Patterns'}
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Total Patterns:</span>
              <span className="ml-2 font-medium">{stats.total_patterns}</span>
            </div>
            <div>
              <span className="text-gray-500">High Confidence:</span>
              <span className="ml-2 font-medium">{stats.high_confidence_patterns}</span>
            </div>
            <div>
              <span className="text-gray-500">Active Rules:</span>
              <span className="ml-2 font-medium">{stats.active_rules}</span>
            </div>
            <div>
              <span className="text-gray-500">Accuracy Rate:</span>
              <span className="ml-2 font-medium">{(stats.accuracy_rate * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Messages */}
        {message && (
          <div className="px-6 py-3 bg-green-50 border-b border-green-200">
            <p className="text-sm text-green-800">{message}</p>
          </div>
        )}

        {error && (
          <div className="px-6 py-3 bg-red-50 border-b border-red-200">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Content */}
        <div className="p-6">
          {patterns.length === 0 ? (
            <div className="text-center py-8">
              <Lightbulb className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No patterns found</h3>
              <p className="text-gray-500 mb-4">
                Click "Analyze Patterns" to discover intelligent patterns in your transaction data.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {patterns.map((pattern) => (
                <div
                  key={pattern.pattern_id}
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      {getPatternIcon(pattern.pattern_type)}
                      <div>
                        <h3 className="font-medium text-gray-900">
                          {getPatternTypeLabel(pattern.pattern_type)} Pattern
                        </h3>
                        <p className="text-sm text-gray-500">
                          Support: {pattern.support_count} transactions • Confidence: 
                          <span className={`ml-1 ${getConfidenceColor(pattern.confidence_score)}`}>
                            {(pattern.confidence_score * 100).toFixed(1)}%
                          </span>
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleGenerateRule(pattern.pattern_id)}
                        className="btn-primary text-sm"
                      >
                        <Zap className="w-4 h-4 mr-1" />
                        Generate Rule
                      </button>
                    </div>
                  </div>

                  {/* Pattern Details */}
                  <div className="space-y-3">
                    {/* Pattern Data */}
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded">
                      <h4 className="font-medium text-blue-900 mb-2">Pattern Details</h4>
                      <div className="text-sm text-blue-800">
                        {pattern.pattern_type === 'vendor' && pattern.pattern_data.vendor && (
                          <p>Vendor: {pattern.pattern_data.vendor}</p>
                        )}
                        {pattern.pattern_type === 'amount' && pattern.pattern_data.amount_range && (
                          <p>Amount Range: ${pattern.pattern_data.amount_range.min} - ${pattern.pattern_data.amount_range.max}</p>
                        )}
                        {pattern.pattern_type === 'frequency' && pattern.pattern_data.frequency && (
                          <p>Frequency: {pattern.pattern_data.frequency.count} times per {pattern.pattern_data.frequency.period}</p>
                        )}
                        {pattern.pattern_type === 'category' && pattern.pattern_data.category && (
                          <p>Category: {pattern.pattern_data.category}</p>
                        )}
                        {pattern.pattern_type === 'time' && pattern.pattern_data.time_pattern && (
                          <p>Time Pattern: {pattern.pattern_data.time_pattern}</p>
                        )}
                        {pattern.pattern_type === 'location' && pattern.pattern_data.location && (
                          <p>Location: {pattern.pattern_data.location}</p>
                        )}
                        {pattern.pattern_type === 'description' && pattern.pattern_data.description_keywords && (
                          <p>Keywords: {pattern.pattern_data.description_keywords.join(', ')}</p>
                        )}
                      </div>
                    </div>

                    {/* Examples */}
                    <div className="p-3 bg-gray-50 border border-gray-200 rounded">
                      <h4 className="font-medium text-gray-900 mb-2">Example Transactions</h4>
                      <div className="space-y-2">
                        {pattern.examples.slice(0, 3).map((example, index) => (
                          <div key={index} className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-4">
                              <span className="font-medium text-gray-900">${example.amount}</span>
                              <span className="text-gray-700">{example.description}</span>
                              <span className="text-gray-500">{example.vendor}</span>
                              <span className="text-gray-500">{example.date}</span>
                            </div>
                            <span className="text-gray-500">{example.category}</span>
                          </div>
                        ))}
                        {pattern.examples.length > 3 && (
                          <p className="text-sm text-gray-500 mt-2">
                            +{pattern.examples.length - 3} more examples
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </ErrorBoundary>
  )
}
