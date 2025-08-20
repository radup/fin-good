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
  Settings,
  X,
  Plus,
  Brain,
  Heart,
  ChevronDown,
  Clock,
  Archive,
  Lightbulb,
  DollarSign,
  PieChart,
  Calculator,
  GitBranch,
  Receipt
} from 'lucide-react'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
  activeSection: string
  onSectionChange: (section: string) => void
}

export default function Sidebar({ isOpen, onToggle, activeSection, onSectionChange }: SidebarProps) {
  const [isHistoryExpanded, setIsHistoryExpanded] = useState(true)

  // Mock chat history data
  const chatHistory = [
    { id: '1', title: 'Budget Planning for Q4', date: 'Today', preview: 'How can I create a realistic budget...' },
    { id: '2', title: 'Expense Categorization Help', date: 'Yesterday', preview: 'I need help understanding why...' },
    { id: '3', title: 'Cash Flow Forecasting', date: '2 days ago', preview: 'What will my cash flow look like...' },
    { id: '4', title: 'Investment Anxiety Discussion', date: '3 days ago', preview: 'I feel anxious about investing...' },
    { id: '5', title: 'Monthly Spending Review', date: '1 week ago', preview: 'Can you help me analyze...' }
  ]

  const technicalTools = [
    { id: 'transactions', icon: FileText, label: 'Transactions', description: 'Manage your financial data' },
    { id: 'analytics', icon: BarChart3, label: 'Analytics', description: 'Insights and reports' },
    { id: 'forecasting', icon: TrendingUp, label: 'Forecasting', description: 'Predict cash flow' },
    { id: 'budgets', icon: Target, label: 'Budgets', description: 'Plan and track spending' },
    { id: 'scenarios', icon: GitBranch, label: 'Scenario Simulation', description: 'What-if financial modeling' },
    { id: 'tax-optimization', icon: Receipt, label: 'Tax Optimization', description: 'Minimize tax burden' },
    { id: 'upload', icon: Upload, label: 'Upload Data', description: 'Import financial files' }
  ]

  if (!isOpen) return null

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">Your Sessions</h2>
          <button
            onClick={onToggle}
            className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        
        {/* New Chat Button */}
        <button
          onClick={() => onSectionChange('chat')}
          className="w-full mt-3 flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>New Session</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Chat History */}
        <div className="p-4">
          <button
            onClick={() => setIsHistoryExpanded(!isHistoryExpanded)}
            className="flex items-center justify-between w-full text-sm font-medium text-gray-700 hover:text-gray-900"
          >
            <div className="flex items-center space-x-2">
              <History className="h-4 w-4" />
              <span>Recent Sessions</span>
            </div>
            <ChevronDown className={`h-4 w-4 transition-transform ${isHistoryExpanded ? 'rotate-0' : '-rotate-90'}`} />
          </button>

          {isHistoryExpanded && (
            <div className="mt-3 space-y-1">
              {chatHistory.map((chat) => (
                <button
                  key={chat.id}
                  onClick={() => onSectionChange('chat')}
                  className={`w-full text-left p-3 rounded-lg transition-colors group hover:bg-gray-50 ${
                    activeSection === 'chat' && chat.id === '1' ? 'bg-blue-50 border border-blue-200' : ''
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium text-gray-900 truncate">{chat.title}</h4>
                      <p className="text-xs text-gray-500 mt-1 truncate">{chat.preview}</p>
                      <div className="flex items-center space-x-1 mt-1">
                        <Clock className="h-3 w-3 text-gray-400" />
                        <span className="text-xs text-gray-400">{chat.date}</span>
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="mx-4 border-t border-gray-200"></div>

        {/* Technical Tools */}
        <div className="p-4">
          <div className="flex items-center space-x-2 mb-3">
            <Brain className="h-4 w-4 text-purple-600" />
            <span className="text-sm font-medium text-gray-700">Technical Tools</span>
          </div>

          <div className="space-y-1">
            {technicalTools.map((tool) => (
              <button
                key={tool.id}
                onClick={() => onSectionChange(tool.id)}
                className={`w-full text-left p-3 rounded-lg transition-colors group hover:bg-gray-50 ${
                  activeSection === tool.id ? 'bg-purple-50 border border-purple-200' : ''
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    activeSection === tool.id ? 'bg-purple-100' : 'bg-gray-100 group-hover:bg-gray-200'
                  }`}>
                    <tool.icon className={`h-4 w-4 ${
                      activeSection === tool.id ? 'text-purple-600' : 'text-gray-600'
                    }`} />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">{tool.label}</h4>
                    <p className="text-xs text-gray-500">{tool.description}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Divider */}
        <div className="mx-4 border-t border-gray-200"></div>

        {/* Therapeutic Features */}
        <div className="p-4">
          <div className="flex items-center space-x-2 mb-3">
            <Heart className="h-4 w-4 text-red-500" />
            <span className="text-sm font-medium text-gray-700">Wellness Tools</span>
          </div>

          <div className="space-y-1">
            <button
              className="w-full text-left p-3 rounded-lg transition-colors group hover:bg-gray-50"
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                  <Heart className="h-4 w-4 text-red-600" />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-900">Emotional Check-in</h4>
                  <p className="text-xs text-gray-500">How are you feeling today?</p>
                </div>
              </div>
            </button>

            <button
              className="w-full text-left p-3 rounded-lg transition-colors group hover:bg-gray-50"
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <Lightbulb className="h-4 w-4 text-yellow-600" />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-900">Insights</h4>
                  <p className="text-xs text-gray-500">Personalized recommendations</p>
                </div>
              </div>
            </button>

            <button
              className="w-full text-left p-3 rounded-lg transition-colors group hover:bg-gray-50"
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <DollarSign className="h-4 w-4 text-green-600" />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-900">Goal Setting</h4>
                  <p className="text-xs text-gray-500">Define financial objectives</p>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-gray-200 p-4">
        <button
          className="w-full flex items-center space-x-3 p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors"
        >
          <Settings className="h-5 w-5" />
          <span className="text-sm">Settings</span>
        </button>
      </div>
    </div>
  )
}