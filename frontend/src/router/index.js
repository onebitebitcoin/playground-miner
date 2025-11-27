import { createRouter, createWebHistory } from 'vue-router'
import Learn from '../pages/learn/Learn.vue'
import BitcoinMining from '../pages/mining/BitcoinMining.vue'
import UTXOPage from '../pages/UTXOPage.vue'
import WalletKingstonePage from '../pages/WalletKingstonePage.vue'
import WalletKingstoneDetailPage from '../pages/WalletKingstoneDetailPage.vue'
import FeePage from '../pages/FeePage.vue'
import FinancePage from '../pages/FinancePage.vue'
import AdminPage from '../pages/AdminPage.vue'
import NicknameSetup from '../pages/NicknameSetup.vue'

const routes = [
  {
    path: '/',
    redirect: () => {
      // Check if nickname is set, if not redirect to nickname setup
      const nickname = localStorage.getItem('nickname')
      return nickname ? '/mining' : '/nickname'
    }
  },
  {
    path: '/nickname',
    name: 'nickname',
    component: NicknameSetup,
    meta: { requiresNoNickname: true }
  },
  {
    path: '/learn',
    name: 'learn',
    component: Learn,
    meta: { requiresNickname: true }
  },
  {
    path: '/mining',
    name: 'mining',
    component: BitcoinMining,
    meta: { requiresNickname: true }
  },
  {
    path: '/utxo',
    name: 'utxo',
    component: UTXOPage,
    meta: { requiresNickname: true }
  },
  {
    path: '/wallet',
    name: 'wallet',
    redirect: '/wallet/kingstone',
    meta: { requiresNickname: true }
  },
  {
    path: '/wallet/kingstone',
    name: 'wallet-kingstone',
    component: WalletKingstonePage,
    meta: { requiresNickname: true }
  },
  {
    path: '/wallet/kingstone/:id',
    name: 'wallet-kingstone-detail',
    component: WalletKingstoneDetailPage,
    meta: { requiresNickname: true }
  },
  {
    path: '/fee',
    name: 'fee',
    component: FeePage,
    meta: { requiresNickname: true }
  },
  {
    path: '/finance',
    name: 'finance',
    component: FinancePage,
    meta: { requiresNickname: true }
  },
  {
    path: '/admin',
    name: 'admin',
    component: AdminPage,
    meta: { requiresNickname: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard to handle nickname requirement
router.beforeEach((to, from, next) => {
  const nickname = localStorage.getItem('nickname')
  const isAdmin = nickname === 'admin' && localStorage.getItem('isAdmin') === 'true'

  if (to.meta.requiresNickname && !nickname) {
    next('/nickname')
  } else if (to.meta.requiresNoNickname && nickname) {
    next('/mining')
  } else {
    next()
  }
})

export default router
