import { useQuery } from '@tanstack/react-query'
import { transactionAPI } from '@/lib/api'

export interface AvailableCategories {
  categories: Record<string, string[]>
  total_categories: number
}

export function useCategories() {
  return useQuery<AvailableCategories>({
    queryKey: ['categories', 'available'],
    queryFn: async () => {
      const response = await transactionAPI.getAvailableCategories()
      return response.data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  })
}

export function useCategoryOptions() {
  const { data, isLoading, error } = useCategories()
  
  const categoryOptions = data?.categories ? Object.keys(data.categories) : []
  
  const getSubcategoryOptions = (category: string) => {
    return data?.categories[category] || []
  }
  
  return {
    categories: categoryOptions,
    getSubcategories: getSubcategoryOptions,
    isLoading,
    error,
    data
  }
}
