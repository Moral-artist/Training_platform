import { createRouter, createWebHistory } from 'vue-router'

import Login from '../views/Login.vue'
import Home from '../views/Home.vue'
import Dashboard from '../views/Dashboard.vue'
import PreRegister from '../views/PreRegister.vue'
import ForgotPassword from '../views/ForgotPassword.vue'
import testhome from '../views/TestHome0922.vue'
import VerifyRegister from '../views/VerifyRegister.vue'
import LessonList from '../views/LessonList.vue'
import VideoDetail from '../views/VideoDetail.vue'
import Root from '../views/Root.vue'
import SystemCreate from '../views/SystemCreate.vue'
import LessonCreate from '../views/LessonCreate.vue'
import LessonAccessManage from '../views/LessonAccessManage.vue'
import CreatePlan from '../views/CreatePlan.vue'
import Mylesson from '../views/Mylesson.vue'

const routes = [
  { path: '/lessons/accessmanage', name: 'LessonAccessManage', component: LessonAccessManage },
  {
    path: '/',
    redirect: '/home'
  },

  {
    path: '/login',
    name: 'Login',
    component: Login
  },

  {
    path: '/home',
    name: 'Home',
    component: Home,
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/pre_register',
    name: 'PreRegister',
    component: PreRegister
  },
  {
    path: '/forgot_password',
    name: 'ForgotPassword',
    component: ForgotPassword
  },
  {
    path: '/testhome',
    name: 'testhome',
    component: testhome
  },
  {
    path: '/verify_register',
    name: 'verify_register',
    component: VerifyRegister
  },
  {
    path: '/lessons/:major',
    name: 'LessonList',
    component: LessonList
  },
  {
    path: '/lessons/:major/:lessonId',
    name: 'VideoDetail',
    component: VideoDetail
  },
  {
    path:'/lessons/systemcreate',
    name:'systemcreate',
    component: SystemCreate,
    meta: { requiresAuth: true }
  },
  {
    path:'/lessons/lessoncreate',
    name:'lessoncreate',
    component: LessonCreate,
    meta: { requiresAuth: true }
  },
  {
    path:'/plan/plancreate',
    name:'plancreate',
    component: CreatePlan,
    meta: { requiresAuth: true }
  },
  {
    path:'/user_info/mylessons',
    name:'Mylessons',
    component: Mylesson,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
