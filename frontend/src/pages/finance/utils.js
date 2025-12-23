export function isBitcoinLegend(series) {
  if (!series || !series.label) return false
  const label = series.label.toLowerCase()
  return label.includes('비트코인') || label.includes('bitcoin') || label.includes('btc')
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
  return series.market_cap_info || series.category || '자산군 정보 없음'
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

export function getDividendYieldText(series) {
  const yield_pct = series.dividend_yield_pct || (series.metadata && series.metadata.dividend_yield_pct)
  const val = Number(yield_pct)
  if (!Number.isFinite(val) || val < 0.1) return ''
  return `현재 배당률 ${formatPercent(val)}`
}
