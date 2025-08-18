import { useQuery } from '@tanstack/react-query'
import { transactionAPI } from '@/lib/api'

export function useTransactions(params?: {
  skip?: number
  limit?: number
  category?: string
  start_date?: string
  end_date?: string
  is_income?: boolean
}, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['transactions', params],
    queryFn: async () => {
      try {
        const response = await transactionAPI.getTransactions(params)
        return response.data
      } catch (error) {
        console.error('Error fetching transactions:', error)
        throw error
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false,
    refetchOnWindowFocus: false,
    enabled: options?.enabled !== false, // Default to true unless explicitly disabled
  })
}

export function useTransaction(id: number) {
  return useQuery({
    queryKey: ['transaction', id],
    queryFn: () => transactionAPI.getById(id),
    enabled: !!id,
  })
}
