/**
 * ErrorMessage Component Tests
 *
 * Testing Requirements:
 * 1. Renders error message correctly
 * 2. Calls onRetry when retry button clicked
 * 3. Calls onDismiss when dismiss button clicked
 * 4. Has proper accessibility role (alert)
 *
 * Design Philosophy: Rams Principle 6 - "Good design is honest"
 * Never hide errors, show clear, actionable information
 */

import { render, screen, fireEvent } from '@testing-library/react';
import ErrorMessage from '@/components/ErrorMessage';

describe('ErrorMessage', () => {
  test('renders error message correctly', () => {
    // Arrange
    const errorText = 'Failed to fetch papers from OpenAlex API. Check your internet connection.';

    // Act
    render(<ErrorMessage message={errorText} />);

    // Assert
    const messageElement = screen.getByText(errorText);
    expect(messageElement).toBeInTheDocument();
  });

  test('calls onRetry when retry button clicked', () => {
    // Arrange
    const mockRetry = jest.fn();
    const errorText = 'Network error occurred';

    // Act
    render(
      <ErrorMessage
        message={errorText}
        onRetry={mockRetry}
      />
    );

    const retryButton = screen.getByRole('button', { name: /retry/i });
    fireEvent.click(retryButton);

    // Assert
    expect(mockRetry).toHaveBeenCalledTimes(1);
  });

  test('calls onDismiss when dismiss button clicked', () => {
    // Arrange
    const mockDismiss = jest.fn();
    const errorText = 'Something went wrong';

    // Act
    render(
      <ErrorMessage
        message={errorText}
        onDismiss={mockDismiss}
      />
    );

    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    fireEvent.click(dismissButton);

    // Assert
    expect(mockDismiss).toHaveBeenCalledTimes(1);
  });

  test('has proper accessibility role', () => {
    // Arrange
    const errorText = 'Error message for screen readers';

    // Act
    render(<ErrorMessage message={errorText} />);

    // Assert
    const alertElement = screen.getByRole('alert');
    expect(alertElement).toBeInTheDocument();
    expect(alertElement).toHaveTextContent(errorText);
  });
});
