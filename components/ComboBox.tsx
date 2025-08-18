'use client'

import { useState, useRef, useEffect } from 'react'
import { ChevronDown, Check } from 'lucide-react'

interface ComboBoxProps {
  options: string[]
  value: string
  onChange: (value: string) => void
  placeholder?: string
  allowCustom?: boolean
  className?: string
  disabled?: boolean
}

export function ComboBox({ 
  options, 
  value, 
  onChange, 
  placeholder = "Select...", 
  allowCustom = true,
  className = "",
  disabled = false
}: ComboBoxProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [inputValue, setInputValue] = useState(value)
  const [filteredOptions, setFilteredOptions] = useState(options)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setInputValue(value)
  }, [value])

  useEffect(() => {
    const filtered = options.filter(option =>
      option.toLowerCase().includes(inputValue.toLowerCase())
    )
    setFilteredOptions(filtered)
  }, [inputValue, options])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return
    const newValue = e.target.value
    setInputValue(newValue)
    setIsOpen(true)
  }

  const handleOptionSelect = (option: string) => {
    if (disabled) return
    setInputValue(option)
    onChange(option)
    setIsOpen(false)
  }

  const handleInputBlur = () => {
    // Small delay to allow option selection to complete
    setTimeout(() => {
      if (allowCustom && inputValue && !options.includes(inputValue)) {
        onChange(inputValue)
      }
      setIsOpen(false)
    }, 150)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return
    if (e.key === 'Enter') {
      if (allowCustom && inputValue && !options.includes(inputValue)) {
        onChange(inputValue)
      }
      setIsOpen(false)
    } else if (e.key === 'Escape') {
      setIsOpen(false)
    }
  }

  const handleToggleDropdown = () => {
    if (disabled) return
    setIsOpen(!isOpen)
  }

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <div className="relative">
        <input
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={() => !disabled && setIsOpen(true)}
          onBlur={handleInputBlur}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className={`w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm ${
            disabled 
              ? 'bg-gray-100 text-gray-500 cursor-not-allowed' 
              : 'bg-white text-gray-900'
          }`}
        />
        <button
          type="button"
          onClick={handleToggleDropdown}
          disabled={disabled}
          className={`absolute inset-y-0 right-0 flex items-center pr-2 ${
            disabled ? 'cursor-not-allowed' : 'cursor-pointer'
          }`}
        >
          <ChevronDown className={`w-4 h-4 transition-transform ${
            disabled 
              ? 'text-gray-400' 
              : isOpen 
                ? 'text-primary-600 rotate-180' 
                : 'text-gray-400'
          }`} />
        </button>
      </div>
      
      {isOpen && !disabled && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-auto">
          {filteredOptions.length > 0 ? (
            <ul className="py-1">
              {filteredOptions.map((option, index) => (
                <li
                  key={index}
                  onClick={() => handleOptionSelect(option)}
                  className={`px-3 py-2 cursor-pointer hover:bg-gray-100 flex items-center justify-between ${
                    option === value ? 'bg-primary-50 text-primary-700' : 'text-gray-900'
                  }`}
                >
                  <span>{option}</span>
                  {option === value && <Check className="w-4 h-4 text-primary-600" />}
                </li>
              ))}
            </ul>
          ) : (
            <div className="px-3 py-2 text-gray-500 text-sm">
              No options found
            </div>
          )}
          
          {allowCustom && inputValue && !options.includes(inputValue) && (
            <div className="border-t border-gray-200">
              <div
                onClick={() => handleOptionSelect(inputValue)}
                className="px-3 py-2 cursor-pointer hover:bg-gray-100 text-primary-600 text-sm"
              >
                Add "{inputValue}"
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
