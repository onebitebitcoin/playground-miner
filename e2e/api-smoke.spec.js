// @ts-check
const { test, expect } = require('@playwright/test')

test.describe('Backend API smoke tests', () => {
  test('GET /api/health/ returns ok', async ({ request }) => {
    const res = await request.get('/api/health/')
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body.status).toBe('ok')
  })

  test('GET /api/status returns height field', async ({ request }) => {
    const res = await request.get('/api/status')
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body).toHaveProperty('height')
  })

  test('GET /api/exchange-rates returns ok:true', async ({ request }) => {
    const res = await request.get('/api/exchange-rates')
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body.ok).toBe(true)
    expect(Array.isArray(body.rates)).toBe(true)
  })

  test('GET /api/withdrawal-fees returns ok:true', async ({ request }) => {
    const res = await request.get('/api/withdrawal-fees')
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body.ok).toBe(true)
  })

  test('GET /api/lightning-services returns ok:true', async ({ request }) => {
    const res = await request.get('/api/lightning-services')
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body.ok).toBe(true)
  })

  test('GET /api/routing-snapshot returns ok:true', async ({ request }) => {
    const res = await request.get('/api/routing-snapshot')
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body.ok).toBe(true)
  })

  test('GET /api/sidebar-config returns 200', async ({ request }) => {
    const res = await request.get('/api/sidebar-config')
    expect(res.status()).toBe(200)
  })

  test('GET /api/finance/quick-requests returns ok:true', async ({ request }) => {
    const res = await request.get('/api/finance/quick-requests')
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body.ok).toBe(true)
  })

  test('GET /api/compatibility/report-templates returns ok:true', async ({ request }) => {
    const res = await request.get('/api/compatibility/report-templates')
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body.ok).toBe(true)
  })
})
