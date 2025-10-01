/**
 * Validate mnemonic phrase
 */
export function validateMnemonic(mnemonic) {
  if (!mnemonic || !mnemonic.trim()) {
    return '니모닉을 입력하세요'
  }

  const words = mnemonic.trim().split(/\s+/)
  const validCounts = [12, 15, 18, 21, 24]

  if (!validCounts.includes(words.length)) {
    return `단어 개수가 올바르지 않습니다 (${validCounts.join('/')}개 필요)`
  }

  return null
}

/**
 * Normalize mnemonic (trim and lowercase)
 */
export function normalizeMnemonic(mnemonic) {
  if (!mnemonic) return ''
  return mnemonic.trim().toLowerCase().split(/\s+/).join(' ')
}

/**
 * Parse mnemonic words from text
 */
export function parseMnemonicWords(text, maxWords = 12) {
  if (!text) return Array(maxWords).fill('')

  const words = text.trim().split(/\s+/).filter(w => w.length > 0)
  const result = Array(maxWords).fill('')

  for (let i = 0; i < maxWords; i++) {
    result[i] = words[i] || ''
  }

  return result
}
