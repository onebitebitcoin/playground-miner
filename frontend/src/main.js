import { createApp, reactive, provide } from 'vue'
import App from './App.vue'
import './assets/index.css'

// 간단한 전역 상태(선택된 메뉴용)
const appState = reactive({ active: 'mining' })

const app = createApp(App)
app.provide('appState', appState)
app.mount('#app')

