'use client'

import React from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import CategorizationPerformance from '@/components/CategorizationPerformance'
import AutoImprovement from '@/components/AutoImprovement'
import SuggestionDisplay from '@/components/SuggestionDisplay'

export default function CategorizationPage() {
  return (
    <DashboardLayout>
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
    </DashboardLayout>
  )
}
