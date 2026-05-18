// @ts-check
const { test, expect } = require('@playwright/test')

test.describe('Frontend smoke tests', () => {
  test('homepage loads without JS errors', async ({ page }) => {
    const errors = []
    page.on('pageerror', (err) => errors.push(err.message))

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    expect(errors.filter(e => !e.includes('favicon'))).toHaveLength(0)
  })

  test('page title is set', async ({ page }) => {
    await page.goto('/')
    const title = await page.title()
    expect(title.length).toBeGreaterThan(0)
  })

  test('main content area is visible', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')
    const body = page.locator('body')
    await expect(body).toBeVisible()
  })

  test('/fee route loads without crash', async ({ page }) => {
    const errors = []
    page.on('pageerror', (err) => errors.push(err.message))

    await page.goto('/fee')
    await page.waitForLoadState('networkidle')

    expect(errors).toHaveLength(0)
  })

  test('/finance route loads without crash', async ({ page }) => {
    const errors = []
    page.on('pageerror', (err) => errors.push(err.message))

    await page.goto('/finance')
    await page.waitForLoadState('networkidle')

    expect(errors).toHaveLength(0)
  })

  test('unknown route shows 404 page (no white screen)', async ({ page }) => {
    await page.goto('/this-route-does-not-exist')
    await page.waitForLoadState('domcontentloaded')
    const body = page.locator('body')
    await expect(body).not.toBeEmpty()
  })
})
