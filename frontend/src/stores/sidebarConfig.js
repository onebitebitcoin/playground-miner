import { ref } from 'vue'
import { apiGetSidebarConfig } from '@/api'

const defaultConfig = {
  show_mining: true,
  show_utxo: true,
  show_wallet: true,
  show_fee: true,
  show_finance: false,
  show_compatibility: true,
  show_timecapsule: true
}

export const sidebarConfig = ref({ ...defaultConfig })

const featureKeyMap = {
  mining: 'show_mining',
  utxo: 'show_utxo',
  wallet: 'show_wallet',
  fee: 'show_fee',
  finance: 'show_finance',
  compatibility: 'show_compatibility',
  timecapsule: 'show_timecapsule'
}

let loadingPromise = null

export function isFeatureEnabled(key) {
  const configKey = featureKeyMap[key]
  if (!configKey) return true
  return !!sidebarConfig.value[configKey]
}

export async function loadSidebarConfig(force = false) {
  if (loadingPromise && !force) {
    return loadingPromise
  }

  loadingPromise = apiGetSidebarConfig()
    .then((result) => {
      if (result?.success && result.config) {
        sidebarConfig.value = {
          ...defaultConfig,
          ...result.config
        }
      }
      return sidebarConfig.value
    })
    .catch((error) => {
      console.error('Failed to load sidebar config:', error)
      return sidebarConfig.value
    })
    .finally(() => {
      loadingPromise = null
    })

  return loadingPromise
}

export { featureKeyMap }
