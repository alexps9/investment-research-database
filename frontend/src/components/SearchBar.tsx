/**
 * SearchBar Component
 *
 * Design Philosophy: Dieter Rams' Principle 3 - "Good design is aesthetic"
 * - Minimalist, industrial aesthetic
 * - Only essential elements
 * - Color only on interaction (orange focus state)
 *
 * Accessibility:
 * - Keyboard shortcuts (Cmd+K / Ctrl+K)
 * - ARIA labels
 * - Focus management
 */

'use client'

import { useState, useRef, useCallback } from 'react'
import { useKeyboardShortcut } from '@/hooks/useKeyboardShortcut'
import styles from './SearchBar.module.css'

export interface SearchBarProps {
  /** Callback when search is submitted */
  onSearch: (query: string) => void
  /** Initial query value */
  initialValue?: string
  /** Whether search is in progress */
  isLoading?: boolean
  /** Placeholder text (avoid if possible per Rams) */
  placeholder?: string
  /** Accessibility label */
  ariaLabel?: string
}

export default function SearchBar({
  onSearch,
  initialValue = '',
  isLoading = false,
  placeholder = '',
  ariaLabel = 'Search academic papers'
}: SearchBarProps) {
  const [query, setQuery] = useState(initialValue)
  const inputRef = useRef<HTMLInputElement>(null)

  // Keyboard shortcut: Cmd+K (Mac) or Ctrl+K (Windows/Linux)
  const focusInput = useCallback(() => {
    inputRef.current?.focus()
  }, [])

  useKeyboardShortcut({
    key: 'k',
    meta: true,
    ctrl: true,
    callback: focusInput
  })

  const handleSubmit = useCallback((event: React.FormEvent) => {
    event.preventDefault()

    // Validate non-empty query
    if (!query.trim()) {
      return
    }

    onSearch(query.trim())
  }, [query, onSearch])

  const handleChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(event.target.value)
  }, [])

  return (
    <form
      onSubmit={handleSubmit}
      className={styles.searchForm}
      role="search"
    >
      <label htmlFor="paper-search" className={styles.label}>
        搜索学术论文
      </label>

      <div className={styles.inputWrapper}>
        <input
          id="paper-search"
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleChange}
          className={styles.input}
          placeholder={placeholder}
          aria-label={ariaLabel}
          disabled={isLoading}
          autoComplete="off"
          spellCheck="false"
        />

        <button
          type="submit"
          className={styles.submitButton}
          disabled={isLoading || !query.trim()}
          aria-label="Search"
        >
          {isLoading ? '搜索中...' : '搜索'}
        </button>
      </div>
    </form>
  )
}
