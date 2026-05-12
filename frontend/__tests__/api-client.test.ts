/**
 * API Client tests
 * TDD: Red → Green → Refactor
 */

import { getHealth, searchPapers, APIError } from '@/lib/api-client'
import * as apiClient from '@/lib/api-client'

// Mock fetch
global.fetch = jest.fn()

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('getHealth', () => {
    it('returns health status when API responds successfully', async () => {
      const mockResponse = { status: 'ok', version: '1.0.0' }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await getHealth()

      expect(result).toEqual(mockResponse)
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/health')
    })

    it('throws APIError when API returns error status', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 503,
        text: async () => 'Service Unavailable',
      })

      try {
        await getHealth()
        fail('Should have thrown APIError')
      } catch (error) {
        expect(error).toBeInstanceOf(APIError)
        expect((error as APIError).message).toBe('Health check failed')
        expect((error as APIError).statusCode).toBe(503)
      }
    })

    it('throws APIError with connection message when fetch fails', async () => {
      ;(global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      )

      try {
        await getHealth()
        fail('Should have thrown APIError')
      } catch (error) {
        expect(error).toBeInstanceOf(APIError)
        expect((error as APIError).message).toContain('Failed to connect to backend')
      }
    })
  })

  describe('searchPapers', () => {
    it('searches papers successfully', async () => {
      const mockResponse = {
        nodes: [
          {
            id: 'W1',
            title: 'Test Paper',
            cited_by_count: 50,
            publication_year: 2020,
            community: 0
          }
        ],
        links: [],
        metadata: {
          total_nodes: 1,
          total_links: 0,
          communities: 1
        }
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await searchPapers('machine learning', 50)

      expect(result).toEqual(mockResponse)
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/search?query=machine+learning&limit=50'
      )
    })

    it('throws APIError when search fails', async () => {
      const mockFetch = global.fetch as jest.Mock

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: async () => 'Server error details',
      })

      await expect(searchPapers('test')).rejects.toThrow(APIError)

      // Reset and test again with fresh mock
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: async () => 'Server error details',
      })

      try {
        await searchPapers('test')
        fail('Should have thrown an error')
      } catch (error) {
        expect(error).toBeInstanceOf(APIError)
        expect((error as apiClient.APIError).message).toContain('Search failed')
        expect((error as apiClient.APIError).statusCode).toBe(500)
      }
    })

    it('throws APIError with connection message when fetch fails', async () => {
      ;(global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      )

      try {
        await searchPapers('test')
        fail('Should have thrown an error')
      } catch (error) {
        expect(error).toBeInstanceOf(APIError)
        expect((error as APIError).message).toMatch(/Failed to search papers.*backend is running/)
      }
    })
  })
})
