'use client'

import { useState, useEffect, useMemo } from 'react'
import { Upload, BarChart3, DollarSign, TrendingUp, TrendingDown, FileText, Trash2, ChevronDown, ChevronRight, HelpCircle, Info, Lightbulb, Target, AlertCircle, Heart, Brain } from 'lucide-react'
import { TransactionTable } from '@/components/TransactionTable'
import { DESIGN_TOKENS, getBadgeColorClasses } from '@/lib/design-system'
import { TherapeuticUploadModal } from '@/components/TherapeuticUploadModal'
import { DashboardStats } from '@/components/DashboardStats'
import { ImportBatchManager } from '@/components/ImportBatchManager'
import { ErrorBoundary, ErrorFallback } from '@/components/ErrorBoundary'
import DrSigmundSpendAvatar from '@/components/DrSigmundSpendAvatar'
import EmotionalCheckIn from '@/components/EmotionalCheckIn'
import AdvancedAIExplanation from '@/components/AdvancedAIExplanation'
import { authAPI, transactionAPI, analyticsAPI } from '@/lib/api'

// Progressive Disclosure Section Component
interface ProgressiveSectionProps {
  title: string
  description?: string
  isExpanded: boolean
  onToggle: () => void
  children: React.ReactNode
  icon?: React.ReactNode
  helpText?: string
  badge?: string
  badgeColor?: 'success' | 'warning' | 'danger' | 'info'
}

function ProgressiveSection({ 
  title, 
  description, 
  isExpanded, 
  onToggle, 
  children, 
  icon,
  helpText,
  badge,
  badgeColor = 'info'
}: ProgressiveSectionProps) {
  const [showHelp, setShowHelp] = useState(false)

  // Use design system badge colors
  const getBadgeColorClass = (color: 'success' | 'warning' | 'danger' | 'info') => getBadgeColorClasses(color)

  return (
    <div className="card therapeutic-transition">
      <div 
        className="flex items-center justify-between cursor-pointer therapeutic-hover"
        onClick={onToggle}
      >
        <div className="flex items-center gap-3">
          {icon && <div className="text-gray-500">{icon}</div>}
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
                             {badge && (
                 <span className={`px-2 py-1 text-xs font-medium rounded-full ${getBadgeColorClass(badgeColor)}`}>
                   {badge}
                 </span>
               )}
            </div>
            {description && (
              <p className="text-sm text-gray-600 mt-1">{description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {helpText && (
            <div className="relative">
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setShowHelp(!showHelp)
                }}
                className="p-1 text-gray-400 hover:text-gray-600 therapeutic-transition"
                aria-label="Help"
              >
                <HelpCircle className="w-4 h-4" />
              </button>
              {showHelp && (
                <div className="absolute right-0 top-8 w-64 p-3 bg-blue-50 border border-blue-200 rounded-lg shadow-lg z-10">
                  <p className="text-sm text-blue-800">{helpText}</p>
                  <div className="absolute -top-1 right-3 w-2 h-2 bg-blue-50 border-l border-t border-blue-200 transform rotate-45"></div>
                </div>
              )}
            </div>
          )}
          {isExpanded ? (
            <ChevronDown className="w-5 h-5 text-gray-500" />
          ) : (
            <ChevronRight className="w-5 h-5 text-gray-500" />
          )}
        </div>
      </div>
      
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          {children}
        </div>
      )}
    </div>
  )
}

// Financial Wellness Card Component
interface WellnessCardProps {
  title: string
  value: string | number
  description: string
  icon: React.ReactNode
  color: 'success' | 'warning' | 'danger' | 'info'
  trend?: 'up' | 'down' | 'stable'
  trendValue?: string
}

function WellnessCard({ title, value, description, icon, color, trend, trendValue }: WellnessCardProps) {
  const colorClasses = {
    success: 'bg-success-50 border-success-200 text-success-800',
    warning: 'bg-warning-50 border-warning-200 text-warning-800',
    danger: 'bg-danger-50 border-danger-200 text-danger-800',
    info: 'bg-primary-50 border-primary-200 text-primary-800'
  }

  const iconColors = {
    success: 'text-success-600',
    warning: 'text-warning-600',
    danger: 'text-danger-600',
    info: 'text-primary-600'
  }

  return (
    <div className={`p-4 rounded-lg border ${colorClasses[color]} therapeutic-transition therapeutic-hover`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg bg-white/50 ${iconColors[color]}`}>
            {icon}
          </div>
          <div>
            <h4 className="font-medium text-gray-900">{title}</h4>
            <p className="text-sm text-gray-600">{description}</p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-900">{value}</div>
          {trend && trendValue && (
            <div className={`text-sm flex items-center gap-1 ${
              trend === 'up' ? 'text-success-600' : 
              trend === 'down' ? 'text-danger-600' : 'text-gray-600'
            }`}>
              {trend === 'up' && <TrendingUp className="w-3 h-3" />}
              {trend === 'down' && <TrendingDown className="w-3 h-3" />}
              {trendValue}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

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
  
  // Progressive disclosure state
  const [expandedSections, setExpandedSections] = useState({
    overview: true,
    wellness: false,
    actions: false,
    transactions: true,
    insights: false,
    emotional: false,
    aiExplanation: false
  })

  // Emotional check-in state
  const [userMood, setUserMood] = useState<any>(null)
  const [achievements, setAchievements] = useState<any[]>([])

  // AI Explanation state
  const [aiReasoning, setAiReasoning] = useState({
    id: 'demo_reasoning',
    category: 'Food & Dining',
    confidence: 87,
    reasoning: [
      'Transaction description contains "STARBUCKS" which is a known coffee chain',
      'Amount ($4.50) is typical for a coffee purchase',
      'Previous transactions with this vendor were categorized as Food & Dining',
      'Time of transaction (9:30 AM) is consistent with morning coffee purchases'
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
      }
    ],
    learningData: {
      userCorrections: 12,
      accuracy: 94.2,
      lastUpdated: new Date('2024-01-15')
    }
  })

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
      // Redirecting to login
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
      // Transactions fetched successfully
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
      // Summary fetched successfully
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
      // Demo login initiated
      const response = await authAPI.login('demo@fingood.com', 'demo123')
              // Login successful
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
    // Expand the transactions section to show new data
    setExpandedSections(prev => ({ ...prev, transactions: true }))
  }

  const handleCategorizeAll = async () => {
    setIsCategorizing(true)
    try {
      const response = await transactionAPI.categorize()
      // Categorization completed successfully
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

  const handleMoodSubmit = (moodData: any) => {
    setUserMood(moodData)
    // In a real app, this would be sent to the backend
    console.log('Mood submitted:', moodData)
  }

  // AI Explanation handlers
  const handleAIFeedback = (feedback: any) => {
    console.log('AI feedback received:', feedback)
    // In a real app, this would be sent to the backend for model training
    // For demo purposes, we'll simulate learning by adjusting confidence
    setAiReasoning(prev => ({
      ...prev,
      confidence: Math.min(100, prev.confidence + (feedback.type === 'correct' ? 1 : -2))
    }))
  }

  const handleAIConfidenceAdjust = (newConfidence: number) => {
    console.log('AI confidence adjusted to:', newConfidence)
    setAiReasoning(prev => ({
      ...prev,
      confidence: newConfidence
    }))
  }

  // Generate mock achievements based on user activity
  const generateAchievements = () => {
    const mockAchievements = []
    
    if (summary?.categorized_count && summary.categorized_count > 0) {
      mockAchievements.push({
        id: 'categorization',
        type: 'categorization' as const,
        title: 'Organized Finances',
        description: `You've categorized ${summary.categorized_count} transactions!`,
        timestamp: new Date(),
        value: summary.categorized_count
      })
    }
    
    if (wellnessMetrics?.savingsRate && wellnessMetrics.savingsRate > 20) {
      mockAchievements.push({
        id: 'savings',
        type: 'savings' as const,
        title: 'Savings Champion',
        description: `You're saving ${wellnessMetrics.savingsRate.toFixed(0)}% of your income!`,
        timestamp: new Date(),
        value: wellnessMetrics.savingsRate
      })
    }
    
    if (wellnessMetrics?.categorizationRate && wellnessMetrics.categorizationRate > 90) {
      mockAchievements.push({
        id: 'consistency',
        type: 'consistency' as const,
        title: 'Financial Organization Pro',
        description: 'You keep your finances well organized!',
        timestamp: new Date()
      })
    }
    
    return mockAchievements
  }

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

    // Use design system thresholds
  const WELLNESS_THRESHOLDS = DESIGN_TOKENS.WELLNESS_THRESHOLDS

  // Calculate financial wellness metrics with memoization
  const wellnessMetrics = useMemo(() => {
    if (!summary) return null

    const netIncome = summary.total_income - summary.total_expenses
    const categorizationRate = summary.total_transactions > 0
      ? (summary.categorized_count / summary.total_transactions) * 100
      : 0
    const expenseRatio = summary.total_income > 0
      ? (summary.total_expenses / summary.total_income) * 100
      : 0

    return {
      netIncome,
      categorizationRate,
      expenseRatio,
      savingsRate: Math.max(0, 100 - expenseRatio)
    }
  }, [summary])

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
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-8">
          <DrSigmundSpendAvatar 
            size="xl" 
            mood="encouraging"
            message="Welcome to Spend's Analysis! I'm here to help you understand your finances better."
            className="mb-6"
          />
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Welcome to Spend's Analysis</h1>
          <p className="text-gray-600 mb-8">Your AI-powered financial companion is ready to help you achieve financial wellness</p>
          <div className="space-y-4">
            <a 
              href="/login" 
              className="bg-brand-gradient text-white px-4 py-2 rounded-lg font-medium transition-all duration-300 shadow-sm hover:shadow-lg transform hover:scale-105 block w-full text-center"
            >
              Login
            </a>
            <button 
              onClick={handleDemoLogin}
              className="bg-white/80 backdrop-blur-sm text-gray-700 border border-gray-300 hover:border-brand-primary-light hover:text-brand-primary px-4 py-2 rounded-lg font-medium transition-all duration-300 shadow-sm hover:shadow-md transform hover:scale-105 block w-full text-center"
            >
              Try Demo (demo@fingood.com)
            </button>
          </div>
        </div>
      </div>
    )
  }

  // wellnessMetrics is now calculated with useMemo above

  // Show dashboard if authenticated
  return (
    <div className="min-h-screen bg-white">
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
                <h1 className="text-3xl font-bold text-gray-900">Spend's Analysis</h1>
                <p className="text-gray-600">AI-Powered Financial Intelligence</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  // Upload modal opened
                  setIsUploadModalOpen(true)
                }}
                className="bg-brand-gradient text-white px-4 py-2 rounded-lg font-medium transition-all duration-300 shadow-sm hover:shadow-lg transform hover:scale-105 flex items-center gap-2"
              >
                <Upload className="w-4 h-4" />
                Upload CSV
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Overview Section */}
        <ProgressiveSection
          title="Financial Overview"
          description="Your key financial metrics at a glance"
          isExpanded={expandedSections.overview}
          onToggle={() => toggleSection('overview')}
          icon={<BarChart3 className="w-5 h-5" />}
          helpText="This section shows your total income, expenses, and net income. Use these metrics to understand your overall financial health."
        >
          <ErrorBoundary fallback={ErrorFallback}>
            <DashboardStats summary={summary} isLoading={isLoadingSummary} />
          </ErrorBoundary>
        </ProgressiveSection>

        {/* Financial Wellness Section */}
        <ProgressiveSection
          title="Financial Wellness"
          description="AI-powered insights into your financial health"
          isExpanded={expandedSections.wellness}
          onToggle={() => toggleSection('wellness')}
          icon={<Target className="w-5 h-5" />}
          helpText="These wellness indicators help you understand your financial habits and suggest areas for improvement."
          badge={wellnessMetrics?.categorizationRate === 100 ? "Excellent" : "Good"}
          badgeColor={wellnessMetrics?.categorizationRate === 100 ? "success" : "warning"}
        >
          {wellnessMetrics && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <WellnessCard
                title="Net Income"
                value={`$${wellnessMetrics.netIncome.toLocaleString()}`}
                description="Income minus expenses"
                icon={<DollarSign className="w-5 h-5" />}
                color={wellnessMetrics.netIncome >= 0 ? "success" : "danger"}
                trend={wellnessMetrics.netIncome >= 0 ? "up" : "down"}
                trendValue={wellnessMetrics.netIncome >= 0 ? "Positive" : "Negative"}
              />
              <WellnessCard
                title="Categorization"
                value={`${wellnessMetrics.categorizationRate.toFixed(0)}%`}
                description="Transactions categorized"
                icon={<FileText className="w-5 h-5" />}
                                 color={wellnessMetrics.categorizationRate >= WELLNESS_THRESHOLDS.CATEGORIZATION_EXCELLENT ? "success" : wellnessMetrics.categorizationRate >= WELLNESS_THRESHOLDS.CATEGORIZATION_GOOD ? "warning" : "danger"}
                 trend={wellnessMetrics.categorizationRate >= WELLNESS_THRESHOLDS.CATEGORIZATION_EXCELLENT ? "up" : "stable"}
                 trendValue={wellnessMetrics.categorizationRate >= WELLNESS_THRESHOLDS.CATEGORIZATION_EXCELLENT ? "Excellent" : "Good"}
              />
              <WellnessCard
                title="Expense Ratio"
                value={`${wellnessMetrics.expenseRatio.toFixed(0)}%`}
                description="Expenses as % of income"
                icon={<TrendingDown className="w-5 h-5" />}
                                 color={wellnessMetrics.expenseRatio <= WELLNESS_THRESHOLDS.EXPENSE_RATIO_HEALTHY ? "success" : wellnessMetrics.expenseRatio <= WELLNESS_THRESHOLDS.EXPENSE_RATIO_WARNING ? "warning" : "danger"}
                 trend={wellnessMetrics.expenseRatio <= WELLNESS_THRESHOLDS.EXPENSE_RATIO_HEALTHY ? "up" : "down"}
                 trendValue={wellnessMetrics.expenseRatio <= WELLNESS_THRESHOLDS.EXPENSE_RATIO_HEALTHY ? "Healthy" : "High"}
              />
              <WellnessCard
                title="Savings Rate"
                value={`${wellnessMetrics.savingsRate.toFixed(0)}%`}
                description="Potential savings rate"
                icon={<TrendingUp className="w-5 h-5" />}
                                 color={wellnessMetrics.savingsRate >= WELLNESS_THRESHOLDS.SAVINGS_RATE_GREAT ? "success" : wellnessMetrics.savingsRate >= WELLNESS_THRESHOLDS.SAVINGS_RATE_GOOD ? "warning" : "danger"}
                 trend={wellnessMetrics.savingsRate >= WELLNESS_THRESHOLDS.SAVINGS_RATE_GREAT ? "up" : "stable"}
                 trendValue={wellnessMetrics.savingsRate >= WELLNESS_THRESHOLDS.SAVINGS_RATE_GREAT ? "Great" : "Good"}
              />
            </div>
          )}
        </ProgressiveSection>

        {/* Quick Actions Section */}
        <ProgressiveSection
          title="Quick Actions"
          description="Common tasks to manage your finances"
          isExpanded={expandedSections.actions}
          onToggle={() => toggleSection('actions')}
          icon={<Lightbulb className="w-5 h-5" />}
          helpText="Quick access to the most common financial management tasks. Upload new data, categorize transactions, or export your information."
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card therapeutic-hover therapeutic-transition cursor-pointer" onClick={() => setIsUploadModalOpen(true)}>
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

            <div className="card therapeutic-hover therapeutic-transition">
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

            <div className="card therapeutic-hover therapeutic-transition">
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
        </ProgressiveSection>

        {/* Transactions Section */}
        <ProgressiveSection
          title="Transaction Management"
          description="View and manage your financial transactions"
          isExpanded={expandedSections.transactions}
          onToggle={() => toggleSection('transactions')}
          icon={<FileText className="w-5 h-5" />}
          helpText="Manage your transactions, categorize them automatically, and export your data. Use the filters to find specific transactions."
                     badge={summary?.uncategorized_count && summary.uncategorized_count > 0 ? `${summary.uncategorized_count} uncategorized` : "All categorized"}
           badgeColor={summary?.uncategorized_count && summary.uncategorized_count > 0 ? "warning" : "success"}
        >
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
                    onClick={() => {/* Export functionality */}}
                    className="bg-white/80 backdrop-blur-sm text-gray-700 border border-gray-300 hover:border-brand-primary-light hover:text-brand-primary px-4 py-2 rounded-lg font-medium transition-all duration-300 shadow-sm hover:shadow-md transform hover:scale-105"
                  >
                    Export
                  </button>
                  <button 
                    onClick={handleCategorizeAll}
                    disabled={isCategorizing}
                    className="bg-brand-gradient text-white px-4 py-2 rounded-lg font-medium transition-all duration-300 shadow-sm hover:shadow-lg transform hover:scale-105 disabled:opacity-50"
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
        </ProgressiveSection>

        {/* AI Insights Section */}
        <ProgressiveSection
          title="AI Insights"
          description="Intelligent recommendations and patterns"
          isExpanded={expandedSections.insights}
          onToggle={() => toggleSection('insights')}
          icon={<Lightbulb className="w-5 h-5" />}
          helpText="AI-powered insights about your spending patterns, potential savings opportunities, and financial recommendations."
          badge="New"
          badgeColor="info"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Info className="w-5 h-5 text-blue-600" />
                </div>
                <h3 className="text-lg font-medium text-gray-900">Spending Patterns</h3>
              </div>
              <p className="text-gray-600 mb-4">
                Based on your transaction history, we've identified some interesting patterns in your spending habits.
              </p>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-2 h-2 bg-success-500 rounded-full"></div>
                  <span>Your largest expense category is typically groceries</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-2 h-2 bg-warning-500 rounded-full"></div>
                  <span>Consider reviewing subscription services monthly</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-2 h-2 bg-info-500 rounded-full"></div>
                  <span>You're on track for your savings goals</span>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Target className="w-5 h-5 text-green-600" />
                </div>
                <h3 className="text-lg font-medium text-gray-900">Recommendations</h3>
              </div>
              <p className="text-gray-600 mb-4">
                Here are some personalized recommendations to improve your financial health.
              </p>
              <div className="space-y-3">
                <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                  <h4 className="font-medium text-green-900 mb-1">Increase Savings</h4>
                  <p className="text-sm text-green-700">Consider setting up automatic transfers to your savings account.</p>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <h4 className="font-medium text-blue-900 mb-1">Review Subscriptions</h4>
                  <p className="text-sm text-blue-700">You have several recurring payments that could be optimized.</p>
                </div>
                <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                  <h4 className="font-medium text-purple-900 mb-1">Emergency Fund</h4>
                  <p className="text-sm text-purple-700">Great job maintaining your emergency fund! Keep it up.</p>
                </div>
              </div>
            </div>
          </div>
        </ProgressiveSection>

        {/* Emotional Check-in Section */}
        <ProgressiveSection
          title="Emotional Wellness"
          description="Track your financial mood and get personalized support"
          isExpanded={expandedSections.emotional}
          onToggle={() => toggleSection('emotional')}
          icon={<Heart className="w-5 h-5" />}
          helpText="Your emotional relationship with money matters. Regular check-ins help us provide better support and celebrate your achievements."
          badge={userMood ? "Checked In" : "Ready"}
          badgeColor={userMood ? "success" : "info"}
        >
          <ErrorBoundary fallback={ErrorFallback}>
            <EmotionalCheckIn
              onMoodSubmit={handleMoodSubmit}
              achievements={generateAchievements()}
              showNudges={true}
            />
          </ErrorBoundary>
        </ProgressiveSection>

        {/* AI Explanation Section */}
        <ProgressiveSection
          title="AI Explanation Interface"
          description="Understand how AI categorizes your transactions"
          isExpanded={expandedSections.aiExplanation}
          onToggle={() => toggleSection('aiExplanation')}
          icon={<Brain className="w-5 h-5" />}
          helpText="See the reasoning behind AI categorization decisions, provide feedback to improve accuracy, and understand the learning process."
          badge="Advanced"
          badgeColor="warning"
        >
          <ErrorBoundary fallback={ErrorFallback}>
            <AdvancedAIExplanation
              reasoning={aiReasoning}
              onFeedback={handleAIFeedback}
              onConfidenceAdjust={handleAIConfidenceAdjust}
              showLearning={true}
            />
          </ErrorBoundary>
        </ProgressiveSection>
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
