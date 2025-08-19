import { useQuery } from '@tanstack/react-query'
import { analyticsAPI, enhancedAnalyticsAPI } from '@/lib/api'

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

// Enhanced Analytics Hooks

export function useCashFlowAnalysis(params?: {
  start_date?: string
  end_date?: string
  group_by?: string
}) {
  return useQuery({
    queryKey: ['analytics', 'cash-flow', params],
    queryFn: async () => {
      const response = await enhancedAnalyticsAPI.getCashFlowAnalysis(params)
      return response.data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  })
}

export function useCategoryInsights(params?: {
  start_date?: string
  end_date?: string
  category?: string
}) {
  return useQuery({
    queryKey: ['analytics', 'category-insights', params],
    queryFn: async () => {
      const response = await enhancedAnalyticsAPI.getCategoryInsights(params)
      return response.data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  })
}

export function useVendorAnalysis(params?: {
  start_date?: string
  end_date?: string
  vendor?: string
}) {
  return useQuery({
    queryKey: ['analytics', 'vendor-analysis', params],
    queryFn: async () => {
      const response = await enhancedAnalyticsAPI.getVendorAnalysis(params)
      return response.data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  })
}

export function useAnomalyDetection(params?: {
  start_date?: string
  end_date?: string
  threshold?: number
}) {
  return useQuery({
    queryKey: ['analytics', 'anomaly-detection', params],
    queryFn: async () => {
      const response = await enhancedAnalyticsAPI.getAnomalyDetection(params)
      return response.data
    },
    staleTime: 2 * 60 * 1000, // 2 minutes (anomalies can change quickly)
    retry: 2,
  })
}

export function useComparativeAnalysis(params: {
  period1_start: string
  period1_end: string
  period2_start: string
  period2_end: string
  metric?: string
}) {
  return useQuery({
    queryKey: ['analytics', 'comparative', params],
    queryFn: async () => {
      const response = await enhancedAnalyticsAPI.getComparativeAnalysis(params)
      return response.data
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 2,
  })
}

export function useTrendAnalysis(params?: {
  start_date?: string
  end_date?: string
  metric?: string
  period_type?: string
}) {
  return useQuery({
    queryKey: ['analytics', 'trend-analysis', params],
    queryFn: async () => {
      const response = await enhancedAnalyticsAPI.getTrendAnalysis(params)
      return response.data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  })
}

export function useDashboardData(params?: {
  start_date?: string
  end_date?: string
}) {
  return useQuery({
    queryKey: ['analytics', 'dashboard', params],
    queryFn: async () => {
      const response = await enhancedAnalyticsAPI.getDashboardData(params)
      return response.data
    },
    staleTime: 2 * 60 * 1000, // 2 minutes (dashboard should be fresh)
    retry: 2,
  })
}

// Combined Analytics Hook for Dashboard
export function useAnalyticsDashboard(params?: {
  start_date?: string
  end_date?: string
}) {
  const dashboardData = useDashboardData(params)
  const cashFlow = useCashFlowAnalysis(params)
  const categoryInsights = useCategoryInsights(params)
  const vendorAnalysis = useVendorAnalysis(params)
  const anomalyDetection = useAnomalyDetection(params)
  const trendAnalysis = useTrendAnalysis(params)

  return {
    dashboardData,
    cashFlow,
    categoryInsights,
    vendorAnalysis,
    anomalyDetection,
    trendAnalysis,
    isLoading: dashboardData.isLoading || cashFlow.isLoading || categoryInsights.isLoading || 
               vendorAnalysis.isLoading || anomalyDetection.isLoading || trendAnalysis.isLoading,
    error: dashboardData.error || cashFlow.error || categoryInsights.error || 
           vendorAnalysis.error || anomalyDetection.error || trendAnalysis.error,
  }
}
