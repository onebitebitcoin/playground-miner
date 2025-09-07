// Core Types
export interface BlockchainStatus {
  height: number
  difficulty: number
  reward: number
}

export interface Block {
  height: number
  difficulty: number
  nonce: number
  reward: number
  miner: string
  timestamp: string
  hash?: string
}

export interface UTXO {
  id: string
  amount: number
  address: string
  txId: string
  vout: number
  created?: number
  isSelected?: boolean
  isConsumed?: boolean
}

export interface Wallet {
  name: string
  address: string
  utxos: UTXO[]
}

export interface Transaction {
  id: string
  timestamp: number
  inputs: UTXO[]
  outputs: Array<{
    address: string
    amount: number
    recipientName?: string
  }>
  fee: number
}

export interface TransactionRecipient {
  walletAddress: string
  amount: number
}

// Mining Types
export type MiningState = 'idle' | 'mining' | 'success' | 'fail'

// API Response Types
export interface ApiResponse<T = any> {
  ok: boolean
  data?: T
  error?: string
}

export interface MiningResponse extends ApiResponse {
  block?: Block
  status?: BlockchainStatus
}

// WebSocket/SSE Event Types
export interface WebSocketMessage {
  type: 'snapshot' | 'block' | 'status' | 'peers'
  blocks?: Block[]
  block?: Block
  status?: BlockchainStatus
  peers?: string[]
  notice?: string
  me?: { nickname: string }
}

// Component Props Types
export interface StatusCardProps {
  title: string
  value: string | number
  subtitle: string
  icon: string
  color: 'orange' | 'blue' | 'green'
  clickable?: boolean
}

// Error Types
export interface AppError {
  code: string
  message: string
  details?: any
}

// State Types
export interface AppState {
  active: 'mining' | 'utxo' | 'nick'
}

export interface NotificationState {
  id: number
  user: string
  timestamp: number
}