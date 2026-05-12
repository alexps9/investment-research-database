import { render } from '@testing-library/react'
import RootLayout, { metadata } from '@/app/layout'

describe('RootLayout', () => {
  it('renders children correctly', () => {
    const { container } = render(
      <RootLayout>
        <div data-testid="child">Test Child</div>
      </RootLayout>
    )
    const child = container.querySelector('[data-testid="child"]')
    expect(child).toBeInTheDocument()
    expect(child?.textContent).toBe('Test Child')
  })

  it('sets html lang attribute to "en"', () => {
    const { container } = render(
      <RootLayout>
        <div />
      </RootLayout>
    )

    const htmlElement = container.querySelector('html')
    expect(htmlElement).toHaveAttribute('lang', 'en')
  })

  it('has correct metadata', () => {
    expect(metadata.title).toBe('Academic Paper Analysis')
    expect(metadata.description).toBe('Visualize academic paper citation networks')
  })

  it('renders body element with children', () => {
    const { container } = render(
      <RootLayout>
        <div data-testid="content">Page Content</div>
      </RootLayout>
    )

    const body = container.querySelector('body')
    expect(body).toBeInTheDocument()
    expect(body?.querySelector('[data-testid="content"]')).toBeInTheDocument()
  })
})
