/**
 * Jest setup file for FinGood frontend testing.
 * Configures testing environment and global test utilities.
 */

import '@testing-library/jest-dom'

// Extend Jest matchers
import { toHaveNoViolations } from 'jest-axe'
expect.extend(toHaveNoViolations)

// Mock console methods to avoid noise in tests
global.console = {
  ...console,
  // Uncomment to ignore specific console methods
  // log: jest.fn(),
  // debug: jest.fn(),
  // info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
}

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock scrollTo
Object.defineProperty(window, 'scrollTo', {
  writable: true,
  value: jest.fn(),
})

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
})

// Mock fetch
global.fetch = jest.fn()

// Mock URL.createObjectURL
Object.defineProperty(URL, 'createObjectURL', {
  writable: true,
  value: jest.fn(() => 'mock-url'),
})

Object.defineProperty(URL, 'revokeObjectURL', {
  writable: true,
  value: jest.fn(),
})

// Mock File and FileList for file upload testing
global.File = class MockFile {
  constructor(parts: any[], filename: string, properties?: any) {
    return {
      name: filename,
      size: parts.reduce((acc, part) => acc + part.length, 0),
      type: properties?.type || '',
      lastModified: Date.now(),
      ...properties,
    } as File
  }
}

global.FileList = class MockFileList extends Array {
  item(index: number) {
    return this[index] || null
  }
}

// Setup cleanup after each test
afterEach(() => {
  // Clear all mocks
  jest.clearAllMocks()
  
  // Clear localStorage and sessionStorage
  localStorageMock.clear()
  sessionStorageMock.clear()
  
  // Reset fetch mock
  if (global.fetch) {
    (global.fetch as jest.Mock).mockReset()
  }
})

// Global test timeout
jest.setTimeout(10000)