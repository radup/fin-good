'use client'

import { useState, useEffect, useMemo } from 'react'
import { format } from 'date-fns'
import { Edit, Trash2, Check, X, ChevronUp, ChevronDown, ChevronsUpDown, CheckCircle, AlertCircle } from 'lucide-react'
import { ComboBox } from './ComboBox'
import { TransactionFilters } from './TransactionFilters'
import { Pagination } from './Pagination'
import { useCategoryOptions } from '@/hooks/useCategories'
import { transactionAPI } from '@/lib/api'
import { useQueryClient } from '@tanstack/react-query'

interface Transaction {
  id: number
  date: string
  description: string
  amount: number
  vendor?: string
  category?: string
  subcategory?: string
  is_income: boolean
  is_categorized: boolean
  confidence_score?: number
}

type SortField = 'date' | 'description' | 'vendor' | 'amount' | 'category' | 'subcategory' | 'status'
type SortDirection = 'asc' | 'desc'

interface TransactionTableProps {
  transactions: Transaction[]
  isLoading: boolean
}

export function TransactionTable({ transactions: initialTransactions, isLoading }: TransactionTableProps) {
  const [transactions, setTransactions] = useState<Transaction[]>(initialTransactions || [])
  const [totalCount, setTotalCount] = useState(initialTransactions?.length || 0)
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(50)
  const [filters, setFilters] = useState({})
  const [categories, setCategories] = useState<string[]>([])
  const [subcategories, setSubcategories] = useState<string[]>([])
  const [isLoadingData, setIsLoadingData] = useState(false)
  
  // Edit mode state
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editCategory, setEditCategory] = useState('')
  const [editSubcategory, setEditSubcategory] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState<string | null>(null)

  const { categories: allCategories, getSubcategories, isLoading: categoriesLoading } = useCategoryOptions()
  const queryClient = useQueryClient()

  // Extract unique categories and subcategories from transactions
  useEffect(() => {
    const uniqueCategories = Array.from(new Set(transactions.map(t => t.category).filter(Boolean) as string[]))
    const uniqueSubcategories = Array.from(new Set(transactions.map(t => t.subcategory).filter(Boolean) as string[]))
    setCategories(uniqueCategories)
    setSubcategories(uniqueSubcategories)
  }, [transactions])

  // Update transactions when prop changes
  useEffect(() => {
    if (initialTransactions) {
      setTransactions(initialTransactions)
      setTotalCount(initialTransactions.length)
    }
  }, [initialTransactions])

  // Fetch transactions with filters and pagination
  const fetchTransactions = async () => {
    setIsLoadingData(true)
    try {
      const params = {
        skip: (currentPage - 1) * itemsPerPage,
        limit: itemsPerPage,
        ...filters
      }
      
      const [transactionsResponse, countResponse] = await Promise.all([
        transactionAPI.getTransactions(params),
        transactionAPI.getTransactionCount(filters)
      ])
      
      setTransactions(transactionsResponse.data)
      setTotalCount(countResponse.data.count)
    } catch (error) {
      console.error('Error fetching transactions:', error)
    } finally {
      setIsLoadingData(false)
    }
  }

  // Fetch data when filters, page, or items per page change
  useEffect(() => {
    fetchTransactions()
  }, [filters, currentPage, itemsPerPage])

  // Handle filter changes
  const handleFiltersChange = (newFilters: any) => {
    setFilters(newFilters)
    setCurrentPage(1) // Reset to first page when filters change
  }

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  // Handle items per page change
  const handleItemsPerPageChange = (newItemsPerPage: number) => {
    setItemsPerPage(newItemsPerPage)
    setCurrentPage(1) // Reset to first page when changing items per page
  }

  const handleEdit = (transaction: Transaction) => {
    setEditingId(transaction.id)
    setEditCategory(transaction.category || '')
    setEditSubcategory(transaction.subcategory || '')
  }

  const handleCancel = () => {
    setEditingId(null)
    setEditCategory('')
    setEditSubcategory('')
    setSaveMessage(null)
  }

  const handleSave = async (id: number) => {
    if (!editCategory.trim()) {
      setSaveMessage('Please enter a category')
      return
    }
    
    setIsSaving(true)
    setSaveMessage(null)
    
    try {
      const response = await transactionAPI.update(id, {
        category: editCategory,
        subcategory: editSubcategory || undefined,
        create_rule: true // Automatically create a rule for future similar transactions
      })
      
      if (response.data.auto_categorized_count > 0) {
        setSaveMessage(`✅ Transaction updated! ${response.data.auto_categorized_count} similar transactions were automatically categorized.`)
      } else {
        setSaveMessage('✅ Transaction updated successfully!')
      }
      
      // Refresh the data
      fetchTransactions()
      
      setTimeout(() => {
        setEditingId(null)
        setEditCategory('')
        setEditSubcategory('')
        setSaveMessage(null)
      }, 2000)
      
    } catch (error) {
      console.error('Error saving transaction:', error)
      setSaveMessage('❌ Error saving transaction. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this transaction?')) {
      try {
        await transactionAPI.delete(id)
        fetchTransactions() // Refresh the data
      } catch (error) {
        console.error('Error deleting transaction:', error)
        alert('Error deleting transaction')
      }
    }
  }

  // Get available subcategories based on selected category
  const availableSubcategories = useMemo(() => {
    if (!editCategory) return []
    return getSubcategories(editCategory)
  }, [editCategory, getSubcategories])

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    )
  }

  if (!transactions || !Array.isArray(transactions) || transactions.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500 mb-4">No transactions found</p>
        <p className="text-sm text-gray-400">
          Upload a CSV file to get started
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Filters */}
      <TransactionFilters
        onFiltersChange={handleFiltersChange}
        categories={categories}
        subcategories={subcategories}
      />

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Description
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Vendor
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Amount
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Subcategory
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {isLoadingData ? (
              <tr>
                <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                  Loading transactions...
                </td>
              </tr>
            ) : transactions.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                  No transactions found
                </td>
              </tr>
            ) : (
              transactions.map((transaction) => (
                <tr key={transaction.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {format(new Date(transaction.date), 'MMM dd, yyyy')}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                    {transaction.description}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {transaction.vendor || '-'}
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                    transaction.is_income ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {transaction.is_income ? '+' : '-'}${Math.abs(transaction.amount).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {editingId === transaction.id ? (
                      <ComboBox
                        options={allCategories}
                        value={editCategory}
                        onChange={setEditCategory}
                        placeholder="Select category"
                        className="w-32"
                      />
                    ) : (
                      transaction.category || '-'
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {editingId === transaction.id ? (
                      <ComboBox
                        options={getSubcategories(editCategory)}
                        value={editSubcategory}
                        onChange={setEditSubcategory}
                        placeholder="Select subcategory"
                        className="w-32"
                      />
                    ) : (
                      transaction.subcategory || '-'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      {transaction.is_categorized ? (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-yellow-500" />
                      )}
                      <span className="text-xs text-gray-500">
                        {transaction.confidence_score ? `${Math.round(transaction.confidence_score * 100)}%` : 'N/A'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {editingId === transaction.id ? (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleSave(transaction.id)}
                          disabled={isSaving}
                          className="text-green-600 hover:text-green-900 disabled:opacity-50"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleCancel()}
                          className="text-gray-600 hover:text-gray-900"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleEdit(transaction)}
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(transaction.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Save Message */}
      {saveMessage && (
        <div className="px-6 py-3 bg-blue-50 border-t border-blue-200">
          <p className="text-sm text-blue-800">{saveMessage}</p>
        </div>
      )}

      {/* Pagination */}
      {totalCount > 0 && (
        <Pagination
          currentPage={currentPage}
          totalPages={Math.ceil(totalCount / itemsPerPage)}
          totalItems={totalCount}
          itemsPerPage={itemsPerPage}
          onPageChange={handlePageChange}
          onItemsPerPageChange={handleItemsPerPageChange}
        />
      )}
    </div>
  )
}
