import { describe, it, expect } from 'vitest'
import { validateMnemonic, normalizeMnemonic, parseMnemonicWords } from '../validation'

describe('validateMnemonic', () => {
  it('returns error for empty input', () => {
    expect(validateMnemonic('')).toBeTruthy()
    expect(validateMnemonic('   ')).toBeTruthy()
  })

  it('returns error for null input', () => {
    expect(validateMnemonic(null)).toBeTruthy()
  })

  it('returns null for valid 12-word mnemonic', () => {
    const words = Array(12).fill('abandon').join(' ')
    expect(validateMnemonic(words)).toBeNull()
  })

  it('returns null for valid 24-word mnemonic', () => {
    const words = Array(24).fill('word').join(' ')
    expect(validateMnemonic(words)).toBeNull()
  })

  it('returns error for 11-word mnemonic', () => {
    const words = Array(11).fill('abandon').join(' ')
    expect(validateMnemonic(words)).toBeTruthy()
  })

  it('returns error for 13-word mnemonic', () => {
    const words = Array(13).fill('abandon').join(' ')
    expect(validateMnemonic(words)).toBeTruthy()
  })

  it('accepts 15-word mnemonic', () => {
    const words = Array(15).fill('word').join(' ')
    expect(validateMnemonic(words)).toBeNull()
  })

  it('accepts 18-word mnemonic', () => {
    const words = Array(18).fill('word').join(' ')
    expect(validateMnemonic(words)).toBeNull()
  })

  it('accepts 21-word mnemonic', () => {
    const words = Array(21).fill('word').join(' ')
    expect(validateMnemonic(words)).toBeNull()
  })

  it('handles extra whitespace between words', () => {
    const words = Array(12).fill('abandon').join('  ')
    expect(validateMnemonic(words)).toBeNull()
  })
})

describe('normalizeMnemonic', () => {
  it('trims leading and trailing whitespace', () => {
    expect(normalizeMnemonic('  hello world  ')).toBe('hello world')
  })

  it('lowercases words', () => {
    expect(normalizeMnemonic('ABANDON ABOUT')).toBe('abandon about')
  })

  it('normalizes multiple spaces to single space', () => {
    expect(normalizeMnemonic('word1   word2')).toBe('word1 word2')
  })

  it('returns empty string for null/undefined', () => {
    expect(normalizeMnemonic(null)).toBe('')
    expect(normalizeMnemonic(undefined)).toBe('')
  })

  it('returns empty string for empty input', () => {
    expect(normalizeMnemonic('')).toBe('')
  })
})

describe('parseMnemonicWords', () => {
  it('returns array of maxWords length', () => {
    const result = parseMnemonicWords('word1 word2', 12)
    expect(result).toHaveLength(12)
  })

  it('fills parsed words at the start', () => {
    const result = parseMnemonicWords('alpha beta', 12)
    expect(result[0]).toBe('alpha')
    expect(result[1]).toBe('beta')
  })

  it('fills remaining slots with empty string', () => {
    const result = parseMnemonicWords('alpha', 12)
    expect(result[1]).toBe('')
    expect(result[11]).toBe('')
  })

  it('returns all empty for null input', () => {
    const result = parseMnemonicWords(null, 12)
    expect(result.every(w => w === '')).toBe(true)
  })

  it('uses maxWords parameter', () => {
    const result = parseMnemonicWords('a b c d', 3)
    expect(result).toHaveLength(3)
    expect(result[0]).toBe('a')
  })
})
