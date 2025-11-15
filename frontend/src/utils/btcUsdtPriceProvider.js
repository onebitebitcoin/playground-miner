const CACHE_DURATION_MS = 60 * 1000
let cachedPrice = null
let cacheExpiresAt = 0
let inflight = null

async function fetchFromBinance() {
  const response = await fetch('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT')
  if (!response.ok) throw new Error(`Binance API error (${response.status})`)
  const data = await response.json()
  const price = Number(data?.price)
  if (!Number.isFinite(price) || price <= 0) throw new Error('Invalid BTC/USDT price data')
  return price
}

export async function getBtcPriceUsdt(force = false) {
  const now = Date.now()
  if (!force && cachedPrice !== null && now < cacheExpiresAt) {
    return cachedPrice
  }
  if (inflight) {
    return inflight
  }
  inflight = fetchFromBinance()
    .then((price) => {
      cachedPrice = price
      cacheExpiresAt = Date.now() + CACHE_DURATION_MS
      inflight = null
      return price
    })
    .catch((err) => {
      inflight = null
      throw err
    })
  return inflight
}

