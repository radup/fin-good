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
    id: 'reports',
    name: 'Reports',
    icon: <FileText className="w-5 h-5" />,
    description: 'Financial reports and analytics'
  },

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
          className={`w-full group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
            active
              ? 'bg-brand-primary-lightest text-brand-primary border-r-2 border-brand-primary shadow-sm'
              : 'text-gray-600 hover:bg-brand-primary-lightest/50 hover:text-brand-primary'
          } ${level > 0 ? 'ml-4' : ''}`}
        >
          <div className={`mr-3 ${active ? 'text-brand-primary' : 'text-gray-400 group-hover:text-brand-primary'}`}>
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
    <div className="flex flex-col h-full bg-white/95 backdrop-blur-sm border-r border-brand-primary-lighter/30">
      {/* Navigation starts directly */}

      {/* Navigation */}
      <div className="flex-1 flex flex-col overflow-y-auto">
        <nav className="flex-1 px-2 py-4 pt-8 space-y-1">
          {navigation.map((item) => renderNavItem(item))}
        </nav>
      </div>
    </div>
  )
}
