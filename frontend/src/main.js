import './assets/styles.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import VueApexCharts from 'vue3-apexcharts'

import App from './App.vue'


const app = createApp(App)

app.use(createPinia())


app.mount('#app')
