'use client'

import React, { useState } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { TransactionTable } from '@/components/TransactionTable'

export default function TransactionsPage() {
  // Mock data for transactions - in a real app this would come from an API
  const mockTransactions = [
    {
      id: 1,
      date: '2025-01-15',
      description: 'Client Payment - Web Development',
      amount: 2500,
      vendor: 'Tech Solutions Inc.',
      category: 'Income',
      subcategory: 'Consulting',
      is_income: true,
      is_categorized: true,
      confidence_score: 95
    },
    {
      id: 2,
      date: '2025-01-14',
      description: 'Office Supplies',
      amount: -45.80,
      vendor: 'OfficeMax',
      category: 'Business Expenses',
      subcategory: 'Office Supplies',
      is_income: false,
      is_categorized: true,
      confidence_score: 88
    },
    {
      id: 3,
      date: '2025-01-13',
      description: 'Monthly Software Subscription',
      amount: -29.99,
      vendor: 'Adobe',
      category: 'Business Expenses',
      subcategory: 'Software',
      is_income: false,
      is_categorized: true,
      confidence_score: 92
    }
  ]

  const [isLoading] = useState(false)

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
          transactions={mockTransactions} 
          isLoading={isLoading}
        />
      </div>
    </DashboardLayout>
  )
}
