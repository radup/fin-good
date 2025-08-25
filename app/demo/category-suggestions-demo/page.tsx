'use client'

import React, { useState } from 'react'
import SuggestionDisplay from '@/components/SuggestionDisplay'

export default function CategorySuggestionsDemo() {
  const [selectedCategory, setSelectedCategory] = useState('Food & Dining')
  const [selectedSubcategory, setSelectedSubcategory] = useState('Restaurants')

  const handleSuggestionApplied = (category: string, subcategory?: string) => {
    setSelectedCategory(category)
    setSelectedSubcategory(subcategory || '')
    alert(`Applied suggestion: ${category}${subcategory ? ` → ${subcategory}` : ''}`)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Category Suggestions Demo</h1>
          <p className="mt-2 text-gray-600">
            Test category suggestions with ML predictions and rule-based matches
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Current Selection */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Selection</h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <div className="p-3 bg-gray-50 rounded border">
                  {selectedCategory}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Subcategory
                </label>
                <div className="p-3 bg-gray-50 rounded border">
                  {selectedSubcategory || 'None'}
                </div>
              </div>
            </div>
          </div>

          {/* Suggestions */}
          <div>
            <SuggestionDisplay
              transactionId={1}
              currentCategory={selectedCategory}
              currentSubcategory={selectedSubcategory}
              onSuggestionApplied={handleSuggestionApplied}
            />
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-8 bg-blue-50 rounded-lg border border-blue-200 p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-3">How to Test</h3>
          <ul className="text-sm text-blue-700 space-y-2">
            <li>• The component shows mock suggestions for transaction ID 1</li>
            <li>• Click "Apply" on any suggestion to see it update the current selection</li>
            <li>• Toggle "Show Details" to see ML predictions and rule matches</li>
            <li>• Click "Refresh Suggestions" to reload the suggestions</li>
            <li>• In development mode, mock data is used when the API is unavailable</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
