const CACHE_DURATION_MS = 60 * 1000
let cachedPrice = null
let cacheExpiresAt = 0
let inflight = null

async function fetchFromUpbit() {
  const response = await fetch('https://api.upbit.com/v1/ticker?markets=KRW-BTC')
  if (!response.ok) throw new Error(`Upbit API error (${response.status})`)
  const data = await response.json()
  const price = Number(data?.[0]?.trade_price)
  if (!Number.isFinite(price) || price <= 0) throw new Error('Invalid price data from Upbit')
  return price
}

export async function getUpbitBtcPriceKrw(force = false) {
  const now = Date.now()
  if (!force && cachedPrice !== null && now < cacheExpiresAt) {
    return cachedPrice
  }
  if (inflight) {
    return inflight
  }
  inflight = fetchFromUpbit()
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
