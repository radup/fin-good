'use client'

import { useState } from 'react'
import { 
  MessageCircle, 
  History, 
  FileText, 
  BarChart3, 
  TrendingUp, 
  Target, 
  Upload,
  GitBranch,
  Receipt,
  Settings,
  Menu,
  X,
  Plus,
  Brain,
  Heart,
  ChevronDown,
  Send,
  User,
  Bot,
  Home,
  ChevronRight,
  LogOut
} from 'lucide-react'
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar'
import EnhancedDrSigmundChat from './EnhancedDrSigmundChat'
import CabinetNavigation from './CabinetNavigation'
import CabinetHeader from './CabinetHeader'
import TaxOptimizationDashboard from './TaxOptimizationDashboard'
import CashFlowForecastingDashboard from './CashFlowForecastingDashboard'
import ScenarioSimulationEngine from './ScenarioSimulationEngine'
import InvoiceRiskDashboard from './InvoiceRiskDashboard'
import EnhancedAnalyticsDashboard from './EnhancedAnalyticsDashboard'
import ClientPaymentPredictionDashboard from './ClientPaymentPredictionDashboard'
import { UploadModal } from './UploadModal'
import { ImportBatchManager } from './ImportBatchManager'
import CategorizationPerformance from './CategorizationPerformance'
import AutoImprovement from './AutoImprovement'
import SuggestionDisplay from './SuggestionDisplay'
import DashboardComponent from '@/app/DashboardComponent'
import { ExportManager } from '@/components/ExportManager'
import UserProfile from './UserProfile'

export default function CabinetLayout() {
  const [activeSection, setActiveSection] = useState('dashboard')

  const handleLogout = async () => {
    try {
      const { authAPI } = await import('../lib/api')
      await authAPI.logout()
      window.location.href = '/'
    } catch (error) {
      console.error('Logout failed:', error)
      window.location.href = '/'
    }
  }

  return (
    <div className="h-screen bg-white flex flex-col">
      {/* Full-width Header Bar */}
      <header className="flex items-center h-16 bg-brand-primary-dark border-b border-brand-primary shadow-lg">
        {/* Logo */}
        <div className="flex items-center px-4">
          <div className="w-8 h-8 bg-gradient-to-br from-teal-600 to-cyan-600 rounded-lg flex items-center justify-center shadow-lg">
            <span className="text-white font-bold text-sm">FG</span>
          </div>
          <div className="ml-3">
            <h1 className="text-lg font-semibold text-white">Spend's Analysis</h1>
          </div>
        </div>

        {/* Breadcrumb */}
        <div className="flex-1 px-4">
          <nav className="flex" aria-label="Breadcrumb">
            <ol className="flex items-center space-x-2 text-sm">
              <li>
                <a href="/" className="text-gray-300 hover:text-white transition-colors">
                  <Home className="w-4 h-4" />
                </a>
              </li>
              <ChevronRight className="w-4 h-4 text-gray-400" />
              <li className="text-white font-medium">Cabinet</li>
            </ol>
          </nav>
        </div>

        {/* User Profile */}
        <div className="flex items-center px-4">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-gray-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-white">Demo User</p>
              <p className="text-xs text-gray-300">demo@fingood.com</p>
            </div>
            <button
              onClick={handleLogout}
              className="ml-4 p-2 rounded-md text-gray-300 hover:text-white hover:bg-gray-800 transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Layout: Navigation + Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Navigation Sidebar */}
        <div className="w-64 flex-shrink-0">
          <CabinetNavigation 
            activeSection={activeSection}
            onSectionChange={setActiveSection}
          />
        </div>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto">
          {/* Main Content Interface */}
          <div className="p-6">
            {activeSection === 'dashboard' ? (
              <div className="space-y-6">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    Overview of your financial data and insights
                  </p>
                </div>
                <DashboardComponent />
                <div className="mt-8">
                  <ExportManager />
                </div>
              </div>
            ) : activeSection === 'new-session' ? (
              <div className="h-full flex flex-col space-y-6">
                {/* Enhanced Header Section */}
                <div className="bg-gradient-to-r from-brand-primary-lightest to-brand-primary-lighter rounded-2xl p-6 border border-brand-primary-light shadow-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <h1 className="text-3xl font-bold text-gray-900">New Session</h1>
                      <p className="mt-2 text-lg text-gray-600">
                        Start a new therapy session with Dr. Sigmund Spend
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-500">Session #6</div>
                      <div className="text-xs text-gray-400">January 21, 2025</div>
                    </div>
                  </div>
                </div>

                {/* Pre-Session Quick Check */}
                <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 p-4">
                  <h3 className="text-sm font-medium text-gray-900 mb-3">Before We Begin</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                      <span className="text-gray-600">Financial data synced</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                      <span className="text-gray-600">AI tools ready</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                      <span className="text-gray-600">Safe space established</span>
                    </div>
                  </div>
                </div>

                {/* Session Focus Quick Selector */}
                <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 p-4">
                  <h3 className="text-sm font-medium text-gray-900 mb-3">What would you like to focus on today?</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    <button className="px-3 py-2 text-xs bg-brand-gradient text-white rounded-lg border border-transparent transition-all duration-300 shadow-sm hover:shadow-lg transform hover:scale-105">
                      Cash Flow
                    </button>
                    <button className="px-3 py-2 text-xs bg-brand-gradient text-white rounded-lg border border-transparent transition-all duration-300 shadow-sm hover:shadow-lg transform hover:scale-105">
                      Tax Planning
                    </button>
                    <button className="px-3 py-2 text-xs bg-brand-gradient text-white rounded-lg border border-transparent transition-all duration-300 shadow-sm hover:shadow-lg transform hover:scale-105">
                      Investment Anxiety
                    </button>
                    <button className="px-3 py-2 text-xs bg-brand-gradient text-white rounded-lg border border-transparent transition-all duration-300 shadow-sm hover:shadow-lg transform hover:scale-105">
                      General Discussion
                    </button>
                  </div>
                </div>

                {/* Chat Interface */}
                <div className="flex-1 min-h-0">
                  <EnhancedDrSigmundChat />
                </div>
              </div>
            ) : activeSection === 'sessions-history' ? (
              <div className="space-y-6">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Sessions History</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    View your past therapy sessions
                  </p>
                </div>
                <div className="space-y-4">
                  {/* Recent Session */}
                  <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-medium text-gray-900">Cash Flow Anxiety Discussion</h3>
                        <p className="mt-1 text-sm text-gray-600">Explored Q1 cash flow forecasting and payment delays</p>
                        <div className="mt-3 flex items-center space-x-4 text-sm text-gray-500">
                          <span>January 18, 2025</span>
                          <span>•</span>
                          <span>45 minutes</span>
                          <span>•</span>
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                            Completed
                          </span>
                        </div>
                        <div className="mt-2 text-xs text-gray-600">
                          Tools used: Cash Flow Forecast, Client Payment Prediction
                        </div>
                      </div>
                      <button className="bg-brand-gradient text-white px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 shadow-sm hover:shadow-lg transform hover:scale-105">
                        View Details
                      </button>
                    </div>
                  </div>

                  {/* Previous Session */}
                  <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-medium text-gray-900">Tax Optimization Strategy</h3>
                        <p className="mt-1 text-sm text-gray-600">Discussed Belgian tax structure and business expense optimization</p>
                        <div className="mt-3 flex items-center space-x-4 text-sm text-gray-500">
                          <span>January 15, 2025</span>
                          <span>•</span>
                          <span>38 minutes</span>
                          <span>•</span>
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                            Completed
                          </span>
                        </div>
                        <div className="mt-2 text-xs text-gray-600">
                          Tools used: Tax Optimization, Scenario Analysis
                        </div>
                      </div>
                      <button className="bg-brand-gradient text-white px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 shadow-sm hover:shadow-lg transform hover:scale-105">
                        View Details
                      </button>
                    </div>
                  </div>

                  {/* Older Session */}
                  <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-medium text-gray-900">Investment Anxiety & Surplus Planning</h3>
                        <p className="mt-1 text-sm text-gray-600">Addressed concerns about investing business surplus and emergency fund sizing</p>
                        <div className="mt-3 flex items-center space-x-4 text-sm text-gray-500">
                          <span>January 10, 2025</span>
                          <span>•</span>
                          <span>52 minutes</span>
                          <span>•</span>
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                            Completed
                          </span>
                        </div>
                        <div className="mt-2 text-xs text-gray-600">
                          Tools used: Investment Analysis, Budget Analysis
                        </div>
                      </div>
                      <button className="bg-brand-gradient text-white px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 shadow-sm hover:shadow-lg transform hover:scale-105">
                        View Details
                      </button>
                    </div>
                  </div>

                  {/* Earlier Session */}
                  <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-medium text-gray-900">Rate Increase Decision Support</h3>
                        <p className="mt-1 text-sm text-gray-600">Explored scenarios for raising hourly rate from €75 to €95</p>
                        <div className="mt-3 flex items-center space-x-4 text-sm text-gray-500">
                          <span>January 5, 2025</span>
                          <span>•</span>
                          <span>41 minutes</span>
                          <span>•</span>
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                            Completed
                          </span>
                        </div>
                        <div className="mt-2 text-xs text-gray-600">
                          Tools used: Scenario Analysis, Client Payment Prediction
                        </div>
                      </div>
                      <button className="text-brand-secondary hover:text-brand-secondary-hover text-sm font-medium transition-colors">
                        View Details
                      </button>
                    </div>
                  </div>

                  {/* First Session */}
                  <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-medium text-gray-900">Initial Financial Health Assessment</h3>
                        <p className="mt-1 text-sm text-gray-600">First consultation to understand financial situation and money relationship</p>
                        <div className="mt-3 flex items-center space-x-4 text-sm text-gray-500">
                          <span>December 28, 2024</span>
                          <span>•</span>
                          <span>37 minutes</span>
                          <span>•</span>
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                            Completed
                          </span>
                        </div>
                        <div className="mt-2 text-xs text-gray-600">
                          Tools used: Budget Analysis, Cash Flow Forecast
                        </div>
                      </div>
                      <button className="text-brand-secondary hover:text-brand-secondary-hover text-sm font-medium transition-colors">
                        View Details
                      </button>
                    </div>
                  </div>

                  {/* Load More */}
                  <div className="text-center pt-4">
                    <button className="text-brand-secondary hover:text-brand-secondary-hover text-sm font-medium transition-colors">
                      Load Earlier Sessions
                    </button>
                  </div>
                </div>
              </div>
            ) : activeSection === 'scenario-engine' ? (
              <div className="space-y-6">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Scenario Engine</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    What-if financial simulations and modeling
                  </p>
                </div>
                <ScenarioSimulationEngine />
              </div>
            ) : activeSection === 'payment-prediction' ? (
              <div className="space-y-6">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Payment Prediction</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    Predict client payments and cash flow
                  </p>
                </div>
                <ClientPaymentPredictionDashboard />
              </div>
            ) : activeSection === 'tax-optimization' ? (
              <div className="space-y-6">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Tax Optimization</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    Multi-jurisdiction tax planning and optimization
                  </p>
                </div>
                <TaxOptimizationDashboard />
              </div>
            ) : activeSection === 'cash-flow-forecast' ? (
              <div className="space-y-6">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Cash Flow Forecast</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    Financial forecasting and predictions
                  </p>
                </div>
                <CashFlowForecastingDashboard />
              </div>
            ) : activeSection === 'budget-analysis' ? (
              <div className="space-y-6">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Budget Analysis</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    Budget planning and analysis tools
                  </p>
                </div>
                <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 p-6">
                  <p className="text-gray-600">Budget analysis tools will be displayed here.</p>
                </div>
              </div>
            ) : activeSection === 'invoice-risk' ? (
              <div className="space-y-6">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Invoice & Risk</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    Invoice analysis and risk assessment
                  </p>
                </div>
                <InvoiceRiskDashboard />
              </div>
            ) : activeSection === 'transactions' ? (
              <div className="space-y-6">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Transactions</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    Manage and view your financial transactions
                  </p>
                </div>
                <TransactionsSection />
              </div>
            ) : activeSection === 'categorization' ? (
              <div className="space-y-6">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Categorisation</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    AI-powered categorization tools
                  </p>
                </div>
                <CategorizationSection />
              </div>
            ) : activeSection === 'data-import' ? (
              <div className="space-y-6">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Data Import</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    Import and manage your financial data
                  </p>
                </div>
                <UploadSection />
              </div>
            ) : activeSection === 'analytics' ? (
              <div className="space-y-6">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    Advanced analytics and insights
                  </p>
                </div>
                <EnhancedAnalyticsDashboard />
              </div>
            ) : activeSection === 'emotional-checkin' ? (
              <div className="space-y-6">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Emotional Check-In</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    Track your financial emotions and wellness
                  </p>
                </div>
                <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 p-6">
                  <p className="text-gray-600">Emotional check-in tools will be displayed here.</p>
                </div>
              </div>
            ) : activeSection === 'insights' ? (
              <div className="space-y-6">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Insights</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    Personalized financial insights
                  </p>
                </div>
                <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 p-6">
                  <p className="text-gray-600">Personalized insights will be displayed here.</p>
                </div>
              </div>
            ) : activeSection === 'goal-settings' ? (
              <div className="space-y-6">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Goal Settings</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    Set and track your financial goals
                  </p>
                </div>
                <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 p-6">
                  <p className="text-gray-600">Goal setting tools will be displayed here.</p>
                </div>
              </div>
            ) : activeSection === 'settings' ? (
              <div className="space-y-6">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    Manage your preferences and account
                  </p>
                </div>
                <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 p-6">
                  <p className="text-gray-600">Settings will be displayed here.</p>
                </div>
              </div>
            ) : activeSection === 'user-profile' ? (
              <UserProfile />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                                  <div className="w-16 h-16 bg-brand-primary-lightest rounded-full flex items-center justify-center mx-auto mb-4">
                  <Brain className="h-8 w-8 text-brand-primary" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Welcome to Cabinet</h3>
                  <p className="text-gray-600">Select a section from the navigation to get started.</p>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

// Categorization Section Component
function CategorizationSection() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Categorization</h1>
        <p className="mt-1 text-sm text-gray-500">
          AI-powered categorization tools and performance insights
        </p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Performance Dashboard */}
        <div>
          <CategorizationPerformance />
        </div>
        
        {/* Auto-Improvement */}
        <div>
          <AutoImprovement />
        </div>
      </div>
      
      {/* Category Suggestions Demo */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Category Suggestions</h2>
        <SuggestionDisplay
          transactionId={1}
          currentCategory="Food & Dining"
          currentSubcategory="Restaurants"
          onSuggestionApplied={(category, subcategory) => {
            console.log('Suggestion applied:', category, subcategory)
          }}
        />
      </div>
    </div>
  )
}

// Transactions Section Component
function TransactionsSection() {
  // Mock data for transactions - in a real app this would come from an API
  const mockTransactions = [
    {
      id: 1,
      date: '2025-01-15',
      description: 'Client Payment - Web Development',
      amount: 2500,
      vendor: 'Tech Solutions Inc.',
      category: 'Income',
      subcategory: 'Consulting',
      is_income: true,
      is_categorized: true,
      confidence_score: 0.95
    },
    {
      id: 2,
      date: '2025-01-14',
      description: 'Office Supplies',
      amount: -45.80,
      vendor: 'OfficeMax',
      category: 'Business Expenses',
      subcategory: 'Office Supplies',
      is_income: false,
      is_categorized: true,
      confidence_score: 0.88
    },
    {
      id: 3,
      date: '2025-01-13',
      description: 'Monthly Software Subscription',
      amount: -29.99,
      vendor: 'Adobe',
      category: 'Business Expenses',
      subcategory: 'Software',
      is_income: false,
      is_categorized: true,
      confidence_score: 0.92
    },
    {
      id: 4,
      date: '2025-01-12',
      description: 'Freelance Design Work',
      amount: 1800,
      vendor: 'Creative Agency',
      category: 'Income',
      subcategory: 'Freelance',
      is_income: true,
      is_categorized: true,
      confidence_score: 0.97
    },
    {
      id: 5,
      date: '2025-01-11',
      description: 'Coffee Shop Meeting',
      amount: -12.50,
      vendor: 'Starbucks',
      category: 'Business Expenses',
      subcategory: 'Meals & Entertainment',
      is_income: false,
      is_categorized: true,
      confidence_score: 0.85
    }
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Transactions</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage and categorize your financial transactions
        </p>
      </div>
      
      {/* Simple Transaction Table for Cabinet */}
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Recent Transactions</h2>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <span>Total: {mockTransactions.length} transactions</span>
            </div>
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Vendor
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {mockTransactions.map((transaction) => (
                <tr key={transaction.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(transaction.date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <div className="max-w-xs truncate" title={transaction.description}>
                      {transaction.description}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {transaction.vendor || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div>
                      <div className="font-medium">{transaction.category}</div>
                      {transaction.subcategory && (
                        <div className="text-xs text-gray-500">{transaction.subcategory}</div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                    <span className={`font-medium ${transaction.is_income ? 'text-green-600' : 'text-red-600'}`}>
                      {transaction.is_income ? '+' : ''}€{Math.abs(transaction.amount).toFixed(2)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <div className="flex items-center justify-center space-x-2">
                      {transaction.is_categorized ? (
                        <div className="flex items-center space-x-1">
                          <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                          <span className="text-xs text-green-600">Categorized</span>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-1">
                          <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                          <span className="text-xs text-yellow-600">Pending</span>
                        </div>
                      )}
                      {transaction.confidence_score && (
                        <div className="text-xs text-gray-500">
                          {Math.round(transaction.confidence_score * 100)}%
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              <span className="font-medium">Income:</span> €{mockTransactions.filter(t => t.is_income).reduce((sum, t) => sum + t.amount, 0).toFixed(2)}
            </div>
            <div>
              <span className="font-medium">Expenses:</span> €{Math.abs(mockTransactions.filter(t => !t.is_income).reduce((sum, t) => sum + t.amount, 0)).toFixed(2)}
            </div>
            <div>
              <span className="font-medium">Net:</span> €{mockTransactions.reduce((sum, t) => sum + t.amount, 0).toFixed(2)}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Upload Section Component
function UploadSection() {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)

  return (
    <div className="space-y-6">
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upload Modal */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload New File</h2>
          <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
            <div className="text-center">
                              <div className="w-16 h-16 bg-brand-primary-lightest rounded-full flex items-center justify-center mx-auto mb-4">
                  <Upload className="h-8 w-8 text-brand-primary" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Upload CSV File</h3>
              <p className="text-gray-600 mb-6">
                Import your financial transactions from a CSV file for AI-powered categorization and analysis.
              </p>
              <button
                onClick={() => setIsUploadModalOpen(true)}
                className="px-6 py-3 bg-gradient-to-r from-brand-secondary to-brand-secondary-hover text-white rounded-lg hover:shadow-lg transform hover:scale-105 transition-all duration-200"
              >
                Choose File
              </button>
            </div>
          </div>
        </div>
        
        {/* Import Batch Manager */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Import History</h2>
          <ImportBatchManager />
        </div>
      </div>

      {/* Upload Modal */}
      <UploadModal 
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={() => {
          setIsUploadModalOpen(false)
          // Could trigger a refresh here
        }}
      />
    </div>
  )
}