/**
 * ErrorMessage Component
 *
 * Design Philosophy: Rams Principle 6 - "Good design is honest"
 * - Never hide errors
 * - Show clear, actionable information
 * - Provide users with ways to resolve issues (Retry/Dismiss)
 *
 * Accessibility:
 * - role="alert" for screen readers
 * - aria-live="assertive" for immediate announcements
 * - Semantic button elements
 * - Clear action labels with ARIA descriptions
 */

'use client';

import React, { useCallback } from 'react';
import styles from './ErrorMessage.module.css';

export interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export default function ErrorMessage({
  message,
  onRetry,
  onDismiss,
}: ErrorMessageProps) {
  // Memoize callbacks to prevent unnecessary re-renders
  const handleRetry = useCallback(() => {
    if (onRetry) {
      onRetry();
    }
  }, [onRetry]);

  const handleDismiss = useCallback(() => {
    if (onDismiss) {
      onDismiss();
    }
  }, [onDismiss]);

  return (
    <div
      className={styles.error}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <p className={styles.message}>{message}</p>

      <div className={styles.actions}>
        {onRetry && (
          <button
            className={styles.button}
            onClick={handleRetry}
            type="button"
            aria-label="重试操作"
          >
            重试
          </button>
        )}

        {onDismiss && (
          <button
            className={styles.buttonSecondary}
            onClick={handleDismiss}
            type="button"
            aria-label="关闭错误信息"
          >
            关闭
          </button>
        )}
      </div>
    </div>
  );
}
