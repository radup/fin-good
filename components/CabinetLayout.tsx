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
  Bot
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

export default function CabinetLayout() {
  const [activeSection, setActiveSection] = useState('dashboard')

  return (
    <div className="h-screen bg-gray-50 flex">
      {/* Navigation */}
      <div className="w-64 flex-shrink-0">
        <CabinetNavigation 
          activeSection={activeSection}
          onSectionChange={setActiveSection}
        />
      </div>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <CabinetHeader title="Cabinet" />

        {/* Main Content Interface */}
        <div className="flex-1 overflow-y-auto">
          <div className="py-6 px-4 sm:px-6 lg:px-8">
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
              <div className="h-full flex flex-col">
                <div className="flex-shrink-0 mb-4">
                  <h1 className="text-2xl font-bold text-gray-900">New Session</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    Start a new therapy session with Dr. Sigmund
                  </p>
                </div>
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
                <div className="bg-white rounded-lg shadow p-6">
                  <p className="text-gray-600">Session history will be displayed here.</p>
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
                <div className="bg-white rounded-lg shadow p-6">
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
                <div className="bg-white rounded-lg shadow p-6">
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
                <div className="bg-white rounded-lg shadow p-6">
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
                <div className="bg-white rounded-lg shadow p-6">
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
                <div className="bg-white rounded-lg shadow p-6">
                  <p className="text-gray-600">Settings will be displayed here.</p>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Brain className="h-8 w-8 text-blue-600" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Welcome to Cabinet</h3>
                  <p className="text-gray-600">Select a section from the navigation to get started.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
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
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Upload className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Upload CSV File</h3>
              <p className="text-gray-600 mb-6">
                Import your financial transactions from a CSV file for AI-powered categorization and analysis.
              </p>
              <button
                onClick={() => setIsUploadModalOpen(true)}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
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