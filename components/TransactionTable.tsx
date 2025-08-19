'use client'

import { useState, useEffect, useMemo } from 'react'
import { format } from 'date-fns'
import { Edit, Trash2, Check, X, ChevronUp, ChevronDown, ChevronsUpDown, CheckCircle, AlertCircle, Square, CheckSquare, ScanSearch } from 'lucide-react'
import { ComboBox } from './ComboBox'
import { TransactionFilters } from './TransactionFilters'
import { Pagination } from './Pagination'
import { useCategoryOptions } from '@/hooks/useCategories'
import { transactionAPI, bulkOperationsAPI } from '@/lib/api'
import { useQueryClient } from '@tanstack/react-query'
import AIConfidenceDisplay from './AIConfidenceDisplay'
import type { BulkOperationResponse } from '@/types/api'

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
	refreshKey?: number // Add refresh key to trigger data refresh
}

export function TransactionTable({ transactions: initialTransactions, isLoading, refreshKey }: TransactionTableProps) {
	const [transactions, setTransactions] = useState<Transaction[]>(initialTransactions || [])
	const [totalCount, setTotalCount] = useState(initialTransactions?.length || 0)
	const [currentPage, setCurrentPage] = useState(1)
	const [itemsPerPage, setItemsPerPage] = useState(50)
	const [filters, setFilters] = useState({})
	const [categories, setCategories] = useState<string[]>([])
	const [subcategories, setSubcategories] = useState<string[]>([])
	const [isLoadingData, setIsLoadingData] = useState(false)
	
	// Sorting state
	const [sortField, setSortField] = useState<SortField>('date')
	const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
	
	// Edit mode state
	const [editingId, setEditingId] = useState<number | null>(null)
	const [editCategory, setEditCategory] = useState('')
	const [editSubcategory, setEditSubcategory] = useState('')
	const [isSaving, setIsSaving] = useState(false)
	const [saveMessage, setSaveMessage] = useState<string | null>(null)

	// Bulk selection state
	const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
	const [isApplyingBulk, setIsApplyingBulk] = useState(false)
	const [bulkCategory, setBulkCategory] = useState('')
	const [bulkSubcategory, setBulkSubcategory] = useState('')
	const [bulkMessage, setBulkMessage] = useState<string | null>(null)
	const [lastBulkAction, setLastBulkAction] = useState<null | { changes: { id: number, prevCategory?: string, prevSubcategory?: string }[] }>(null)
	
	const { categories: allCategories, getSubcategories, isLoading: categoriesLoading } = useCategoryOptions()
	const queryClient = useQueryClient()

	// Extract unique categories and subcategories from transactions
	useEffect(() => {
		const uniqueCategories = Array.from(new Set(transactions.map(t => t.category).filter(Boolean) as string[]))
		const uniqueSubcategories = Array.from(new Set(transactions.map(t => t.subcategory).filter(Boolean) as string[]))
		setCategories(uniqueCategories)
		setSubcategories(uniqueSubcategories)
	}, [transactions])

	// Always fetch fresh data from the API for filtering and sorting
	// Ignore the prop data to ensure we always have the latest data

	// Fetch transactions with filters, sorting, and pagination
	const fetchTransactions = async () => {
		setIsLoadingData(true)
		try {
			const params = {
				skip: (currentPage - 1) * itemsPerPage,
				limit: itemsPerPage,
				sort_by: sortField,
				sort_order: sortDirection,
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

	// Fetch data when filters, sorting, page, or items per page change
	useEffect(() => {
		fetchTransactions()
	}, [filters, sortField, sortDirection, currentPage, itemsPerPage])

	// Also fetch data on component mount and when refreshKey changes
	useEffect(() => {
		fetchTransactions()
	}, [refreshKey])

	// Handle filter changes
	const handleFiltersChange = (newFilters: any) => {
		// Clean up filter values - remove empty strings and convert boolean strings
		const cleanedFilters = Object.entries(newFilters).reduce((acc, [key, value]) => {
			if (value === '') return acc
			
			// Convert boolean strings to actual booleans
			if (key === 'is_income' || key === 'is_categorized') {
				if (value === 'true') acc[key] = true
				else if (value === 'false') acc[key] = false
			} else {
				acc[key] = value
			}
			
			return acc
		}, {} as any)
		
		setFilters(cleanedFilters)
		setCurrentPage(1) // Reset to first page when filters change
	}

	// Handle sorting
	const handleSort = (field: SortField) => {
		if (sortField === field) {
			// Toggle direction if same field
			setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
		} else {
			// Set new field with default direction
			setSortField(field)
			setSortDirection('asc')
		}
		setCurrentPage(1) // Reset to first page when sorting changes
	}

	// Get sort icon for a column
	const getSortIcon = (field: SortField) => {
		if (sortField !== field) {
			return <ChevronsUpDown className="w-4 h-4" />
		}
		return sortDirection === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
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
			const response = await transactionAPI.updateCategory(
				id,
				editCategory,
				editSubcategory || undefined
			)
			
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

	// Bulk selection helpers
	const isAllSelected = transactions.length > 0 && transactions.every(t => selectedIds.has(t.id))
	const toggleSelectAll = () => {
		if (isAllSelected) {
			setSelectedIds(new Set())
		} else {
			setSelectedIds(new Set(transactions.map(t => t.id)))
		}
	}
	const toggleSelectRow = (id: number) => {
		setSelectedIds(prev => {
			const next = new Set(prev)
			if (next.has(id)) next.delete(id)
			else next.add(id)
			return next
		})
	}
	const selectSimilarByVendor = (vendor?: string) => {
		if (!vendor) return
		setSelectedIds(prev => {
			const next = new Set(prev)
			transactions.forEach(t => {
				if ((t.vendor || '').toLowerCase() === vendor.toLowerCase()) next.add(t.id)
			})
			return next
		})
	}

	// Bulk apply categorization using new API
	const applyBulkCategorization = async () => {
		if (selectedIds.size === 0) {
			setBulkMessage('Please select at least one transaction')
			return
		}
		
		// Check transaction limit (backend allows max 1000)
		if (selectedIds.size > 1000) {
			setBulkMessage('Maximum 1000 transactions can be categorized at once. Please select fewer transactions.')
			return
		}
		
		setBulkMessage(null)
		setIsApplyingBulk(true)
		
		try {
			// Use new bulk operations API
			const response = await bulkOperationsAPI.categorize(
				Array.from(selectedIds),
				bulkCategory || 'Uncategorized',
				bulkSubcategory
			)
			
			const result = response.data
			
			// Display detailed results from new API
			setBulkMessage(
				`Bulk categorization completed: ${result.successful_operations} of ${result.total_transactions} transactions categorized. ` +
				`Failed: ${result.failed_operations}. Processing time: ${result.processing_time.toFixed(2)}s. ` +
				`${result.undo_available ? 'Undo available.' : ''}`
			)
			
			// Clear selection and refresh data
			setSelectedIds(new Set())
			setBulkCategory('')
			setBulkSubcategory('')
			fetchTransactions()
			
		} catch (error: any) {
			console.error('Bulk categorization failed:', error)
			
			if (error.response?.status === 429) {
				// Rate limit exceeded
				const retryAfter = error.response.data?.retry_after || 60
				setBulkMessage(`Rate limit exceeded. Please wait ${retryAfter} seconds before trying again.`)
			} else if (error.response?.status === 400) {
				// Bad request - show specific error
				setBulkMessage(`Bulk categorization failed: ${error.response.data?.detail || 'Invalid request'}`)
			} else {
				// Generic error
				setBulkMessage('Bulk categorization failed. Please try again.')
			}
		} finally {
			setIsApplyingBulk(false)
		}
	}

	const undoLastBulk = async () => {
		setIsApplyingBulk(true)
		try {
			const response = await bulkOperationsAPI.undo()
			const result = response.data
			
			setBulkMessage(
				`Undo completed: ${result.successful_operations} of ${result.total_transactions} operations undone. ` +
				`Failed: ${result.failed_operations}. Processing time: ${result.processing_time.toFixed(2)}s. ` +
				`${result.redo_available ? 'Redo available.' : ''}`
			)
			
			fetchTransactions()
		} catch (error: any) {
			console.error('Undo failed:', error)
			setBulkMessage('Undo failed. Please try again.')
		} finally {
			setIsApplyingBulk(false)
		}
	}

	const redoLastBulk = async () => {
		setIsApplyingBulk(true)
		try {
			const response = await bulkOperationsAPI.redo()
			const result = response.data
			
			setBulkMessage(
				`Redo completed: ${result.successful_operations} of ${result.total_transactions} operations redone. ` +
				`Failed: ${result.failed_operations}. Processing time: ${result.processing_time.toFixed(2)}s. ` +
				`${result.undo_available ? 'Undo available.' : ''}`
			)
			
			fetchTransactions()
		} catch (error: any) {
			console.error('Redo failed:', error)
			setBulkMessage('Redo failed. Please try again.')
		} finally {
			setIsApplyingBulk(false)
		}
	}

	// Get available subcategories based on selected category
	const availableSubcategories = useMemo(() => {
		if (!editCategory) return []
		return getSubcategories(editCategory)
	}, [editCategory, getSubcategories])

	if (isLoading) {
		return (
			<div className="animate-pulse therapeutic-transition">
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
			<div className="text-center py-8 therapeutic-transition">
				<p className="text-gray-500 mb-4">No transactions found</p>
				<p className="text-sm text-gray-400">
					Upload a CSV file to get started
				</p>
			</div>
		)
	}

	return (
		<div className="bg-white rounded-lg shadow therapeutic-transition">
			{/* Filters */}
			<TransactionFilters
				onFiltersChange={handleFiltersChange}
				categories={categories}
				subcategories={subcategories}
			/>

			{/* Bulk Actions Toolbar */}
			<div className="flex flex-wrap items-center justify-between gap-3 px-6 py-3 border-b border-gray-200 bg-gray-50">
				<div className="flex items-center gap-2">
					<button
						onClick={toggleSelectAll}
						className="px-2 py-1 text-sm rounded border border-gray-300 bg-white hover:bg-gray-100"
						aria-label={isAllSelected ? 'Deselect all' : 'Select all'}
					>
						{isAllSelected ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4" />}
					</button>
					<span className="text-sm text-gray-600">{selectedIds.size} selected</span>
				</div>

				<div className="flex items-center gap-2">
					{/* Bulk Categorization */}
					<div className="flex items-center gap-2">
						<ComboBox
							options={allCategories}
							value={bulkCategory}
							onChange={setBulkCategory}
							placeholder="Select category"
							className="w-32"
						/>
						<ComboBox
							options={getSubcategories(bulkCategory)}
							value={bulkSubcategory}
							onChange={setBulkSubcategory}
							placeholder="Select subcategory"
							className="w-32"
						/>
						<button
							onClick={applyBulkCategorization}
							disabled={isApplyingBulk || selectedIds.size === 0 || !bulkCategory}
							className="btn-primary disabled:opacity-50"
						>
							{isApplyingBulk ? 'Categorizing...' : `Categorize ${selectedIds.size} selected`}
						</button>
					</div>

					{/* Bulk Delete */}
					<button
						onClick={async () => {
							if (confirm(`Are you sure you want to delete ${selectedIds.size} selected transactions?`)) {
								setIsApplyingBulk(true)
								try {
									const response = await bulkOperationsAPI.delete(Array.from(selectedIds))
									const result = response.data
									setBulkMessage(
										`Bulk delete completed: ${result.successful_operations} of ${result.total_transactions} transactions deleted. ` +
										`Failed: ${result.failed_operations}. Processing time: ${result.processing_time.toFixed(2)}s. ` +
										`${result.undo_available ? 'Undo available.' : ''}`
									)
									setSelectedIds(new Set())
									fetchTransactions()
								} catch (error: any) {
									console.error('Bulk delete failed:', error)
									setBulkMessage('Bulk delete failed. Please try again.')
								} finally {
									setIsApplyingBulk(false)
								}
							}
						}}
						disabled={isApplyingBulk || selectedIds.size === 0}
						className="btn-danger disabled:opacity-50"
					>
						{isApplyingBulk ? 'Deleting...' : `Delete ${selectedIds.size} selected`}
					</button>

					{/* Undo/Redo */}
					<button
						onClick={undoLastBulk}
						disabled={isApplyingBulk}
						className="btn-secondary disabled:opacity-50"
					>
						Undo
					</button>
					<button
						onClick={redoLastBulk}
						disabled={isApplyingBulk}
						className="btn-secondary disabled:opacity-50"
					>
						Redo
					</button>

					{selectedIds.size > 1000 && (
						<span className="text-sm text-orange-600">
							⚠️ Max 1000 transactions
						</span>
					)}
				</div>
			</div>

			{/* Bulk message */}
			{bulkMessage && (
				<div className="px-6 py-2 bg-blue-50 border-b border-blue-200 text-sm text-blue-800">{bulkMessage}</div>
			)}

			{/* Table */}
			<div className="overflow-x-auto">
				<table className="min-w-full divide-y divide-gray-200">
					<thead className="bg-gray-50">
						<tr>
							<th className="px-3 py-3">
								<button
									onClick={toggleSelectAll}
									className="p-1 rounded hover:bg-gray-100"
									aria-label={isAllSelected ? 'Deselect all' : 'Select all'}
								>
									{isAllSelected ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4" />}
								</button>
							</th>
							<th 
								className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 therapeutic-transition"
								onClick={() => handleSort('date')}
							>
								<div className="flex items-center space-x-1">
									<span>Date</span>
									{getSortIcon('date')}
								</div>
							</th>
							<th 
								className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 therapeutic-transition"
								onClick={() => handleSort('description')}
							>
								<div className="flex items-center space-x-1">
									<span>Description</span>
									{getSortIcon('description')}
								</div>
							</th>
							<th 
								className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 therapeutic-transition"
								onClick={() => handleSort('vendor')}
							>
								<div className="flex items-center space-x-1">
									<span>Vendor</span>
									{getSortIcon('vendor')}
								</div>
							</th>
							<th 
								className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 therapeutic-transition"
								onClick={() => handleSort('amount')}
							>
								<div className="flex items-center space-x-1">
									<span>Amount</span>
									{getSortIcon('amount')}
								</div>
							</th>
							<th 
								className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 therapeutic-transition"
								onClick={() => handleSort('category')}
							>
								<div className="flex items-center space-x-1">
									<span>Category</span>
									{getSortIcon('category')}
								</div>
							</th>
							<th 
								className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 therapeutic-transition"
								onClick={() => handleSort('subcategory')}
							>
								<div className="flex items-center space-x-1">
									<span>Subcategory</span>
									{getSortIcon('subcategory')}
								</div>
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
								<td colSpan={9} className="px-6 py-4 text-center text-gray-500">
									Loading transactions...
								</td>
							</tr>
						) : transactions.length === 0 ? (
							<tr>
								<td colSpan={9} className="px-6 py-4 text-center text-gray-500">
									No transactions found
								</td>
							</tr>
						) : (
							transactions.map((transaction) => (
								<tr key={transaction.id} className="hover:bg-gray-50">
									<td className="px-3 py-4">
										<button
											onClick={() => toggleSelectRow(transaction.id)}
											className="p-1 rounded hover:bg-gray-100"
											aria-label={selectedIds.has(transaction.id) ? 'Deselect row' : 'Select row'}
										>
											{selectedIds.has(transaction.id) ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4" />}
										</button>
									</td>
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
									}`}
									>
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
											<div className="flex items-center space-x-2">
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
												<button
													onClick={() => selectSimilarByVendor(transaction.vendor)}
													title="Select similar by vendor"
													className="text-gray-600 hover:text-gray-900"
												>
													<ScanSearch className="w-4 h-4" />
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
				<div className="px-6 py-3 bg-blue-50 border-t border-blue-200 therapeutic-transition">
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
