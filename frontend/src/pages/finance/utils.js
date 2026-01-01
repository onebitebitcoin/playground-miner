export function isBitcoinLegend(series) {
  if (!series || !series.label) return false
  const label = series.label.toLowerCase()
  return label.includes('비트코인') || label.includes('bitcoin') || label.includes('btc')
}

export function isKoreanM2Legend(series) {
  if (!series || !series.label) return false
  const label = series.label.toLowerCase()
  const hasKorea = label.includes('한국') || label.includes('korea')
  return hasKorea && label.includes('m2')
}

export function getLegendLabel(series) {
  if (!series) return ''
  // Try to find normalized label from price map if available, or use the series label
  // This logic might need to be passed in or the map provided
  return series.display_label || series.label || ''
}

export function formatAssetCategory(series) {
  if (series.market_cap_group && typeof series.market_cap_rank === 'number') {
    return `${series.market_cap_group} ${series.market_cap_rank}위`
  }

  // Category 매핑
  const category = series.market_cap_info || series.category || series.metadata?.category || ''

  if (!category) return '자산군 정보 없음'

  const categoryLower = category.toLowerCase()

  // 명확한 카테고리 매핑
  if (categoryLower.includes('빅테크') || categoryLower.includes('bigtech')) {
    return '미국 빅테크'
  }
  if (categoryLower.includes('us stock') || categoryLower.includes('미국 주식') || categoryLower.includes('미국')) {
    return '미국 주식'
  }
  if (categoryLower.includes('국내') || categoryLower.includes('korea') || categoryLower.includes('kospi') || categoryLower.includes('kosdaq')) {
    return '국내 주식'
  }
  if (categoryLower.includes('etf')) {
    return 'ETF'
  }
  if (categoryLower.includes('reit') || categoryLower.includes('리츠')) {
    return 'REIT'
  }
  if (categoryLower.includes('crypto') || categoryLower.includes('암호화폐') || categoryLower.includes('비트코인')) {
    return '암호화폐'
  }
  if (categoryLower.includes('예적금') || categoryLower.includes('deposit')) {
    return '예적금'
  }
  if (categoryLower.includes('금') || categoryLower.includes('silver') || categoryLower.includes('은') || categoryLower.includes('gold')) {
    return '귀금속'
  }

  return category
}

export function formatPercent(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '0.0%'
  return `${value.toFixed(1)}%`
}

export function formatMultiple(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '0.0'
  const absValue = Math.abs(value)
  let precision = 1
  if (absValue < 1) precision = 2
  if (absValue < 0.1) precision = 3
  if (absValue < 0.01) precision = 4
  return value.toFixed(precision)
}

/**
 * 알려진 월배당 ETF 목록
 */
const MONTHLY_DIVIDEND_TICKERS = new Set([
  'JEPI', 'JEPQ', 'QYLD', 'XYLD', 'RYLD', 'NUSI', 'DIVO', 'O', 'STAG', 'LTC'
])

/**
 * 티커 기반으로 배당 주기를 추론
 */
function inferDividendFrequency(series) {
  const ticker = (series.ticker || series.id || '').toUpperCase()
  const label = (series.label || '').toUpperCase()

  // 월배당 ETF 확인
  if (MONTHLY_DIVIDEND_TICKERS.has(ticker) || MONTHLY_DIVIDEND_TICKERS.has(label)) {
    return '월배당'
  }

  // 리츠(REIT)는 일반적으로 월배당 또는 분기배당
  const category = (series.category || (series.metadata && series.metadata.category) || '').toLowerCase()
  if (category.includes('reit') || category.includes('리츠')) {
    return '월배당'
  }

  // 기본값은 분기배당 (미국 주식의 일반적인 배당 주기)
  return '분기배당'
}

export function getDividendYieldText(series) {
  if (!series) return ''

  const yield_pct = series.dividend_yield_pct || (series.metadata && series.metadata.dividend_yield_pct)
  const val = Number(yield_pct)
  if (!Number.isFinite(val) || val < 0.1) return ''

  const frequency = inferDividendFrequency(series)
  return `배당 ${formatPercent(val)} (${frequency})`
}
