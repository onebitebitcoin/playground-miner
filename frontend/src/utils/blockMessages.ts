import { ref } from 'vue'
import type { Block } from '@/types'

type MessageEntry = {
  message: string
  timestamp: number
}

type MessageStore = Record<string, MessageEntry>

const STORAGE_KEY = 'minedBlockMessages'

const hasStorage = typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'

const loadStore = (): MessageStore => {
  try {
    if (!hasStorage) return {}
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    if (parsed && typeof parsed === 'object') {
      return parsed as MessageStore
    }
  } catch (error) {
    console.warn('Failed to parse block message store', error)
  }
  return {}
}

const storeRef = ref<MessageStore>(loadStore())

const persistStore = () => {
  if (!hasStorage) return
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storeRef.value))
  } catch (error) {
    console.warn('Failed to persist block message store', error)
  }
}

export const getBlockMessageKey = (source: Partial<Block>): string => {
  if (source?.hash) {
    return `hash:${source.hash}`
  }
  const height = typeof source?.height === 'number' ? source.height : 'unknown'
  const nonce = typeof source?.nonce === 'number' ? source.nonce : 'na'
  return `${height}:${nonce}`
}

export const useBlockMessageStore = () => {
  const saveMessage = (block: Block, rawMessage: string) => {
    const trimmed = (rawMessage || '').trim()
    if (!trimmed) return
    const key = getBlockMessageKey(block)
    storeRef.value = {
      ...storeRef.value,
      [key]: {
        message: trimmed,
        timestamp: Date.now()
      }
    }
    persistStore()
  }

  const getMessage = (block: Partial<Block>): string => {
    if (!block) return ''
    const key = getBlockMessageKey(block)
    return storeRef.value[key]?.message || ''
  }

  return {
    messages: storeRef,
    saveMessage,
    getMessage
  }
}
