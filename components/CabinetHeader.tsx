'use client'

import React from 'react'
import Breadcrumbs from './Breadcrumbs'
import { useAuth } from '../hooks/useAuth'
import DrSigmundSpendAvatar from './DrSigmundSpendAvatar'
import { LogOut } from 'lucide-react'

interface CabinetHeaderProps {
  title: string
  description?: string
  onUserProfileClick?: () => void
  onLogout?: () => void
  user?: any
}

export default function CabinetHeader({ 
  title, 
  description, 
  onUserProfileClick, 
  onLogout,
  user: propUser 
}: CabinetHeaderProps) {
  const { user: authUser, logout: authLogout } = useAuth()
  
  // Use prop user if provided, otherwise use auth user
  const user = propUser || authUser

  const handleLogout = async () => {
    if (onLogout) {
      onLogout()
    } else {
      try {
        await authLogout()
        // Redirect to home page after successful logout
        window.location.href = '/'
      } catch (error) {
        console.error('Logout failed:', error)
        // Still redirect to home even if logout API call fails
        window.location.href = '/'
      }
    }
  }
  return (
    <div className="flex-shrink-0 bg-brand-primary-dark border-b border-brand-primary shadow-sm">
      <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
        {/* Logo and Breadcrumbs */}
        <div className="flex items-center space-x-4">
          {/* Logo */}
          <div className="flex-shrink-0">
            <img 
              src="/logo.png" 
              alt="Spend's Analysis - AI Financial Therapy" 
              className="h-8 w-auto rounded-lg"
              onError={(e) => {
                // Fallback to original design if logo doesn't load
                e.currentTarget.style.display = 'none';
                const fallback = e.currentTarget.nextElementSibling as HTMLElement;
                if (fallback) fallback.style.display = 'flex';
              }}
            />
            <div className="w-8 h-8 bg-gradient-to-br from-brand-primary to-brand-primary-light rounded-lg flex items-center justify-center shadow-lg hidden">
              <span className="text-white font-bold text-sm">S</span>
            </div>
          </div>
          
          {/* Breadcrumbs */}
          <Breadcrumbs />
        </div>
        
        {/* Right side actions */}
        <div className="flex items-center space-x-4">
          {/* User Info */}
          <button
            onClick={onUserProfileClick}
            className="flex items-center space-x-3 group rounded-lg p-2 transition-colors hover:bg-gray-700/50"
          >
            <DrSigmundSpendAvatar 
              size="sm" 
              mood="analytical"
              showMessage={false}
              className="group-hover:scale-110 transition-transform duration-300"
            />
            <div className="text-left">
              <p className="text-sm font-medium text-white group-hover:text-brand-secondary-light transition-colors">
                {user?.full_name || user?.email?.split('@')[0] || 'Guest User'}
              </p>
              <p className="text-xs text-gray-300 group-hover:text-brand-secondary-light/80 transition-colors">
                {user?.email || 'Not authenticated'}
              </p>
            </div>
          </button>
          
          {/* Logout */}
          <button
            onClick={handleLogout}
            className="p-2 text-gray-400 hover:text-brand-secondary-light hover:bg-gray-700 rounded-lg transition-colors"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
