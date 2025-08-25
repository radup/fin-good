'use client'

import React, { useState } from 'react'
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar'
import { 
  drSigmundAdviceClasses, 
  drSigmundHeaderClasses, 
  drSigmundToggleClasses,
  drSigmundExpandableBorderClasses
} from '../lib/design-utils'

interface DrSigmundAdviceCardProps {
  variant?: 'default' | 'risk' | 'insights' | 'ml' | 'business'
  title: string
  badgeText: string
  children: React.ReactNode
  expandableContent?: React.ReactNode
  className?: string
  defaultExpanded?: boolean
  mood?: 'encouraging' | 'celebrating' | 'supportive' | 'thinking' | 'reassuring' | 'analytical' | 'inspiring' | 'protective'
}

export function DrSigmundAdviceCard({
  variant = 'default',
  title,
  badgeText,
  children,
  expandableContent,
  className,
  defaultExpanded = false,
  mood = 'analytical'
}: DrSigmundAdviceCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  const headerStyles = drSigmundHeaderClasses(variant)

  return (
    <div className={drSigmundAdviceClasses(variant, className)}>
      {/* Main Banner */}
      <div className="flex items-center space-x-4">
        <DrSigmundSpendAvatar 
          size="sm"
          mood={mood}
          message=""
          showMessage={false}
          animated={true}
        />
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-sm font-semibold">Dr. Sigmund Spend</span>
            <span className={headerStyles.badge}>{badgeText}</span>
          </div>
          <div className={headerStyles.content}>
            {children}
          </div>
        </div>
        {expandableContent && (
          <button 
            onClick={() => setIsExpanded(!isExpanded)}
            className={drSigmundToggleClasses(variant)}
          >
            <span>{isExpanded ? 'Hide Details' : 'View Details'}</span>
            <svg 
              className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        )}
      </div>

      {/* Expanded Details */}
      {expandableContent && isExpanded && (
        <div className={drSigmundExpandableBorderClasses(variant)}>
          {expandableContent}
        </div>
      )}
    </div>
  )
}

export default DrSigmundAdviceCard