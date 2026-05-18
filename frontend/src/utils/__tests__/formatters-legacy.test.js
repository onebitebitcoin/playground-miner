import { describe, it, expect } from 'vitest'
import { formatBtc, formatDate, formatNumber, formatKrw, truncate } from '../formatters.js'

describe('formatBtc', () => {
  it('returns 0 BTC for zero', () => {
    expect(formatBtc(0)).toBe('0 BTC')
  })

  it('returns 0 BTC for null', () => {
    expect(formatBtc(null)).toBe('0 BTC')
  })

  it('converts 1 BTC worth of satoshis', () => {
    const result = formatBtc(100000000)
    expect(result).toContain('1.00000000')
    expect(result).toContain('BTC')
  })

  it('formats partial satoshi amount', () => {
    expect(formatBtc(50000000)).toContain('0.50000000')
  })
})

describe('formatDate', () => {
  it('returns dash for null', () => {
    expect(formatDate(null)).toBe('—')
  })

  it('returns dash for empty string', () => {
    expect(formatDate('')).toBe('—')
  })

  it('returns dash for invalid date string', () => {
    expect(formatDate('not-a-date')).toBe('—')
  })

  it('formats valid ISO date string as non-empty string', () => {
    const result = formatDate('2024-01-15T10:30:00Z')
    expect(typeof result).toBe('string')
    expect(result).not.toBe('—')
    expect(result.length).toBeGreaterThan(4)
  })
})

describe('formatNumber', () => {
  it('returns 0 for null', () => {
    expect(formatNumber(null)).toBe('0')
  })

  it('returns string for a number', () => {
    expect(typeof formatNumber(1000)).toBe('string')
  })

  it('includes the digits', () => {
    const result = formatNumber(1234)
    expect(result).toContain('1')
    expect(result).toContain('234')
  })
})

describe('formatKrw', () => {
  it('returns 0원 for zero', () => {
    expect(formatKrw(0)).toBe('0원')
  })

  it('returns 0원 for null', () => {
    expect(formatKrw(null)).toBe('0원')
  })

  it('includes 원 suffix', () => {
    expect(formatKrw(10000)).toContain('원')
  })

  it('includes the number digits', () => {
    expect(formatKrw(50000)).toContain('50')
  })
})

describe('truncate', () => {
  it('returns empty string for null', () => {
    expect(truncate(null)).toBe('')
  })

  it('returns unchanged string shorter than limit', () => {
    expect(truncate('hello', 20)).toBe('hello')
  })

  it('truncates with ellipsis for long string', () => {
    const result = truncate('abcdefghijklmnopqrstuvwxyz', 10)
    expect(result).toBe('abcdefghij...')
  })

  it('uses default length of 20', () => {
    const str = 'a'.repeat(25)
    expect(truncate(str)).toBe('a'.repeat(20) + '...')
  })
})
