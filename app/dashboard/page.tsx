'use client'

import React from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import DashboardComponent from '@/app/DashboardComponent'
import { ExportManager } from '@/components/ExportManager'

export default function DashboardPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            Overview of your financial data and insights
          </p>
        </div>
        
        <DashboardComponent />
        
        {/* Export Manager Section */}
        <div className="mt-8">
          <ExportManager />
        </div>
      </div>
    </DashboardLayout>
  )
}
