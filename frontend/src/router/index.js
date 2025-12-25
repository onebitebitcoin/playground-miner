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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
