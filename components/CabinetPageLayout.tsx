'use client'

import React, { useState, useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { Home, ChevronRight, User, LogOut } from 'lucide-react'
import CabinetNavigation from './CabinetNavigation'
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar'
import { useAuth } from '../hooks/useAuth'

interface CabinetPageLayoutProps {
  children: React.ReactNode
  title?: string
  description?: string
}

export default function CabinetPageLayout({ 
  children, 
  title = "Cabinet",
  description = "AI Financial Therapy"
}: CabinetPageLayoutProps) {
  const router = useRouter()
  const pathname = usePathname()
  const { user, logout } = useAuth()
  const [activeSection, setActiveSection] = useState('dashboard')
  const [showUserProfile, setShowUserProfile] = useState(false)

  // Determine active section based on current pathname
  useEffect(() => {
    const path = pathname.split('/').pop() || 'dashboard'
    setActiveSection(path)
  }, [pathname])

  const handleSectionChange = (section: string) => {
    setActiveSection(section)
    router.push(`/cabinet/${section}`)
  }

  const handleUserProfileClick = () => {
    router.push('/cabinet/settings')
  }

  const handleLogout = async () => {
    try {
      await logout()
      router.push('/')
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  return (
    <div className="h-screen bg-white flex flex-col">
      {/* Full-width Header Bar */}
      <header className="flex items-center h-16 bg-brand-primary-dark border-b border-brand-primary shadow-lg">
        {/* Logo */}
        <div className="w-64 flex items-center px-4">
          <img 
            src="http://localhost:3000/logo.png" 
            alt="Spend's Analysis Logo" 
            className="h-12 w-auto rounded-lg shadow-lg"
          />
        </div>

        {/* Breadcrumb - positioned to align with main content */}
        <div className="flex-1">
          <nav className="flex px-6 max-w-6xl mx-auto" aria-label="Breadcrumb">
            <ol className="flex items-center space-x-2 text-sm ml-8">
              <li>
                <a href="/" className="text-gray-300 hover:text-white transition-colors">
                  <Home className="w-4 h-4" />
                </a>
              </li>
              <ChevronRight className="w-4 h-4 text-gray-400" />
              <li className="text-gray-300">Cabinet</li>
              <ChevronRight className="w-4 h-4 text-gray-400" />
              <li className="text-white font-medium">{title}</li>
            </ol>
          </nav>
        </div>

        {/* User Profile */}
        <div className="flex items-center px-4">
          <div className="flex items-center">
            <button
              onClick={handleUserProfileClick}
              className="flex items-center hover:bg-brand-primary rounded-lg p-2 transition-colors"
              title="View Profile"
            >
              {user?.email === 'demo@fingood.com' || user?.email === 'sigmund@spendsanalysis.com' ? (
                <DrSigmundSpendAvatar 
                  size="sm" 
                  showMessage={false}
                  animated={false}
                  className="flex-shrink-0"
                />
              ) : (
                <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-gray-600" />
                </div>
              )}
              <div className="ml-3">
                <p className="text-sm font-medium text-white">{user?.full_name || 'Demo User'}</p>
                <p className="text-xs text-gray-300">{user?.email || 'demo@fingood.com'}</p>
              </div>
            </button>
            <button
              onClick={handleLogout}
              className="ml-4 p-2 rounded-md text-gray-300 hover:text-white hover:bg-brand-primary transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Layout: Navigation + Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Navigation Sidebar */}
        <div className="w-64 flex-shrink-0">
          <CabinetNavigation 
            activeSection={activeSection} 
            onSectionChange={handleSectionChange}
          />
        </div>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto -mt-4 pt-8">
          {children}
        </main>
      </div>
    </div>
  )
}
