import '@testing-library/jest-dom'

// Suppress console errors for act(...) warnings and expected test errors
const originalError = console.error
beforeAll(() => {
  console.error = (...args) => {
    // Suppress act(...) warnings
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: An update to') &&
      args[0].includes('inside a test was not wrapped in act(...)')
    ) {
      return
    }
    
    // Suppress expected test error messages from components
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Failed to fetch performance data:') ||
       args[0].includes('Auto-improvement failed:') ||
       args[0].includes('Feedback submission failed:'))
    ) {
      return
    }
    
    originalError.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
})

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
    }
  },
  usePathname() {
    return '/dashboard'
  },
  useSearchParams() {
    return new URLSearchParams()
  }
}))

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'

// Global test timeout
jest.setTimeout(10000)
