/**
 * Utility functions for formatting data across the application
 */

// Number formatting
export function formatNumber(num: number): string {
  return num.toLocaleString()
}

export function formatBTC(amount: number): string {
  return `${formatNumber(amount)} BTC`
}

// Address formatting
export function truncateAddress(address: string, startLength = 20, endLength = 10): string {
  if (address.length <= startLength + endLength) {
    return address
  }
  return `${address.slice(0, startLength)}...${address.slice(-endLength)}`
}

// Date/Time formatting
export function formatTimestamp(timestamp: string | number): string {
  const date = new Date(timestamp)
  return date.toLocaleString()
}

export function formatRelativeTime(timestamp: string | number): string {
  const now = Date.now()
  const time = typeof timestamp === 'string' ? new Date(timestamp).getTime() : timestamp
  const diffMs = now - time
  
  const diffSeconds = Math.floor(diffMs / 1000)
  const diffMinutes = Math.floor(diffSeconds / 60)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)
  
  if (diffSeconds < 60) return `${diffSeconds}초 전`
  if (diffMinutes < 60) return `${diffMinutes}분 전`
  if (diffHours < 24) return `${diffHours}시간 전`
  if (diffDays < 7) return `${diffDays}일 전`
  
  return formatTimestamp(timestamp)
}

// Block formatting
export function formatBlockHeight(height: number): string {
  return `#${formatNumber(height)}`
}

export function formatDifficulty(difficulty: number): string {
  return `≤ ${formatNumber(difficulty)}`
}

// UTXO formatting
export function formatUTXOId(id: string, length = 8): string {
  return id.slice(0, length)
}

export function formatTransactionId(txId: string, length = 16): string {
  return `${txId.slice(0, length)}...`
}

// Validation helpers
export function isValidBTCAmount(amount: number): boolean {
  return amount > 0 && amount <= 21_000_000 && Number.isInteger(amount)
}

export function isValidNickname(nickname: string): boolean {
  return nickname.length >= 2 && nickname.length <= 20 && /^[a-zA-Z0-9_]+$/.test(nickname)
}