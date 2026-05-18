import { describe, it, expect, beforeEach } from 'vitest'
import { getCurrentUsername, getAdminUsername } from '../adminAuth.js'

describe('getCurrentUsername', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('returns anonymous when no nickname set', () => {
    expect(getCurrentUsername()).toBe('anonymous')
  })

  it('returns stored nickname', () => {
    localStorage.setItem('nickname', 'alice')
    expect(getCurrentUsername()).toBe('alice')
  })
})

describe('getAdminUsername', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('returns empty string when nothing is set', () => {
    expect(getAdminUsername()).toBe('')
  })

  it('returns empty when nickname is admin but isAdmin not set', () => {
    localStorage.setItem('nickname', 'admin')
    expect(getAdminUsername()).toBe('')
  })

  it('returns empty when isAdmin is true but nickname is not admin', () => {
    localStorage.setItem('nickname', 'alice')
    localStorage.setItem('isAdmin', 'true')
    expect(getAdminUsername()).toBe('')
  })

  it('returns admin when both nickname=admin and isAdmin=true', () => {
    localStorage.setItem('nickname', 'admin')
    localStorage.setItem('isAdmin', 'true')
    expect(getAdminUsername()).toBe('admin')
  })
})
