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
import ChatInterface from './ChatInterface'
import Sidebar from './Sidebar'
import TaxOptimizationDashboard from './TaxOptimizationDashboard'
import CashFlowForecastingDashboard from './CashFlowForecastingDashboard'
import ScenarioSimulationDashboard from './ScenarioSimulationDashboard'

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
                  <span className="text-white font-bold text-xs">F</span>
                </div>
                <h1 className="text-lg font-semibold text-gray-900">FeenGood</h1>
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
            <ChatInterface />
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
              <ScenarioSimulationDashboard />
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  {activeSection === 'transactions' && <FileText className="h-8 w-8 text-blue-600" />}
                  {activeSection === 'analytics' && <BarChart3 className="h-8 w-8 text-blue-600" />}
                  {activeSection === 'forecasting' && <TrendingUp className="h-8 w-8 text-blue-600" />}
                  {activeSection === 'budgets' && <Target className="h-8 w-8 text-blue-600" />}
                  {activeSection === 'scenarios' && <GitBranch className="h-8 w-8 text-blue-600" />}
                  {activeSection === 'upload' && <Upload className="h-8 w-8 text-blue-600" />}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {activeSection === 'transactions' && 'Transaction Management'}
                  {activeSection === 'analytics' && 'Financial Analytics'}
                  {activeSection === 'forecasting' && 'Cash Flow Forecasting'}
                  {activeSection === 'budgets' && 'Budget Analysis'}
                  {activeSection === 'scenarios' && 'Scenario Simulation'}
                  {activeSection === 'upload' && 'Data Upload'}
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