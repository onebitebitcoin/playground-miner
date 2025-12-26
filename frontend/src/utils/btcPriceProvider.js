const CACHE_DURATION_MS = 60 * 1000
const STORAGE_KEY = 'upbit_btc_price_cache'

let inflight = null

// localStorage에서 캐시 데이터 가져오기
function getCachedData() {
  try {
    const cached = localStorage.getItem(STORAGE_KEY)
    if (!cached) return null

    const { price, expiresAt, updatedAt } = JSON.parse(cached)
    const now = Date.now()

    if (now < expiresAt && Number.isFinite(price) && price > 0) {
      return { price, updatedAt }
    }

    // 만료된 캐시는 삭제
    localStorage.removeItem(STORAGE_KEY)
    return null
  } catch (err) {
    // 파싱 에러 등이 발생하면 캐시 삭제
    localStorage.removeItem(STORAGE_KEY)
    return null
  }
}

// localStorage에 캐시 데이터 저장하기
function setCachedData(price) {
  try {
    const now = Date.now()
    const cacheData = {
      price,
      updatedAt: now,
      expiresAt: now + CACHE_DURATION_MS
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(cacheData))
  } catch (err) {
    // localStorage가 가득 찼거나 사용할 수 없는 경우 무시
    console.warn('Failed to cache BTC price:', err)
  }
}

async function fetchFromUpbit() {
  const response = await fetch('https://api.upbit.com/v1/ticker?markets=KRW-BTC')
  if (!response.ok) throw new Error(`Upbit API error (${response.status})`)
  const data = await response.json()
  const price = Number(data?.[0]?.trade_price)
  if (!Number.isFinite(price) || price <= 0) throw new Error('Invalid price data from Upbit')
  return price
}

// 가격과 업데이트 시간을 함께 반환
export async function getUpbitBtcPriceKrwWithTime(force = false) {
  // 강제 갱신이 아닌 경우 캐시 확인
  if (!force) {
    const cachedData = getCachedData()
    if (cachedData !== null) {
      return cachedData
    }
  }

  // 이미 진행 중인 요청이 있으면 재사용
  if (inflight) {
    const price = await inflight
    const cached = getCachedData()
    return cached || { price, updatedAt: Date.now() }
  }

  // 새로운 API 요청
  inflight = fetchFromUpbit()
    .then((price) => {
      setCachedData(price)
      inflight = null
      return price
    })
    .catch((err) => {
      inflight = null
      throw err
    })

  const price = await inflight
  return { price, updatedAt: Date.now() }
}

// 기존 API 호환성을 위해 가격만 반환
export async function getUpbitBtcPriceKrw(force = false) {
  const { price } = await getUpbitBtcPriceKrwWithTime(force)
  return price
}
