'use client'

import { useState, useEffect } from 'react'
import { Upload, BarChart3, DollarSign, TrendingUp, FileText, Trash2 } from 'lucide-react'
import { TransactionTable } from '@/components/TransactionTable'
import { UploadModal } from '@/components/UploadModal'
import { DashboardStats } from '@/components/DashboardStats'
import { ImportBatchManager } from '@/components/ImportBatchManager'
import { ErrorBoundary, ErrorFallback } from '@/components/ErrorBoundary'

export default function DashboardComponent() {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [isCategorizing, setIsCategorizing] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [transactions, setTransactions] = useState([])
  const [summary, setSummary] = useState<{
    total_transactions: number
    total_income: number
    total_expenses: number
    categorized_count: number
    uncategorized_count: number
  } | undefined>(undefined)
  const [isLoadingTransactions, setIsLoadingTransactions] = useState(false)
  const [isLoadingSummary, setIsLoadingSummary] = useState(false)
  const [activeView, setActiveView] = useState<'transactions' | 'files'>('transactions')
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    // Mark component as mounted
    setMounted(true)
    
    // Check authentication status
    const token = localStorage.getItem('access_token')
    setIsAuthenticated(!!token)
  }, [])

  // Fetch data when authenticated
  useEffect(() => {
    if (isAuthenticated && mounted) {
      fetchTransactions()
      fetchSummary()
    }
  }, [isAuthenticated, mounted])

  const fetchTransactions = async () => {
    setIsLoadingTransactions(true)
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch('http://localhost:8000/api/v1/transactions/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch transactions')
      }
      
      const data = await response.json()
      console.log('Fetched transactions:', data)
      setTransactions(data)
    } catch (error) {
      console.error('Error fetching transactions:', error)
    } finally {
      setIsLoadingTransactions(false)
    }
  }

  const fetchSummary = async () => {
    setIsLoadingSummary(true)
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch('http://localhost:8000/api/v1/analytics/summary', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch summary')
      }
      
      const data = await response.json()
      console.log('Fetched summary:', data)
      setSummary(data)
    } catch (error) {
      console.error('Error fetching summary:', error)
    } finally {
      setIsLoadingSummary(false)
    }
  }

  const handleDemoLogin = async () => {
    try {
      console.log('Demo login clicked')
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: 'demo@fingood.com',
          password: 'demo123',
        }),
      })
      
      if (!response.ok) {
        throw new Error('Login failed')
      }
      
      const data = await response.json()
      console.log('Login successful:', data)
      localStorage.setItem('access_token', data.access_token)
      setIsAuthenticated(true)
      window.location.reload()
    } catch (error) {
      console.error('Demo login failed:', error)
      alert('Demo login failed. Please check your connection and try again.')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    setIsAuthenticated(false)
    window.location.reload()
  }

  const handleUploadSuccess = () => {
    // Refresh data after successful upload
    fetchTransactions()
    fetchSummary()
    setRefreshKey(prevKey => prevKey + 1)
  }

  const handleCategorizeAll = async () => {
    setIsCategorizing(true)
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch('http://localhost:8000/api/v1/transactions/categorize', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('Categorization failed')
      }
      
      const data = await response.json()
      console.log('Categorization result:', data)
      alert(`Successfully categorized ${data.categorized_count} transactions!`)
      
      // Refresh data after categorization
      await fetchTransactions()
      await fetchSummary()
    } catch (error) {
      console.error('Categorization failed:', error)
      alert('Failed to categorize transactions. Please try again.')
    } finally {
      setIsCategorizing(false)
    }
  }

  // Show loading state until component is mounted
  if (!mounted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Welcome to FinGood</h1>
          <p className="text-gray-600 mb-6">Please log in to access your financial dashboard</p>
          <div className="space-y-3">
            <a 
              href="/login" 
              className="btn-primary block"
            >
              Login
            </a>
            <button 
              onClick={handleDemoLogin}
              className="btn-secondary block"
            >
              Demo Login (demo@fingood.com)
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Show dashboard if authenticated
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">FinGood</h1>
              <p className="text-gray-600">AI-Powered Financial Intelligence</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  console.log('Upload CSV button clicked')
                  setIsUploadModalOpen(true)
                }}
                className="btn-primary flex items-center gap-2"
              >
                <Upload className="w-4 h-4" />
                Upload CSV
              </button>
              <button
                onClick={handleLogout}
                className="btn-secondary"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <ErrorBoundary fallback={ErrorFallback}>
          <DashboardStats summary={summary} isLoading={isLoadingSummary} />
        </ErrorBoundary>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="card">
            <div className="flex items-center">
              <div className="p-2 bg-primary-100 rounded-lg">
                <Upload className="w-6 h-6 text-primary-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">Upload Data</h3>
                <p className="text-gray-600">Import transactions from CSV</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="p-2 bg-success-100 rounded-lg">
                <BarChart3 className="w-6 h-6 text-success-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">View Analytics</h3>
                <p className="text-gray-600">See spending patterns</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="p-2 bg-warning-100 rounded-lg">
                <TrendingUp className="w-6 h-6 text-warning-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">Forecast</h3>
                <p className="text-gray-600">Predict cash flow</p>
              </div>
            </div>
          </div>
        </div>

        {/* View Toggle */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
            <button
              onClick={() => setActiveView('transactions')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                activeView === 'transactions'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <div className="flex items-center">
                <BarChart3 className="w-4 h-4 mr-2" />
                Transactions
              </div>
            </button>
            <button
              onClick={() => setActiveView('files')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                activeView === 'files'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <div className="flex items-center">
                <FileText className="w-4 h-4 mr-2" />
                Import Files
              </div>
            </button>
          </div>
        </div>

        {/* Content based on active view */}
        {activeView === 'transactions' ? (
          /* Transactions Table */
          <div className="card">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Recent Transactions</h2>
              <div className="flex gap-2">
                <button 
                  onClick={() => console.log('Export button clicked')}
                  className="btn-secondary"
                >
                  Export
                </button>
                <button 
                  onClick={handleCategorizeAll}
                  disabled={isCategorizing}
                  className="btn-primary"
                >
                  {isCategorizing ? 'Categorizing...' : 'Categorize All'}
                </button>
              </div>
            </div>
            
            <ErrorBoundary fallback={ErrorFallback}>
              <TransactionTable 
                transactions={transactions} 
                isLoading={isLoadingTransactions} 
              />
            </ErrorBoundary>
          </div>
        ) : (
          /* Import Files Manager */
          <ErrorBoundary fallback={ErrorFallback}>
            <ImportBatchManager refreshKey={refreshKey} />
          </ErrorBoundary>
        )}
      </main>

      {/* Upload Modal */}
      <UploadModal 
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />
    </div>
  )
}
