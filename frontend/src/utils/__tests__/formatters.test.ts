import { describe, it, expect } from 'vitest'
import {
  formatNumber,
  formatBTC,
  truncateAddress,
  formatTimestamp,
  formatRelativeTime,
  formatBlockHeight,
  formatDifficulty,
  formatUTXOId,
  formatTransactionId,
  isValidBTCAmount,
  isValidNickname,
} from '../formatters.ts'

describe('formatNumber', () => {
  it('formats zero', () => {
    expect(formatNumber(0)).toBe('0')
  })

  it('returns a string', () => {
    expect(typeof formatNumber(42)).toBe('string')
  })

  it('includes the number', () => {
    expect(formatNumber(1000)).toContain('1')
  })
})

describe('formatBTC', () => {
  it('includes BTC suffix', () => {
    expect(formatBTC(1)).toContain('BTC')
  })

  it('includes the number', () => {
    expect(formatBTC(100)).toContain('100')
  })
})

describe('truncateAddress', () => {
  it('returns short address unchanged', () => {
    const addr = 'abc123'
    expect(truncateAddress(addr)).toBe(addr)
  })

  it('truncates long address with ellipsis', () => {
    const addr = 'bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq'
    const result = truncateAddress(addr)
    expect(result).toContain('...')
    expect(result.length).toBeLessThan(addr.length)
  })

  it('respects custom start/end lengths', () => {
    const addr = '1234567890abcdefghij'
    const result = truncateAddress(addr, 4, 4)
    expect(result).toBe('1234...ghij')
  })
})

describe('formatBlockHeight', () => {
  it('prefixes with #', () => {
    expect(formatBlockHeight(840000)).toMatch(/^#/)
  })

  it('includes block number', () => {
    expect(formatBlockHeight(100)).toContain('100')
  })
})

describe('formatDifficulty', () => {
  it('includes ≤ prefix', () => {
    expect(formatDifficulty(5000)).toContain('≤')
  })

  it('includes the difficulty value', () => {
    expect(formatDifficulty(999)).toContain('999')
  })
})

describe('formatUTXOId', () => {
  it('returns first N chars', () => {
    expect(formatUTXOId('abcdefghijklmn', 8)).toBe('abcdefgh')
  })

  it('uses default length of 8', () => {
    expect(formatUTXOId('abcdefghijklmn')).toHaveLength(8)
  })
})

describe('formatTransactionId', () => {
  it('appends ellipsis', () => {
    const txId = 'abc123def456ghi789jkl'
    expect(formatTransactionId(txId)).toMatch(/\.\.\.$/)
  })

  it('truncates to default length', () => {
    const txId = 'abcdefghijklmnopqrstuvwxyz'
    const result = formatTransactionId(txId)
    expect(result).toBe('abcdefghijklmnop...')
  })
})

describe('isValidBTCAmount', () => {
  it('accepts valid satoshi amount', () => {
    expect(isValidBTCAmount(100000)).toBe(true)
  })

  it('rejects zero', () => {
    expect(isValidBTCAmount(0)).toBe(false)
  })

  it('rejects negative', () => {
    expect(isValidBTCAmount(-1)).toBe(false)
  })

  it('rejects over 21M BTC', () => {
    expect(isValidBTCAmount(22_000_000)).toBe(false)
  })

  it('rejects float', () => {
    expect(isValidBTCAmount(1.5)).toBe(false)
  })
})

describe('isValidNickname', () => {
  it('accepts alphanumeric nickname', () => {
    expect(isValidNickname('alice123')).toBe(true)
  })

  it('accepts underscore', () => {
    expect(isValidNickname('alice_bob')).toBe(true)
  })

  it('rejects too short', () => {
    expect(isValidNickname('a')).toBe(false)
  })

  it('rejects too long', () => {
    expect(isValidNickname('a'.repeat(21))).toBe(false)
  })

  it('rejects special characters', () => {
    expect(isValidNickname('alice!')).toBe(false)
  })

  it('rejects spaces', () => {
    expect(isValidNickname('alice bob')).toBe(false)
  })
})

describe('formatRelativeTime', () => {
  it('returns "초 전" for recent timestamps', () => {
    const recent = Date.now() - 5000
    expect(formatRelativeTime(recent)).toContain('초 전')
  })

  it('returns "분 전" for minute-old timestamps', () => {
    const minuteAgo = Date.now() - 90000
    expect(formatRelativeTime(minuteAgo)).toContain('분 전')
  })

  it('returns "시간 전" for hour-old timestamps', () => {
    const hourAgo = Date.now() - 3700000
    expect(formatRelativeTime(hourAgo)).toContain('시간 전')
  })

  it('returns "일 전" for day-old timestamps', () => {
    const dayAgo = Date.now() - 86400000 * 2
    expect(formatRelativeTime(dayAgo)).toContain('일 전')
  })
})
