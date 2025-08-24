'use client'

import React, { useState } from 'react'
import { 
  Home, 
  Brain, 
  Target, 
  Clock, 
  Calculator, 
  TrendingUp, 
  PieChart, 
  CreditCard, 
  FileText, 
  Upload, 
  BarChart3, 
  Heart, 
  Settings, 
  LogOut,
  User,
  ChevronDown,
  ChevronRight,
  MessageCircle,
  History,
  Eye,
  Target as TargetIcon,
  Zap
} from 'lucide-react'

interface CabinetNavigationProps {
  activeSection: string
  onSectionChange: (section: string) => void
}

interface NavItem {
  id: string
  name: string
  icon: React.ReactNode
  description: string
  children?: NavItem[]
}

const navigation: NavItem[] = [
  {
    id: 'dashboard',
    name: 'Dashboard',
    icon: <Home className="w-5 h-5" />,
    description: 'Overview and summary'
  },
  {
    id: 'dr-sigmund',
    name: 'Dr Sigmund AI',
    icon: <Brain className="w-5 h-5" />,
    description: 'AI financial therapist',
    children: [
      {
        id: 'new-session',
        name: 'New Session',
        icon: <MessageCircle className="w-4 h-4" />,
        description: 'Start new therapy session'
      },
      {
        id: 'sessions-history',
        name: 'Sessions History',
        icon: <History className="w-4 h-4" />,
        description: 'View past sessions'
      }
    ]
  },
  {
    id: 'scenario-engine',
    name: 'Scenario Engine',
    icon: <Target className="w-5 h-5" />,
    description: 'What-if simulations'
  },
  {
    id: 'payment-prediction',
    name: 'Payment Prediction',
    icon: <Clock className="w-5 h-5" />,
    description: 'Client payment forecasts'
  },
  {
    id: 'tax-optimization',
    name: 'Tax Optimization',
    icon: <Calculator className="w-5 h-5" />,
    description: 'Multi-jurisdiction tax planning'
  },
  {
    id: 'cash-flow-forecast',
    name: 'Cash Flow Forecast',
    icon: <TrendingUp className="w-5 h-5" />,
    description: 'Financial forecasting'
  },
  {
    id: 'budget-analysis',
    name: 'Budget Analysis',
    icon: <PieChart className="w-5 h-5" />,
    description: 'Budget planning & analysis'
  },
  {
    id: 'invoice-risk',
    name: 'Invoice & Risk',
    icon: <CreditCard className="w-5 h-5" />,
    description: 'Invoice analysis and risk assessment'
  },
  {
    id: 'transactions',
    name: 'Transactions',
    icon: <FileText className="w-5 h-5" />,
    description: 'Manage transactions'
  },
  {
    id: 'categorization',
    name: 'Categorisation',
    icon: <Brain className="w-5 h-5" />,
    description: 'AI categorization tools'
  },
  {
    id: 'data-import',
    name: 'Data Import',
    icon: <Upload className="w-5 h-5" />,
    description: 'Import data files'
  },
  {
    id: 'analytics',
    name: 'Analytics',
    icon: <BarChart3 className="w-5 h-5" />,
    description: 'Analytics and insights'
  },
  {
    id: 'wellness-tools',
    name: 'Wellness Tools',
    icon: <Heart className="w-5 h-5" />,
    description: 'Financial wellness tools',
    children: [
      {
        id: 'emotional-checkin',
        name: 'Emotional Check-In',
        icon: <Heart className="w-4 h-4" />,
        description: 'Track financial emotions'
      },
      {
        id: 'insights',
        name: 'Insights',
        icon: <Eye className="w-4 h-4" />,
        description: 'Personalized insights'
      },
      {
        id: 'goal-settings',
        name: 'Goal Settings',
        icon: <TargetIcon className="w-4 h-4" />,
        description: 'Set financial goals'
      }
    ]
  },
  {
    id: 'settings',
    name: 'Settings',
    icon: <Settings className="w-5 h-5" />,
    description: 'Preferences and account'
  }
]

export default function CabinetNavigation({ activeSection, onSectionChange }: CabinetNavigationProps) {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set(['dr-sigmund', 'wellness-tools']))

  const toggleExpanded = (itemId: string) => {
    const newExpanded = new Set(expandedItems)
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId)
    } else {
      newExpanded.add(itemId)
    }
    setExpandedItems(newExpanded)
  }

  const isActive = (itemId: string) => {
    return activeSection === itemId
  }

  const handleLogout = async () => {
    try {
      const { authAPI } = await import('../lib/api')
      await authAPI.logout()
      // Redirect to home page after successful logout
      window.location.href = '/'
    } catch (error) {
      console.error('Logout failed:', error)
      // Still redirect to home even if logout API call fails
      window.location.href = '/'
    }
  }

  const renderNavItem = (item: NavItem, level: number = 0) => {
    const active = isActive(item.id)
    const hasChildren = item.children && item.children.length > 0
    const isExpanded = expandedItems.has(item.id)

    return (
      <div key={item.id}>
        <button
          onClick={() => {
            if (hasChildren) {
              toggleExpanded(item.id)
            } else {
              onSectionChange(item.id)
            }
          }}
          className={`w-full group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
            active
              ? 'bg-blue-100 text-blue-900 border-r-2 border-blue-600'
              : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
          } ${level > 0 ? 'ml-4' : ''}`}
        >
          <div className={`mr-3 ${active ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-500'}`}>
            {item.icon}
          </div>
          <div className="flex-1 text-left">
            <div className="font-medium">{item.name}</div>
            <div className="text-xs text-gray-500">{item.description}</div>
          </div>
          {hasChildren && (
            <div className={`ml-2 transition-transform ${isExpanded ? 'rotate-90' : ''}`}>
              <ChevronRight className="w-4 h-4 text-gray-400" />
            </div>
          )}
        </button>
        
        {hasChildren && isExpanded && (
          <div className="mt-1 space-y-1">
            {item.children!.map((child) => renderNavItem(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-white border-r border-gray-200">
      {/* Logo Header */}
      <div className="flex items-center h-16 flex-shrink-0 px-4 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">FG</span>
            </div>
          </div>
          <div className="ml-3">
            <h1 className="text-lg font-semibold text-gray-900">Spend's Analysis</h1>
            <p className="text-xs text-gray-500">AI Financial Therapy</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 flex flex-col overflow-y-auto">
        <nav className="flex-1 px-2 py-4 space-y-1">
          {navigation.map((item) => renderNavItem(item))}
        </nav>
      </div>

      {/* User Footer */}
      <div className="flex-shrink-0 flex border-t border-gray-200 p-4">
        <div className="flex items-center w-full">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-gray-600" />
            </div>
          </div>
          <div className="ml-3 flex-1">
            <p className="text-sm font-medium text-gray-700">Demo User</p>
            <p className="text-xs text-gray-500">demo@fingood.com</p>
          </div>
          <button
            onClick={handleLogout}
            className="ml-2 p-1 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
