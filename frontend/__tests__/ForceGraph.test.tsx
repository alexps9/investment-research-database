/**
 * ForceGraph Component Tests - TDD Approach
 *
 * Coverage Target: >= 80%
 *
 * Test Cases:
 * 1. Renders graph with correct node count
 * 2. Calls onNodeClick when node is clicked
 * 3. Renders empty graph when no data
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import ForceGraph from '@/components/ForceGraph'
import type { GraphResponse } from '@/types/api'

// ============================================================================
// Mock next/dynamic to return component synchronously (avoid SSR issues)
// ============================================================================
jest.mock('next/dynamic', () => ({
  __esModule: true,
  default: (fn: () => Promise<any>, options: any = {}) => {
    // For testing, just return the mocked component directly
    return jest.requireMock('react-force-graph-2d').default
  }
}))

// ============================================================================
// Mock react-force-graph-2d (CRITICAL for testing)
// ============================================================================
jest.mock('react-force-graph-2d', () => {
  const MockComponent = (props: any) => {
    // Test callback functions by calling them if nodes exist
    const testCallbacks = props.graphData.nodes.length > 0

    return (
      <div data-testid="force-graph-2d">
        <div data-testid="node-count">Nodes: {props.graphData.nodes.length}</div>
        <div data-testid="link-count">Links: {props.graphData.links.length}</div>
        <div data-testid="width">{props.width}</div>
        <div data-testid="height">{props.height}</div>
        <div data-testid="background">{props.backgroundColor}</div>

        {testCallbacks && (
          <>
            <div data-testid="node-label">{props.nodeLabel(props.graphData.nodes[0])}</div>
            <div data-testid="node-size">{props.nodeVal(props.graphData.nodes[0])}</div>
            <div data-testid="node-color">{props.nodeColor(props.graphData.nodes[0])}</div>
            <div data-testid="link-color">{props.linkColor()}</div>
          </>
        )}

        <button
          data-testid="mock-node-click"
          onClick={() => {
            if (props.graphData.nodes.length > 0 && props.onNodeClick) {
              props.onNodeClick(props.graphData.nodes[0])
            }
          }}
        >
          Click Node
        </button>
      </div>
    )
  }

  return {
    __esModule: true,
    default: MockComponent
  }
})

describe('ForceGraph Component', () => {
  // Test data
  const mockData: GraphResponse = {
    nodes: [
      {
        id: 'W1',
        title: 'Paper 1',
        cited_by_count: 100,
        publication_year: 2020,
        community: 0
      },
      {
        id: 'W2',
        title: 'Paper 2',
        cited_by_count: 50,
        publication_year: 2021,
        community: 1
      }
    ],
    links: [
      { source: 'W1', target: 'W2' }
    ],
    metadata: {
      total_nodes: 2,
      total_links: 1,
      communities: 2
    }
  }

  // ==========================================================================
  // Test 1: Renders graph with correct node count
  // ==========================================================================
  it('renders graph with correct node count', () => {
    // Arrange & Act
    render(<ForceGraph data={mockData} />)

    // Assert
    expect(screen.getByTestId('force-graph-2d')).toBeInTheDocument()
    expect(screen.getByTestId('node-count')).toHaveTextContent('Nodes: 2')
    expect(screen.getByTestId('link-count')).toHaveTextContent('Links: 1')
  })

  // ==========================================================================
  // Test 2: Calls onNodeClick when node is clicked
  // ==========================================================================
  it('calls onNodeClick when node is clicked', () => {
    // Arrange
    const mockOnNodeClick = jest.fn()

    // Act
    render(<ForceGraph data={mockData} onNodeClick={mockOnNodeClick} />)
    fireEvent.click(screen.getByTestId('mock-node-click'))

    // Assert
    expect(mockOnNodeClick).toHaveBeenCalledTimes(1)
    expect(mockOnNodeClick).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'W1',
        title: 'Paper 1',
        cited_by_count: 100,
        publication_year: 2020,
        community: 0
      })
    )
  })

  // ==========================================================================
  // Test 3: Renders empty graph when no data
  // ==========================================================================
  it('renders empty graph when no data', () => {
    // Arrange
    const emptyData: GraphResponse = {
      nodes: [],
      links: [],
      metadata: {
        total_nodes: 0,
        total_links: 0,
        communities: 0
      }
    }

    // Act
    render(<ForceGraph data={emptyData} />)

    // Assert
    expect(screen.getByTestId('force-graph-2d')).toBeInTheDocument()
    expect(screen.getByTestId('node-count')).toHaveTextContent('Nodes: 0')
    expect(screen.getByTestId('link-count')).toHaveTextContent('Links: 0')
  })

  // ==========================================================================
  // Test 4: Accepts custom width and height props
  // ==========================================================================
  it('accepts custom width and height props', () => {
    // Act
    render(<ForceGraph data={mockData} width={1000} height={700} />)

    // Assert
    expect(screen.getByTestId('width')).toHaveTextContent('1000')
    expect(screen.getByTestId('height')).toHaveTextContent('700')
  })

  // ==========================================================================
  // Test 5: Uses default width and height when not provided
  // ==========================================================================
  it('uses default width and height when not provided', () => {
    // Act
    render(<ForceGraph data={mockData} />)

    // Assert
    expect(screen.getByTestId('width')).toHaveTextContent('800')
    expect(screen.getByTestId('height')).toHaveTextContent('600')
  })

  // ==========================================================================
  // Test 6: Renders with correct background color
  // ==========================================================================
  it('renders with white background color (Rams design)', () => {
    // Act
    render(<ForceGraph data={mockData} />)

    // Assert
    expect(screen.getByTestId('background')).toHaveTextContent('#FFFFFF')
  })

  // ==========================================================================
  // Test 7: Node styling functions are called correctly
  // ==========================================================================
  it('applies correct node styling based on properties', () => {
    // Act
    render(<ForceGraph data={mockData} />)

    // Assert - Node label contains title, citations, year
    const label = screen.getByTestId('node-label').textContent
    expect(label).toContain('Paper 1')
    expect(label).toContain('Citations: 100')
    expect(label).toContain('Year: 2020')

    // Assert - Node size is calculated (logarithmic scaling)
    const size = screen.getByTestId('node-size').textContent
    expect(size).toBeTruthy()
    expect(parseFloat(size || '0')).toBeGreaterThanOrEqual(3) // Min size
    expect(parseFloat(size || '0')).toBeLessThanOrEqual(12) // Max size

    // Assert - Node color is grayscale (Rams design)
    const color = screen.getByTestId('node-color').textContent
    expect(color).toMatch(/^#[0-9]{6}$/) // Valid hex color

    // Assert - Link color is light gray
    expect(screen.getByTestId('link-color')).toHaveTextContent('#CCCCCC')
  })

  // ==========================================================================
  // Test 8: Handles nodes without community property
  // ==========================================================================
  it('handles nodes without community property (defaults to 0)', () => {
    // Arrange
    const dataWithoutCommunity: GraphResponse = {
      nodes: [
        {
          id: 'W3',
          title: 'Paper 3',
          cited_by_count: 75,
          publication_year: 2022
          // community is missing
        }
      ],
      links: [],
      metadata: {
        total_nodes: 1,
        total_links: 0,
        communities: 0
      }
    }

    // Act
    render(<ForceGraph data={dataWithoutCommunity} />)

    // Assert - Should render without error and use default community color
    expect(screen.getByTestId('force-graph-2d')).toBeInTheDocument()
    expect(screen.getByTestId('node-color')).toHaveTextContent('#333333') // First color in palette
  })
})
