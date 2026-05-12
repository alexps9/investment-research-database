/**
 * useKeyboardShortcut Hook
 *
 * Handles keyboard shortcuts for enhanced UX
 * Follows Rams Principle 1: Good design is innovative
 */

import { useEffect } from 'react'

interface KeyboardShortcutOptions {
  key: string
  meta?: boolean
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  callback: () => void
}

/**
 * Custom hook for keyboard shortcuts
 * Supports combining modifiers with OR logic (e.g., meta OR ctrl)
 *
 * @param options - Keyboard shortcut configuration
 *
 * @example
 * // Cmd+K (Mac) or Ctrl+K (Windows/Linux)
 * useKeyboardShortcut({
 *   key: 'k',
 *   meta: true,
 *   ctrl: true,
 *   callback: () => inputRef.current?.focus()
 * })
 */
export function useKeyboardShortcut({
  key,
  meta = false,
  ctrl = false,
  shift = false,
  alt = false,
  callback
}: KeyboardShortcutOptions) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check if key matches
      const keyMatch = event.key.toLowerCase() === key.toLowerCase()
      if (!keyMatch) return

      // If meta OR ctrl is specified, accept either
      const hasMetaOrCtrl = meta || ctrl
      const metaOrCtrlMatch = hasMetaOrCtrl
        ? (event.metaKey || event.ctrlKey)
        : true

      // Check exact matches for shift and alt
      const shiftMatch = shift ? event.shiftKey : !event.shiftKey
      const altMatch = alt ? event.altKey : !event.altKey

      if (metaOrCtrlMatch && shiftMatch && altMatch) {
        event.preventDefault()
        callback()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [key, meta, ctrl, shift, alt, callback])
}
