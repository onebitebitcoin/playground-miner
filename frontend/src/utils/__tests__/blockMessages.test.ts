import { describe, it, expect, beforeEach } from 'vitest'
import { getBlockMessageKey, useBlockMessageStore } from '../blockMessages'

describe('getBlockMessageKey', () => {
  it('uses hash when available', () => {
    expect(getBlockMessageKey({ hash: 'abc123', height: 100 })).toBe('hash:abc123')
  })

  it('uses height:nonce when no hash', () => {
    expect(getBlockMessageKey({ height: 100, nonce: 42 })).toBe('100:42')
  })

  it('handles missing height', () => {
    expect(getBlockMessageKey({ nonce: 5 })).toBe('unknown:5')
  })

  it('handles missing nonce', () => {
    expect(getBlockMessageKey({ height: 7 })).toBe('7:na')
  })

  it('handles empty object', () => {
    expect(getBlockMessageKey({})).toBe('unknown:na')
  })
})

describe('useBlockMessageStore', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('saves and retrieves a message by hash', () => {
    const { saveMessage, getMessage } = useBlockMessageStore()
    const block: any = { hash: 'beef1111', height: 1, nonce: 0 }
    saveMessage(block, 'hello')
    expect(getMessage({ hash: 'beef1111' })).toBe('hello')
  })

  it('trims whitespace from saved message', () => {
    const { saveMessage, getMessage } = useBlockMessageStore()
    const block: any = { hash: 'beef2222', height: 2, nonce: 0 }
    saveMessage(block, '  trimmed  ')
    expect(getMessage({ hash: 'beef2222' })).toBe('trimmed')
  })

  it('ignores blank messages', () => {
    const { saveMessage, getMessage } = useBlockMessageStore()
    const block: any = { hash: 'beef3333', height: 3, nonce: 0 }
    saveMessage(block, '   ')
    expect(getMessage({ hash: 'beef3333' })).toBe('')
  })

  it('returns empty string for unknown block', () => {
    const { getMessage } = useBlockMessageStore()
    expect(getMessage({ hash: 'does-not-exist' })).toBe('')
  })

  it('returns empty string for null block', () => {
    const { getMessage } = useBlockMessageStore()
    expect(getMessage(null as any)).toBe('')
  })
})
