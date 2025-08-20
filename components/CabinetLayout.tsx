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
import Sidebar from './Sidebar'
import TaxOptimizationDashboard from './TaxOptimizationDashboard'
import CashFlowForecastingDashboard from './CashFlowForecastingDashboard'
import ScenarioSimulationEngine from './ScenarioSimulationEngine'
import InvoiceRiskDashboard from './InvoiceRiskDashboard'
import EnhancedAnalyticsDashboard from './EnhancedAnalyticsDashboard'
import ClientPaymentPredictionDashboard from './ClientPaymentPredictionDashboard'
import TransactionTable from './TransactionTable'
import UploadModal from './UploadModal'
import ImportBatchManager from './ImportBatchManager'
import CategorizationPerformance from './CategorizationPerformance'
import AutoImprovement from './AutoImprovement'
import SuggestionDisplay from './SuggestionDisplay'

export default function CabinetLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [activeSection, setActiveSection] = useState('chat')

  return (
    <div className="h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <Sidebar 
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        activeSection={activeSection}
        onSectionChange={setActiveSection}
      />

      {/* Main Content Area */}
      <main className={`flex-1 flex flex-col transition-all duration-300 ${
        isSidebarOpen ? 'ml-0' : 'ml-0'
      }`}>
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {!isSidebarOpen && (
                <button
                  onClick={() => setIsSidebarOpen(true)}
                  className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
                >
                  <Menu className="h-5 w-5" />
                </button>
              )}
              <div className="flex items-center space-x-3">
                <div className="w-7 h-7 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-xs">S</span>
                </div>
                <h1 className="text-lg font-semibold text-gray-900">Spend's Analysis</h1>
              </div>
            </div>
            
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span>Dr. Spend Online</span>
            </div>
          </div>
        </header>

        {/* Main Content Interface */}
        <div className="flex-1 flex flex-col">
          {activeSection === 'chat' ? (
            <EnhancedDrSigmundChat />
          ) : activeSection === 'tax-optimization' ? (
            <div className="flex-1 overflow-y-auto p-6">
              <TaxOptimizationDashboard />
            </div>
          ) : activeSection === 'forecasting' ? (
            <div className="flex-1 overflow-y-auto p-6">
              <CashFlowForecastingDashboard />
            </div>
          ) : activeSection === 'scenarios' ? (
            <div className="flex-1 overflow-y-auto p-6">
              <ScenarioSimulationEngine />
            </div>
          ) : activeSection === 'invoice-risk' ? (
            <div className="flex-1 overflow-y-auto">
              <InvoiceRiskDashboard />
            </div>
          ) : activeSection === 'analytics' ? (
            <div className="flex-1 overflow-y-auto">
              <EnhancedAnalyticsDashboard />
            </div>
          ) : activeSection === 'payment-prediction' ? (
            <div className="flex-1 overflow-y-auto p-6">
              <ClientPaymentPredictionDashboard />
            </div>
          ) : activeSection === 'categorization' ? (
            <div className="flex-1 overflow-y-auto p-6">
              <CategorizationSection />
            </div>
          ) : activeSection === 'transactions' ? (
            <div className="flex-1 overflow-y-auto p-6">
              <TransactionsSection />
            </div>
          ) : activeSection === 'upload' ? (
            <div className="flex-1 overflow-y-auto p-6">
              <UploadSection />
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  {activeSection === 'budgets' && <Target className="h-8 w-8 text-blue-600" />}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {activeSection === 'budgets' && 'Budget Analysis'}
                </h3>
                <p className="text-gray-600 mb-6">
                  This feature will be integrated soon. For now, let's chat about your financial goals!
                </p>
                <button
                  onClick={() => setActiveSection('chat')}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Return to Chat
                </button>
              </div>
            </div>
          )}
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
      confidence_score: 95
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
      confidence_score: 88
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
      confidence_score: 92
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
      
      <TransactionTable 
        transactions={mockTransactions} 
        isLoading={false}
      />
    </div>
  )
}

// Upload Section Component
function UploadSection() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Upload</h1>
        <p className="mt-1 text-sm text-gray-500">
          Import and map your financial data files
        </p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upload Modal */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload New File</h2>
          <UploadModal />
        </div>
        
        {/* Import Batch Manager */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Import History</h2>
          <ImportBatchManager />
        </div>
      </div>
    </div>
  )
}