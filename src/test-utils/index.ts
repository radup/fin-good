/**
 * Test utilities for FinGood frontend testing.
 * Provides custom render functions, mocks, and test helpers.
 */

import React, { ReactElement } from 'react'
import { render, RenderOptions, RenderResult } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import userEvent from '@testing-library/user-event'
import { faker } from '@faker-js/faker'

// ================================
// TEST PROVIDERS
// ================================

interface TestProvidersProps {
  children: React.ReactNode
  queryClient?: QueryClient
}

const TestProviders: React.FC<TestProvidersProps> = ({ 
  children, 
  queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })
}) => {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

// ================================
// CUSTOM RENDER FUNCTIONS
// ================================

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient
  initialEntries?: string[]
}

/**
 * Custom render function with all providers
 */
export const renderWithProviders = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
): RenderResult & { user: ReturnType<typeof userEvent.setup> } => {
  const { queryClient, ...renderOptions } = options

  const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <TestProviders queryClient={queryClient}>
      {children}
    </TestProviders>
  )

  const user = userEvent.setup()

  return {
    user,
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
  }
}

/**
 * Simplified render for components that don't need providers
 */
export const renderComponent = (ui: ReactElement, options?: RenderOptions) => {
  const user = userEvent.setup()
  return {
    user,
    ...render(ui, options),
  }
}

// ================================
// MOCK DATA GENERATORS
// ================================

export const mockUser = {
  id: 1,
  email: 'test@example.com',
  first_name: 'John',
  last_name: 'Doe',
  is_active: true,
  is_admin: false,
  created_at: '2024-01-01T00:00:00Z',
}

export const mockAdminUser = {
  ...mockUser,
  id: 2,
  email: 'admin@example.com',
  is_admin: true,
}

export const generateMockTransaction = (overrides: Partial<any> = {}) => ({
  id: faker.number.int({ min: 1, max: 10000 }),
  date: faker.date.recent().toISOString().split('T')[0],
  description: faker.lorem.sentence({ min: 2, max: 6 }),
  amount: parseFloat(faker.finance.amount({ min: -1000, max: 1000, dec: 2 })),
  category: faker.helpers.arrayElement([
    'Food & Dining',
    'Transportation',
    'Shopping',
    'Entertainment',
    'Bills & Utilities',
    'Income',
    'Healthcare',
    'Travel'
  ]),
  account: faker.helpers.arrayElement([
    'Checking',
    'Savings',
    'Credit Card',
    'Debit Card'
  ]),
  created_at: faker.date.recent().toISOString(),
  user_id: 1,
  ...overrides,
})

export const generateMockTransactions = (count: number = 10, overrides: Partial<any> = {}) => 
  Array.from({ length: count }, () => generateMockTransaction(overrides))

export const generateMockCategories = () => [
  { name: 'Food & Dining', count: 25, total: -1250.50 },
  { name: 'Transportation', count: 12, total: -450.25 },
  { name: 'Shopping', count: 8, total: -320.75 },
  { name: 'Entertainment', count: 5, total: -125.00 },
  { name: 'Bills & Utilities', count: 15, total: -890.30 },
  { name: 'Income', count: 4, total: 3500.00 },
]

export const generateMockAnalytics = () => ({
  total_income: 5000.00,
  total_expenses: -3250.75,
  net_income: 1749.25,
  transaction_count: 69,
  categories: generateMockCategories(),
  monthly_trends: [
    { month: '2024-01', income: 5000, expenses: -3000, net: 2000 },
    { month: '2024-02', income: 5200, expenses: -3200, net: 2000 },
    { month: '2024-03', income: 4800, expenses: -3100, net: 1700 },
  ]
})

// ================================
// API MOCK HELPERS
// ================================

export const mockApiResponse = <T>(data: T, status: number = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => data,
  headers: new Headers({ 'content-type': 'application/json' }),
})

export const mockApiError = (message: string, status: number = 400) => 
  mockApiResponse({ detail: message }, status)

export const mockPaginatedResponse = <T>(
  items: T[], 
  page: number = 1, 
  size: number = 20,
  total?: number
) => ({
  items,
  total: total ?? items.length,
  page,
  size,
  pages: Math.ceil((total ?? items.length) / size),
})

// ================================
// FORM TESTING HELPERS
// ================================

export const fillForm = async (
  user: ReturnType<typeof userEvent.setup>,
  formData: Record<string, string>
) => {
  for (const [field, value] of Object.entries(formData)) {
    const input = document.querySelector(`[name="${field}"]`) as HTMLInputElement
    if (input) {
      await user.clear(input)
      await user.type(input, value)
    }
  }
}

export const submitForm = async (
  user: ReturnType<typeof userEvent.setup>,
  formSelector: string = 'form'
) => {
  const form = document.querySelector(formSelector)
  if (form) {
    const submitButton = form.querySelector('[type="submit"]') as HTMLButtonElement
    if (submitButton) {
      await user.click(submitButton)
    }
  }
}

// ================================
// FILE UPLOAD HELPERS
// ================================

export const createMockFile = (
  name: string = 'test.csv',
  content: string = 'Date,Description,Amount\n2024-01-01,Test,-10.00',
  type: string = 'text/csv'
): File => {
  const file = new File([content], name, { type })
  return file
}

export const createMockFileList = (files: File[]): FileList => {
  const fileList = {
    length: files.length,
    item: (index: number) => files[index] || null,
    [Symbol.iterator]: function* () {
      for (let i = 0; i < files.length; i++) {
        yield files[i]
      }
    },
  }
  
  // Add files as indexed properties
  files.forEach((file, index) => {
    (fileList as any)[index] = file
  })
  
  return fileList as FileList
}

export const uploadFile = async (
  user: ReturnType<typeof userEvent.setup>,
  inputSelector: string,
  files: File | File[]
) => {
  const fileInput = document.querySelector(inputSelector) as HTMLInputElement
  const fileArray = Array.isArray(files) ? files : [files]
  const fileList = createMockFileList(fileArray)
  
  Object.defineProperty(fileInput, 'files', {
    value: fileList,
    writable: false,
  })
  
  await user.upload(fileInput, fileArray)
}

// ================================
// ACCESSIBILITY TESTING HELPERS
// ================================

export const runAxeTest = async (container: HTMLElement) => {
  const { axe } = await import('jest-axe')
  const results = await axe(container)
  expect(results).toHaveNoViolations()
}

// ================================
// ASYNC TESTING HELPERS
// ================================

export const waitForLoadingToFinish = async () => {
  const { waitFor } = await import('@testing-library/react')
  await waitFor(() => {
    expect(document.querySelector('[data-testid="loading"]')).not.toBeInTheDocument()
  })
}

export const waitForErrorToAppear = async (errorMessage: string) => {
  const { waitFor, screen } = await import('@testing-library/react')
  await waitFor(() => {
    expect(screen.getByText(errorMessage)).toBeInTheDocument()
  })
}

// ================================
// MOCK IMPLEMENTATIONS
// ================================

export const mockLocalStorage = () => {
  const storage: Record<string, string> = {}
  
  return {
    getItem: jest.fn((key: string) => storage[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      storage[key] = value
    }),
    removeItem: jest.fn((key: string) => {
      delete storage[key]
    }),
    clear: jest.fn(() => {
      Object.keys(storage).forEach(key => delete storage[key])
    }),
  }
}

export const mockIntersectionObserver = () => {
  const mockObserver = {
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
  }
  
  window.IntersectionObserver = jest.fn().mockImplementation(() => mockObserver)
  
  return mockObserver
}

// ================================
// CUSTOM MATCHERS
// ================================

declare global {
  namespace jest {
    interface Matchers<R> {
      toHaveNoViolations(): R
    }
  }
}

// Re-export commonly used testing utilities
export { screen, waitFor, within, fireEvent } from '@testing-library/react'
export { default as userEvent } from '@testing-library/user-event'
export { faker }