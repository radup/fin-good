'use client'

import { useState, useEffect } from 'react'
import { Upload, BarChart3, DollarSign, TrendingUp, FileText, Trash2 } from 'lucide-react'
import { TransactionTable } from '@/components/TransactionTable'
import { TherapeuticUploadModal } from '@/components/TherapeuticUploadModal'
import { DashboardStats } from '@/components/DashboardStats'
import { ImportBatchManager } from '@/components/ImportBatchManager'
import { ErrorBoundary, ErrorFallback } from '@/components/ErrorBoundary'
import DrSigmundSpendAvatar from '@/components/DrSigmundSpendAvatar'
import { authAPI, transactionAPI, analyticsAPI } from '@/lib/api'

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
    
    // Check authentication status using the /me endpoint
    checkAuthentication()
  }, [])

  const checkAuthentication = async () => {
    try {
      const response = await authAPI.me()
      setIsAuthenticated(true)
    } catch (error: any) {
      console.log('Not authenticated, redirecting to login')
      setIsAuthenticated(false)
      window.location.href = '/login'
    }
  }

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
      const response = await transactionAPI.getTransactions()
      console.log('Fetched transactions:', response.data)
      setTransactions(response.data)
    } catch (error: any) {
      console.error('Error fetching transactions:', error)
      if (error.response?.status === 401) {
        setIsAuthenticated(false)
        window.location.href = '/login'
      }
    } finally {
      setIsLoadingTransactions(false)
    }
  }

  const fetchSummary = async () => {
    setIsLoadingSummary(true)
    try {
      const response = await analyticsAPI.summary()
      console.log('Fetched summary:', response.data)
      setSummary(response.data)
    } catch (error: any) {
      console.error('Error fetching summary:', error)
      if (error.response?.status === 401) {
        setIsAuthenticated(false)
        window.location.href = '/login'
      }
    } finally {
      setIsLoadingSummary(false)
    }
  }

  const handleDemoLogin = async () => {
    try {
      console.log('Demo login clicked')
      const response = await authAPI.login('demo@fingood.com', 'demo123')
      console.log('Login successful:', response.data)
      setIsAuthenticated(true)
      // Refresh the page to load authenticated data
      window.location.reload()
    } catch (error) {
      console.error('Demo login failed:', error)
      alert('Demo login failed. Please check your connection and try again.')
    }
  }

  const handleLogout = async () => {
    try {
      await authAPI.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setIsAuthenticated(false)
      window.location.href = '/login'
    }
  }

  const handleUploadSuccess = () => {
    // Refresh data after successful upload
    fetchTransactions()
    fetchSummary()
    setRefreshKey(prevKey => prevKey + 1)
    // Ensure modal closes and table view is active so user sees updates
    setIsUploadModalOpen(false)
    setActiveView('transactions')
  }

  const handleCategorizeAll = async () => {
    setIsCategorizing(true)
    try {
      const response = await transactionAPI.categorize()
      console.log('Categorization result:', response.data)
      alert(`Successfully categorized ${response.data.categorized_count} transactions!`)
      
      // Refresh data after categorization
      await fetchTransactions()
      await fetchSummary()
    } catch (error: any) {
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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-8">
          <DrSigmundSpendAvatar 
            size="xl" 
            mood="encouraging"
            message="Welcome to FinGood! I'm here to help you understand your finances better."
            className="mb-6"
          />
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Welcome to FinGood</h1>
          <p className="text-gray-600 mb-8">Your AI-powered financial companion is ready to help you achieve financial wellness</p>
          <div className="space-y-4">
            <a 
              href="/login" 
              className="btn-primary block w-full"
            >
              Login
            </a>
            <button 
              onClick={handleDemoLogin}
              className="btn-secondary block w-full"
            >
              Try Demo (demo@fingood.com)
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Show dashboard if authenticated
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
                showMessage={false}
              />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">FinGood</h1>
                <p className="text-gray-600">AI-Powered Financial Intelligence</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  console.log('Upload CSV button clicked')
                  setIsUploadModalOpen(true)
                }}
                className="btn-primary flex items-center gap-2 therapeutic-hover"
              >
                <Upload className="w-4 h-4" />
                Upload CSV
              </button>
              <button
                onClick={handleLogout}
                className="btn-secondary therapeutic-hover"
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
                refreshKey={refreshKey}
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
      <TherapeuticUploadModal 
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />
    </div>
  )
}
