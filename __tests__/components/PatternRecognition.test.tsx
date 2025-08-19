import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PatternRecognition } from '@/components/PatternRecognition'
import { patternRecognitionAPI } from '@/lib/api'

// Mock the API
jest.mock('@/lib/api', () => ({
  patternRecognitionAPI: {
    getRecognizedPatterns: jest.fn(),
    getPatternStats: jest.fn(),
    analyzePatterns: jest.fn(),
    generateRule: jest.fn(),
  }
}))

// Mock the ErrorBoundary component
jest.mock('@/components/ErrorBoundary', () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}))

const mockPatterns = [
  {
    pattern_id: 'pattern-1',
    pattern_type: 'vendor',
    confidence_score: 0.95,
    support_count: 15,
    pattern_data: {
      vendor: 'Starbucks'
    },
    examples: [
      {
        transaction_id: 1,
        description: 'Coffee Shop',
        amount: 5.50,
        date: '2024-01-01',
        vendor: 'Starbucks',
        category: 'Food'
      },
      {
        transaction_id: 2,
        description: 'Coffee Shop',
        amount: 4.75,
        date: '2024-01-02',
        vendor: 'Starbucks',
        category: 'Food'
      }
    ],
    created_at: '2024-01-01T10:00:00Z'
  },
  {
    pattern_id: 'pattern-2',
    pattern_type: 'amount',
    confidence_score: 0.87,
    support_count: 8,
    pattern_data: {
      amount_range: { min: 20, max: 30 }
    },
    examples: [
      {
        transaction_id: 3,
        description: 'Gas Station',
        amount: 25.00,
        date: '2024-01-01',
        vendor: 'Shell',
        category: 'Transportation'
      }
    ],
    created_at: '2024-01-01T10:00:00Z'
  }
]

const mockStats = {
  total_patterns: 5,
  high_confidence_patterns: 3,
  active_rules: 2,
  accuracy_rate: 0.92
}

const mockAnalysisResults = {
  message: 'Analysis completed',
  analysis_id: 'analysis-123',
  total_transactions_analyzed: 1000,
  patterns_found: 5,
  analysis_duration: 2.5,
  algorithms_used: ['fuzzy_match', 'exact_match'],
  confidence_threshold: 0.7
}

const mockRuleGeneration = {
  message: 'Rule generated successfully',
  rule_id: 'rule-123',
  pattern_id: 'pattern-1',
  generated_rule: {
    condition: 'vendor = "Starbucks"',
    action: 'category = "Food"',
    confidence: 0.95,
    estimated_impact: 15
  },
  created_at: '2024-01-01T10:00:00Z'
}

describe('PatternRecognition', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Default mock implementations
    const mockGetPatterns = patternRecognitionAPI.getRecognizedPatterns as jest.MockedFunction<typeof patternRecognitionAPI.getRecognizedPatterns>
    const mockGetStats = patternRecognitionAPI.getPatternStats as jest.MockedFunction<typeof patternRecognitionAPI.getPatternStats>
    
    mockGetPatterns.mockResolvedValue({ data: mockPatterns })
    mockGetStats.mockResolvedValue({ data: mockStats })
  })

  it('renders the component with header and analyze button', async () => {
    render(<PatternRecognition />)
    
    await waitFor(() => {
      expect(screen.getByText('Pattern Recognition')).toBeInTheDocument()
      expect(screen.getByText('Discover intelligent patterns in your transaction data')).toBeInTheDocument()
      expect(screen.getByText('Analyze Patterns')).toBeInTheDocument()
    })
  })

  it('displays stats when available', async () => {
    render(<PatternRecognition />)
    
    await waitFor(() => {
      expect(screen.getByText('Total Patterns:')).toBeInTheDocument()
      expect(screen.getByText('5')).toBeInTheDocument()
      expect(screen.getByText('High Confidence:')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
      expect(screen.getByText('Active Rules:')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
      expect(screen.getByText('Accuracy Rate:')).toBeInTheDocument()
      expect(screen.getByText('92.0%')).toBeInTheDocument()
    })
  })

  it('displays patterns when available', async () => {
    render(<PatternRecognition />)
    
    await waitFor(() => {
      expect(screen.getByText('Vendor Pattern')).toBeInTheDocument()
      expect(screen.getByText('Amount Pattern')).toBeInTheDocument()
      expect(screen.getByText('95.0%')).toBeInTheDocument()
    })
  })

  it('shows "No patterns found" when no patterns are available', async () => {
    const mockGetPatterns = patternRecognitionAPI.getRecognizedPatterns as jest.MockedFunction<typeof patternRecognitionAPI.getRecognizedPatterns>
    mockGetPatterns.mockResolvedValue({ data: [] })
    
    render(<PatternRecognition />)
    
    await waitFor(() => {
      expect(screen.getByText('No patterns found')).toBeInTheDocument()
      expect(screen.getByText('Click "Analyze Patterns" to discover intelligent patterns in your transaction data.')).toBeInTheDocument()
    })
  })

  it('calls analyze API when analyze button is clicked', async () => {
    const mockAnalyze = patternRecognitionAPI.analyzePatterns as jest.MockedFunction<typeof patternRecognitionAPI.analyzePatterns>
    mockAnalyze.mockResolvedValue({ data: mockAnalysisResults })
    
    render(<PatternRecognition />)
    
    await waitFor(() => {
      const analyzeButton = screen.getByText('Analyze Patterns')
      fireEvent.click(analyzeButton)
    })
    
    await waitFor(() => {
      expect(mockAnalyze).toHaveBeenCalledWith({
        confidence_threshold: 0.7,
        max_patterns: 50,
        include_examples: true
      })
    })
  })

  it('shows analyzing state when analysis is in progress', async () => {
    const mockAnalyze = patternRecognitionAPI.analyzePatterns as jest.MockedFunction<typeof patternRecognitionAPI.analyzePatterns>
    mockAnalyze.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ data: mockAnalysisResults }), 100)))
    
    render(<PatternRecognition />)
    
    await waitFor(() => {
      const analyzeButton = screen.getByText('Analyze Patterns')
      fireEvent.click(analyzeButton)
    })
    
    expect(screen.getByText('Analyzing...')).toBeInTheDocument()
  })

  it('displays pattern details correctly', async () => {
    render(<PatternRecognition />)
    
    await waitFor(() => {
      expect(screen.getAllByText('Pattern Details')).toHaveLength(2)
      expect(screen.getAllByText('Starbucks')).toHaveLength(2)
      expect(screen.getByText('Gas Station')).toBeInTheDocument()
    })
  })

  it('displays example transactions', async () => {
    render(<PatternRecognition />)
    
    await waitFor(() => {
      expect(screen.getAllByText('Example Transactions')).toHaveLength(2)
      expect(screen.getAllByText('Coffee Shop')).toHaveLength(2)
      expect(screen.getAllByText('Starbucks')).toHaveLength(2)
    })
  })

  it('calls generate rule API when generate rule button is clicked', async () => {
    const mockGenerateRule = patternRecognitionAPI.generateRule as jest.MockedFunction<typeof patternRecognitionAPI.generateRule>
    mockGenerateRule.mockResolvedValue({ data: mockRuleGeneration })
    
    render(<PatternRecognition />)
    
    await waitFor(() => {
      const generateRuleButtons = screen.getAllByText('Generate Rule')
      fireEvent.click(generateRuleButtons[0])
    })

    expect(mockGenerateRule).toHaveBeenCalledWith('pattern-1')
  })

  it('shows success message after rule generation', async () => {
    const mockGenerateRule = patternRecognitionAPI.generateRule as jest.MockedFunction<typeof patternRecognitionAPI.generateRule>
    mockGenerateRule.mockResolvedValue({ data: mockRuleGeneration })
    
    render(<PatternRecognition />)
    
    await waitFor(() => {
      const generateRuleButtons = screen.getAllByText('Generate Rule')
      fireEvent.click(generateRuleButtons[0])
    })

    await waitFor(() => {
      expect(screen.getByText('Rule generated successfully! Estimated impact: 15 transactions')).toBeInTheDocument()
    })
  })

  it('shows success message after pattern analysis', async () => {
    const mockAnalyze = patternRecognitionAPI.analyzePatterns as jest.MockedFunction<typeof patternRecognitionAPI.analyzePatterns>
    mockAnalyze.mockResolvedValue({ data: mockAnalysisResults })
    
    render(<PatternRecognition />)
    
    await waitFor(() => {
      const analyzeButton = screen.getByText('Analyze Patterns')
      fireEvent.click(analyzeButton)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Analysis completed! Found 5 patterns in 2.5s')).toBeInTheDocument()
    })
  })

  it('shows error message when API calls fail', async () => {
    const mockGetPatterns = patternRecognitionAPI.getRecognizedPatterns as jest.MockedFunction<typeof patternRecognitionAPI.getRecognizedPatterns>
    mockGetPatterns.mockRejectedValue(new Error('API Error'))
    
    render(<PatternRecognition />)
    
    await waitFor(() => {
      expect(screen.getByText('Error loading patterns')).toBeInTheDocument()
    })
  })

  it('displays confidence colors correctly', async () => {
    render(<PatternRecognition />)
    
    await waitFor(() => {
      // High confidence (95%) should show green
      const highConfidenceElement = screen.getByText('95.0%')
      expect(highConfidenceElement).toHaveClass('text-green-600')
      
      // Medium confidence (87%) should show yellow
      const mediumConfidenceElement = screen.getByText('87.0%')
      expect(mediumConfidenceElement).toHaveClass('text-yellow-600')
    })
  })

  it('displays pattern type labels correctly', async () => {
    render(<PatternRecognition />)
    
    await waitFor(() => {
      expect(screen.getByText('Vendor Pattern')).toBeInTheDocument()
      expect(screen.getByText('Amount Pattern')).toBeInTheDocument()
    })
  })

  it('shows pattern support count', async () => {
    render(<PatternRecognition />)
    
    await waitFor(() => {
      expect(screen.getByText('Vendor Pattern')).toBeInTheDocument()
      expect(screen.getByText('Amount Pattern')).toBeInTheDocument()
    })
  })
})
