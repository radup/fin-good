import { useQuery } from '@tanstack/react-query'
import { analyticsAPI } from '@/lib/api'

export function useAnalytics(params?: {
  start_date?: string
  end_date?: string
}, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['analytics', 'summary', params],
    queryFn: async () => {
      try {
        const response = await analyticsAPI.summary(params)
        return response.data
      } catch (error) {
        console.error('Error fetching analytics:', error)
        throw error
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false,
    refetchOnWindowFocus: false,
    enabled: options?.enabled !== false, // Default to true unless explicitly disabled
  })
}

export function useMonthlyAnalytics(year: number) {
  return useQuery({
    queryKey: ['analytics', 'monthly', year],
    queryFn: () => analyticsAPI.monthly(year),
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

export function useTopCategories(params?: {
  limit?: number
  start_date?: string
  end_date?: string
}) {
  return useQuery({
    queryKey: ['analytics', 'top-categories', params],
    queryFn: () => analyticsAPI.topCategories(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}
