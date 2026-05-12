import { render, screen } from '@testing-library/react';
import Loading from '@/components/Loading';

describe('Loading', () => {
  test('renders default loading message', () => {
    render(<Loading />);

    const message = screen.getByText('Loading...');
    expect(message).toBeInTheDocument();
  });

  test('renders custom message', () => {
    const customMessage = 'Fetching papers...';
    render(<Loading message={customMessage} />);

    const message = screen.getByText(customMessage);
    expect(message).toBeInTheDocument();
  });

  test('has proper accessibility attributes', () => {
    render(<Loading />);

    const loadingElement = screen.getByRole('status');
    expect(loadingElement).toBeInTheDocument();
    expect(loadingElement).toHaveAttribute('aria-live', 'polite');
  });
});
