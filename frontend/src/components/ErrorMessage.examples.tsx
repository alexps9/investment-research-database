/**
 * ErrorMessage Component - Usage Examples
 *
 * This file demonstrates how to use the ErrorMessage component
 * in various scenarios throughout the application.
 */

/* eslint-disable no-console */

import ErrorMessage from '@/components/ErrorMessage';

// Example 1: Basic error with retry
function ExampleWithRetry() {
  const handleRetry = () => {
    console.log('Retrying operation...');
    // Implement retry logic here
  };

  return (
    <ErrorMessage
      message="Failed to fetch papers from OpenAlex API. Check your internet connection."
      onRetry={handleRetry}
    />
  );
}

// Example 2: Error with dismiss
function ExampleWithDismiss() {
  const handleDismiss = () => {
    console.log('Error dismissed');
    // Clear error state
  };

  return (
    <ErrorMessage
      message="No results found for your query. Try different keywords."
      onDismiss={handleDismiss}
    />
  );
}

// Example 3: Error with both retry and dismiss
function ExampleWithBothActions() {
  const handleRetry = () => {
    console.log('Retrying...');
  };

  const handleDismiss = () => {
    console.log('Dismissed');
  };

  return (
    <ErrorMessage
      message="Network timeout occurred. The request took too long to complete."
      onRetry={handleRetry}
      onDismiss={handleDismiss}
    />
  );
}

// Example 4: Simple error message without actions
function ExampleSimple() {
  return (
    <ErrorMessage
      message="This feature is currently unavailable. Please try again later."
    />
  );
}

export {
  ExampleWithRetry,
  ExampleWithDismiss,
  ExampleWithBothActions,
  ExampleSimple,
};
