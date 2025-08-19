import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { DuplicateDetection } from '@/components/DuplicateDetection'
import { duplicateDetectionAPI } from '@/lib/api'

// Mock the API
jest.mock('@/lib/api', () => ({
  duplicateDetectionAPI: {
    getGroups: jest.fn(),
    getStats: jest.fn(),
    scan: jest.fn(),
    merge: jest.fn(),
    dismiss: jest.fn(),
  }
}))

// Mock the ErrorBoundary component
jest.mock('@/components/ErrorBoundary', () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}))

const mockDuplicateGroups = [
  {
    group_id: 'group-1',
    confidence_score: 0.95,
    algorithm_used: 'fuzzy_match',
    transactions: [
      {
        id: 1,
        description: 'Coffee Shop',
        amount: 5.50,
        date: '2024-01-01',
        vendor: 'Starbucks',
        category: 'Food',
        subcategory: 'Restaurants',
        similarity_score: 0.98
      },
      {
        id: 2,
        description: 'Coffee Shop',
        amount: 5.50,
        date: '2024-01-01',
        vendor: 'Starbucks',
        category: 'Food',
        subcategory: 'Restaurants',
        similarity_score: 0.95
      }
    ],
    merge_suggestions: [
      {
        primary_transaction_id: 1,
        fields_to_merge: ['description', 'amount', 'vendor'],
        confidence: 0.95
      }
    ],
    created_at: '2024-01-01T10:00:00Z'
  }
]

const mockStats = {
  total_groups: 5,
  total_duplicates: 12,
  merged_count: 3,
  dismissed_count: 1
}

const mockScanResults = {
  message: 'Scan completed',
  scan_id: 'scan-123',
  total_transactions_scanned: 1000,
  duplicate_groups_found: 5,
  total_duplicates: 12,
  scan_duration: 2.5,
  algorithms_used: ['fuzzy_match', 'exact_match'],
  confidence_threshold: 0.8
}

describe('DuplicateDetection', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Default mock implementations
    const mockGetGroups = duplicateDetectionAPI.getGroups as jest.MockedFunction<typeof duplicateDetectionAPI.getGroups>
    const mockGetStats = duplicateDetectionAPI.getStats as jest.MockedFunction<typeof duplicateDetectionAPI.getStats>
    
    mockGetGroups.mockResolvedValue({ data: mockDuplicateGroups })
    mockGetStats.mockResolvedValue({ data: mockStats })
  })

  it('renders the component with header and scan button', () => {
    render(<DuplicateDetection />)
    
    expect(screen.getByText('Duplicate Detection')).toBeInTheDocument()
    expect(screen.getByText('Find and manage duplicate transactions in your data')).toBeInTheDocument()
    expect(screen.getByText('Scan for Duplicates')).toBeInTheDocument()
  })

  it('displays stats when available', async () => {
    render(<DuplicateDetection />)
    
    await waitFor(() => {
      expect(screen.getByText('Total Groups:')).toBeInTheDocument()
      expect(screen.getByText('5')).toBeInTheDocument()
      expect(screen.getByText('Total Duplicates:')).toBeInTheDocument()
      expect(screen.getByText('12')).toBeInTheDocument()
    })
  })

  it('displays duplicate groups when available', async () => {
    render(<DuplicateDetection />)
    
    await waitFor(() => {
      expect(screen.getByText('Duplicate Group (2 transactions)')).toBeInTheDocument()
    })
  })

  it('shows "No duplicates found" when no groups are available', async () => {
    const mockGetGroups = duplicateDetectionAPI.getGroups as jest.MockedFunction<typeof duplicateDetectionAPI.getGroups>
    mockGetGroups.mockResolvedValue({ data: [] })
    
    render(<DuplicateDetection />)
    
    await waitFor(() => {
      expect(screen.getByText('No duplicates found')).toBeInTheDocument()
      expect(screen.getByText('Click "Scan for Duplicates" to find potential duplicates in your data.')).toBeInTheDocument()
    })
  })

  it('calls scan API when scan button is clicked', async () => {
    const mockScan = duplicateDetectionAPI.scan as jest.MockedFunction<typeof duplicateDetectionAPI.scan>
    mockScan.mockResolvedValue({ data: mockScanResults })
    
    render(<DuplicateDetection />)
    
    const scanButton = screen.getByText('Scan for Duplicates')
    fireEvent.click(scanButton)
    
    await waitFor(() => {
      expect(mockScan).toHaveBeenCalledWith({
        confidence_threshold: 0.8,
        max_results: 100
      })
    })
  })

  it('shows scanning state when scan is in progress', async () => {
    const mockScan = duplicateDetectionAPI.scan as jest.MockedFunction<typeof duplicateDetectionAPI.scan>
    mockScan.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ data: mockScanResults }), 100)))
    
    render(<DuplicateDetection />)
    
    const scanButton = screen.getByText('Scan for Duplicates')
    fireEvent.click(scanButton)
    
    expect(screen.getByText('Scanning...')).toBeInTheDocument()
  })

  it('shows group details when expanded', async () => {
    render(<DuplicateDetection />)
    
    await waitFor(() => {
      expect(screen.getAllByText('Coffee Shop')).toHaveLength(2)
      expect(screen.getAllByText('$5.50')).toHaveLength(2)
      expect(screen.getByText('Merge Suggestions')).toBeInTheDocument()
    })
  })

  it('calls merge API when merge button is clicked', async () => {
    const mockMerge = duplicateDetectionAPI.merge as jest.MockedFunction<typeof duplicateDetectionAPI.merge>
    mockMerge.mockResolvedValue({
      data: {
        message: 'Success',
        merge_id: 'merge-123',
        primary_transaction_id: 1,
        merged_transaction_ids: [2],
        merged_fields: ['description', 'amount', 'vendor'],
        new_transaction: {
          id: 1,
          description: 'Coffee Shop',
          amount: 5.50,
          date: '2024-01-01',
          vendor: 'Starbucks',
          category: 'Food',
          subcategory: 'Restaurants'
        }
      }
    })
    
    render(<DuplicateDetection />)
    
    await waitFor(() => {
      const mergeButton = screen.getByText('Merge')
      fireEvent.click(mergeButton)
      
      expect(mockMerge).toHaveBeenCalledWith('group-1', 1, ['description', 'amount', 'vendor'])
    })
  })

  it('calls dismiss API when dismiss button is clicked', async () => {
    const mockDismiss = duplicateDetectionAPI.dismiss as jest.MockedFunction<typeof duplicateDetectionAPI.dismiss>
    mockDismiss.mockResolvedValue({ data: { message: 'Success' } })
    
    render(<DuplicateDetection />)
    
    await waitFor(() => {
      const dismissButton = screen.getByText('Dismiss')
      fireEvent.click(dismissButton)
      
      expect(mockDismiss).toHaveBeenCalledWith('group-1', 'False positive')
    })
  })

  it('shows error message when API calls fail', async () => {
    const mockGetGroups = duplicateDetectionAPI.getGroups as jest.MockedFunction<typeof duplicateDetectionAPI.getGroups>
    mockGetGroups.mockRejectedValue(new Error('API Error'))
    
    render(<DuplicateDetection />)
    
    await waitFor(() => {
      expect(screen.getByText('Error loading duplicate groups')).toBeInTheDocument()
    })
  })

  it('displays confidence colors correctly', async () => {
    render(<DuplicateDetection />)
    
    await waitFor(() => {
      // High confidence (95%) should show green
      expect(screen.getByText('95.0%')).toHaveClass('text-green-600')
    })
  })
})
