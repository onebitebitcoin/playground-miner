import { createRouter, createWebHistory } from 'vue-router'
import Learn from '../pages/learn/Learn.vue'
import BitcoinMining from '../pages/mining/BitcoinMining.vue'
import UTXOPage from '../pages/UTXOPage.vue'
import WalletKingstonePage from '../pages/WalletKingstonePage.vue'
import WalletKingstoneDetailPage from '../pages/WalletKingstoneDetailPage.vue'
import FeePage from '../pages/FeePage.vue'
import FinancePage from '../pages/FinancePage.vue'
import CompatibilityPage from '../pages/CompatibilityPage.vue'
import TimeCapsulePage from '../pages/TimeCapsulePage.vue'
import AdminPage from '../pages/AdminPage.vue'
import HomePage from '../pages/HomePage.vue'
import NotFoundPage from '../pages/NotFoundPage.vue'
import { loadSidebarConfig, isFeatureEnabled } from '@/stores/sidebarConfig'

const routes = [
  {
    path: '/',
    redirect: '/home'
  },
  {
    path: '/home',
    name: 'home',
    component: HomePage
  },
  {
    path: '/learn',
    name: 'learn',
    component: Learn
  },
  {
    path: '/mining',
    name: 'mining',
    component: BitcoinMining
  },
  {
    path: '/utxo',
    name: 'utxo',
    component: UTXOPage
  },
  {
    path: '/wallet',
    name: 'wallet',
    redirect: '/wallet/kingstone'
  },
  {
    path: '/wallet/kingstone',
    name: 'wallet-kingstone',
    component: WalletKingstonePage
  },
  {
    path: '/wallet/kingstone/:id',
    name: 'wallet-kingstone-detail',
    component: WalletKingstoneDetailPage
  },
  {
    path: '/fee',
    name: 'fee',
    component: FeePage
  },
  {
    path: '/finance',
    name: 'finance',
    component: FinancePage
  },
  {
    path: '/compatibility',
    name: 'compatibility',
    component: CompatibilityPage
  },
  {
    path: '/timecapsule',
    name: 'timecapsule',
    component: TimeCapsulePage
  },
  {
    path: '/admin',
    name: 'admin',
    component: AdminPage
  },
  {
    path: '/not-found',
    name: 'not-found',
    component: NotFoundPage
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/not-found'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const HOME_ROUTE_PATHS = new Set(['/home', '/'])

const hasActiveSession = () => {
  if (typeof window === 'undefined' || typeof window.localStorage === 'undefined') {
    return false
  }
  try {
    return !!window.localStorage.getItem('nickname')
  } catch (error) {
    console.warn('Failed to access localStorage while checking session state', error)
    return false
  }
}

const isHomeRoute = (route) => {
  if (!route) return false
  if (route.name === 'home') return true
  return HOME_ROUTE_PATHS.has(route.path)
}

const featureRouteMap = {
  mining: 'mining',
  utxo: 'utxo',
  wallet: 'wallet',
  'wallet-kingstone': 'wallet',
  'wallet-kingstone-detail': 'wallet',
  fee: 'fee',
  finance: 'finance',
  compatibility: 'compatibility',
  timecapsule: 'timecapsule'
}

router.beforeEach(async (to, from, next) => {
  if (!hasActiveSession() && !isHomeRoute(to)) {
    next({ name: 'home' })
    return
  }

  const featureKey = featureRouteMap[to.name]
  if (!featureKey) {
    next()
    return
  }

  try {
    await loadSidebarConfig()
  } catch (error) {
    console.error('Failed to refresh sidebar config before navigation', error)
  }

  if (!isFeatureEnabled(featureKey)) {
    next({ name: 'not-found' })
    return
  }

  next()
})

export default router
