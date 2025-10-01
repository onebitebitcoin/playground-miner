/**
 * Format satoshis to BTC
 */
export function formatBtc(sats) {
  if (!sats || sats === 0) return '0 BTC'
  const btc = (sats / 100000000).toFixed(8)
  return `${btc} BTC`
}

/**
 * Format date string
 */
export function formatDate(dateString) {
  if (!dateString) return '—'
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return '—'
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return '—'
  }
}

/**
 * Format number with locale
 */
export function formatNumber(num) {
  if (num == null) return '0'
  return Number(num).toLocaleString()
}

/**
 * Format KRW currency
 */
export function formatKrw(amount) {
  if (!amount || amount === 0) return '0원'
  return `${Number(amount).toLocaleString()}원`
}

/**
 * Truncate string with ellipsis
 */
export function truncate(str, length = 20) {
  if (!str) return ''
  if (str.length <= length) return str
  return `${str.substring(0, length)}...`
}
