'use client'

import React, { useState } from 'react'
import CabinetPageLayout from '../../../components/CabinetPageLayout'
import { User, Bell, Shield, Palette, Database, Globe } from 'lucide-react'

export default function SettingsPage() {
  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    weekly: true,
    monthly: true
  })

  const [theme, setTheme] = useState('light')

  return (
    <CabinetPageLayout title="Settings" description="Manage your account preferences and settings">
      <div className="space-y-4">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <div className="mb-3">
            <h2 className="text-base font-semibold text-gray-900 mb-1">Settings</h2>
            <p className="text-xs text-gray-600">
              Manage your account preferences and settings
            </p>
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Profile Settings */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
            <div className="flex items-center mb-3">
              <User className="w-4 h-4 text-brand-primary mr-2" />
              <h3 className="text-sm font-medium text-gray-900">Profile</h3>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  defaultValue="demo@spendsanalysis.com"
                  className="w-full px-2 py-1 text-xs border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-primary focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Display Name
                </label>
                <input
                  type="text"
                  defaultValue="Demo User"
                  className="w-full px-2 py-1 text-xs border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-primary focus:border-transparent"
                />
              </div>
              
              <button className="w-full px-3 py-2 text-xs bg-brand-gradient text-white rounded-lg hover:shadow-lg transition-all">
                Update Profile
              </button>
            </div>
          </div>
          
          {/* Notification Settings */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
            <div className="flex items-center mb-3">
              <Bell className="w-4 h-4 text-emerald-600 mr-2" />
              <h3 className="text-sm font-medium text-gray-900">Notifications</h3>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-900">Email Notifications</p>
                  <p className="text-xs text-gray-500">Receive updates via email</p>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.email}
                  onChange={(e) => setNotifications(prev => ({ ...prev, email: e.target.checked }))}
                  className="rounded border-gray-300 text-brand-primary focus:ring-brand-primary"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-900">Push Notifications</p>
                  <p className="text-xs text-gray-500">Browser push notifications</p>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.push}
                  onChange={(e) => setNotifications(prev => ({ ...prev, push: e.target.checked }))}
                  className="rounded border-gray-300 text-brand-primary focus:ring-brand-primary"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-900">Weekly Reports</p>
                  <p className="text-xs text-gray-500">Weekly financial summaries</p>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.weekly}
                  onChange={(e) => setNotifications(prev => ({ ...prev, weekly: e.target.checked }))}
                  className="rounded border-gray-300 text-brand-primary focus:ring-brand-primary"
                />
              </div>
            </div>
          </div>
          
          {/* Security Settings */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
            <div className="flex items-center mb-3">
              <Shield className="w-4 h-4 text-red-600 mr-2" />
              <h3 className="text-sm font-medium text-gray-900">Security</h3>
            </div>
            
            <div className="space-y-3">
              <button className="w-full px-3 py-2 text-xs border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                Change Password
              </button>
              
              <button className="w-full px-3 py-2 text-xs border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                Two-Factor Authentication
              </button>
              
              <button className="w-full px-3 py-2 text-xs border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                Session Management
              </button>
            </div>
          </div>
          
          {/* Appearance Settings */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
            <div className="flex items-center mb-3">
              <Palette className="w-4 h-4 text-purple-600 mr-2" />
              <h3 className="text-sm font-medium text-gray-900">Appearance</h3>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Theme
                </label>
                <select
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  className="w-full px-2 py-1 text-xs border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-primary focus:border-transparent"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="auto">Auto</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Currency
                </label>
                <select className="w-full px-2 py-1 text-xs border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-primary focus:border-transparent">
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                  <option value="GBP">GBP (£)</option>
                </select>
              </div>
            </div>
          </div>
          
          {/* Data Management */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
            <div className="flex items-center mb-3">
              <Database className="w-4 h-4 text-brand-primary mr-2" />
              <h3 className="text-sm font-medium text-gray-900">Data Management</h3>
            </div>
            
            <div className="space-y-3">
              <button className="w-full px-3 py-2 text-xs border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                Export Data
              </button>
              
              <button className="w-full px-3 py-2 text-xs border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                Import Data
              </button>
              
              <button className="w-full px-3 py-2 text-xs border border-red-300 text-red-700 rounded-lg hover:bg-red-50 transition-colors">
                Delete Account
              </button>
            </div>
          </div>
          
          {/* API Settings */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
            <div className="flex items-center mb-3">
              <Globe className="w-4 h-4 text-brand-primary mr-2" />
              <h3 className="text-sm font-medium text-gray-900">API & Integrations</h3>
            </div>
            
            <div className="space-y-3">
              <button className="w-full px-3 py-2 text-xs border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                API Keys
              </button>
              
              <button className="w-full px-3 py-2 text-xs border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                Webhooks
              </button>
              
              <button className="w-full px-3 py-2 text-xs border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                Third-party Integrations
              </button>
            </div>
          </div>
        </div>
      </div>
    </CabinetPageLayout>
  )
}