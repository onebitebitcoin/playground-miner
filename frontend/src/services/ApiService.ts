import type { BlockchainStatus, Block, MiningResponse, ApiResponse } from '@/types'

// API Configuration
const BASE_URL = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

// Error Classes
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class NetworkError extends ApiError {
  constructor(message = '네트워크 연결 오류') {
    super(message)
    this.name = 'NetworkError'
  }
}

// Base API Handler
class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    try {
      const response = await fetch(`${BASE_URL}${endpoint}`, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      })

      if (!response.ok) {
        throw new ApiError(
          `요청 실패: ${response.status}`,
          response.status
        )
      }

      const contentType = response.headers.get('content-type')
      if (!contentType?.includes('application/json')) {
        const body = await response.text()
        throw new ApiError(
          `잘못된 응답 형식: ${contentType}`,
          response.status
        )
      }

      return await response.json()
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      throw new NetworkError()
    }
  }

  // Blockchain Status
  async getStatus(): Promise<BlockchainStatus> {
    return this.request<BlockchainStatus>('/api/status')
  }

  // Blocks
  async getBlocks(): Promise<{ blocks: Block[] }> {
    return this.request<{ blocks: Block[] }>('/api/blocks')
  }

  // Mining
  async submitMining(data: { miner: string; nonce: number }): Promise<MiningResponse> {
    try {
      return await this.request<MiningResponse>('/api/mine', {
        method: 'POST',
        body: JSON.stringify(data),
      })
    } catch (error) {
      if (error instanceof ApiError) {
        return { 
          ok: false, 
          error: `서버 오류(${error.status})` 
        }
      }
      return { 
        ok: false, 
        error: '요청 실패(네트워크)' 
      }
    }
  }

  // Nickname Management
  async checkNickname(nickname: string): Promise<ApiResponse> {
    return this.request<ApiResponse>(`/api/check_nick?nickname=${encodeURIComponent(nickname)}`)
  }

  async registerNickname(nickname: string): Promise<ApiResponse> {
    return this.request<ApiResponse>('/api/register_nick', {
      method: 'POST',
      body: JSON.stringify({ nickname }),
    })
  }

  // System Reset
  async initReset(token: string): Promise<ApiResponse> {
    return this.request<ApiResponse>('/api/init_reset', {
      method: 'POST',
      body: JSON.stringify({ token }),
    })
  }
}

// Export singleton instance
export const apiService = new ApiService()

// Legacy compatibility exports (to be removed after migration)
export const fetchStatus = () => apiService.getStatus()
export const fetchBlocks = () => apiService.getBlocks()
export const postMine = (data: { miner: string; nonce: number }) => apiService.submitMining(data)
export const apiCheckNickname = (nickname: string) => apiService.checkNickname(nickname)
export const apiRegisterNickname = (nickname: string) => apiService.registerNickname(nickname)
export const apiInitReset = (token: string) => apiService.initReset(token)