'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { useState, useEffect, createContext, useContext } from 'react'
import { AuthErrorBoundary, recoveryUtils } from '@/components/ErrorBoundary'
import { useAuth } from '@/hooks/useAuth'
import { setGlobalCsrfToken } from '@/lib/api'

// Create context for auth state to be accessed throughout the app
const AuthContext = createContext<ReturnType<typeof useAuth> | null>(null)

export const useAuthContext = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuthContext must be used within AuthProvider')
  }
  return context
}

function AuthProvider({ children }: { children: React.ReactNode }) {
  const auth = useAuth()

  // Sync CSRF token with global API state whenever it changes
  useEffect(() => {
    if (auth.csrfToken) {
      setGlobalCsrfToken(auth.csrfToken)
    } else {
      setGlobalCsrfToken(null)
    }
  }, [auth.csrfToken])

  return (
    <AuthContext.Provider value={auth}>
      {children}
    </AuthContext.Provider>
  )
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            retry: 1,
          },
        },
      })
  )

  const handleAuthFailure = () => {
    console.log('Authentication failed in providers - preserving context')
    // Clear CSRF token on auth failure
    setGlobalCsrfToken(null)
    // The AuthErrorBoundary will handle the actual redirection and context preservation
  }

  return (
    <AuthErrorBoundary onAuthFailure={handleAuthFailure}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          {children}
        </AuthProvider>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </AuthErrorBoundary>
  )
}