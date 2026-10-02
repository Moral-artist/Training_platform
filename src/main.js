import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'

const app = createApp(App)
const pinia = createPinia()

// 注册 Router
app.use(router)
// 注册 Element Plus
app.use(ElementPlus)
// 注册 Pinia
app.use(pinia)

app.mount('#app')
