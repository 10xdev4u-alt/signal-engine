import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Pains from '../views/Pains.vue'
import PainDetail from '../views/PainDetail.vue'
import Eval from '../views/Eval.vue'
import Search from '../views/Search.vue'
import Status from '../views/Status.vue'
import Profile from '../views/Profile.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'dashboard', component: Dashboard },
  { path: '/pains', name: 'pains', component: Pains },
  { path: '/pains/:id', name: 'pain-detail', component: PainDetail },
  { path: '/eval', name: 'eval', component: Eval },
  { path: '/search', name: 'search', component: Search },
  { path: '/status', name: 'status', component: Status },
  { path: '/profile/:sub', name: 'profile', component: Profile },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
