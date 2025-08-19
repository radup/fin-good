'use client'

import React, { useState } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { TransactionTable } from '@/components/TransactionTable'

export default function TransactionsPage() {
  const [refreshKey, setRefreshKey] = useState(0)

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Transactions</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage and categorize your financial transactions
          </p>
        </div>
        
        <TransactionTable 
          transactions={[]}
          isLoading={false}
          refreshKey={refreshKey}
        />
      </div>
    </DashboardLayout>
  )
}
