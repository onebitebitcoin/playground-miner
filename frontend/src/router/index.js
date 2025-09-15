import { createRouter, createWebHistory } from 'vue-router'
import Learn from '../pages/learn/Learn.vue'
import BitcoinMining from '../pages/mining/BitcoinMining.vue'
import UTXOPage from '../pages/UTXOPage.vue'
import WalletPage from '../pages/WalletPage.vue'
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
    component: WalletPage,
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

  if (to.meta.requiresNickname && !nickname) {
    next('/nickname')
  } else if (to.meta.requiresNoNickname && nickname) {
    next('/mining')
  } else {
    next()
  }
})

export default router