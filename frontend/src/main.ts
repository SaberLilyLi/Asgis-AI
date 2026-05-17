import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './styles.css'
import App from './App.vue'

// 创建 Vue 应用并注册 Element Plus。
createApp(App).use(ElementPlus).mount('#app')

