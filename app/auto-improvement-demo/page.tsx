'use client'

import React from 'react'
import AutoImprovement from '@/components/AutoImprovement'

export default function AutoImprovementDemo() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Auto-Improvement Dashboard</h1>
          <p className="mt-2 text-gray-600">
            Automatically improve categorization rules and ML model based on feedback and patterns
          </p>
        </div>
        <AutoImprovement />
      </div>
    </div>
  )
}
