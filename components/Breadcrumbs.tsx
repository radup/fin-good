'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ChevronRight, Home } from 'lucide-react'

interface BreadcrumbsProps {
  className?: string
}

interface BreadcrumbItem {
  name: string
  href: string
  current: boolean
}

export default function Breadcrumbs({ className = '' }: BreadcrumbsProps) {
  const pathname = usePathname()

  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    const segments = pathname.split('/').filter(Boolean)
    const breadcrumbs: BreadcrumbItem[] = []

    // Always add home
    breadcrumbs.push({
      name: 'Home',
      href: '/',
      current: segments.length === 0
    })

    // Build breadcrumbs from path segments
    let currentPath = ''
    segments.forEach((segment, index) => {
      currentPath += `/${segment}`
      
      // Convert segment to readable name
      const name = segment
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')

      breadcrumbs.push({
        name,
        href: currentPath,
        current: index === segments.length - 1
      })
    })

    return breadcrumbs
  }

  const breadcrumbs = generateBreadcrumbs()

  if (breadcrumbs.length <= 1) {
    return null
  }

  return (
    <nav className={`flex ${className}`} aria-label="Breadcrumb">
      <ol className="flex items-center space-x-2">
        {breadcrumbs.map((item, index) => (
          <li key={item.href} className="flex items-center">
            {index > 0 && (
              <ChevronRight className="w-4 h-4 text-gray-400 mx-2" />
            )}
            
            {item.current ? (
              <span className="text-sm font-medium text-gray-300">
                {item.name === 'Home' ? (
                  <Home className="w-4 h-4" />
                ) : (
                  item.name
                )}
              </span>
            ) : (
              <Link
                href={item.href}
                className="text-sm font-medium text-gray-400 hover:text-white transition-colors flex items-center"
              >
                {item.name === 'Home' ? (
                  <Home className="w-4 h-4" />
                ) : (
                  item.name
                )}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}
