<template>
  <div class="root-page">

    <div class="root-card">

      <!-- Logo -->
      <div class="logo">
        T
      </div>

      <h1>
        培训平台
      </h1>

      <p>
        Training System
      </p>

      <!-- Loading -->
      <div class="loading">

        <div class="spinner"></div>

        <span>
          正在进入系统...
        </span>

      </div>

    </div>

  </div>
</template>


<script setup>

import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import request from '../api/request'


const router = useRouter()


async function checkLogin() {

  try {

    /*
      FastAPI 检查当前 Session

      浏览器会自动携带 HttpOnly Cookie
      因为 request.js 已经：
      withCredentials: true
    */
    await request.get('/api/auth/me')


    /*
      Session 有效
      进入登录后的首页
    */
    router.replace('/home')

  }

  catch (error) {

    /*
      没有登录
      Session 过期
      Session 无效
    */

    router.replace('/login')

  }

}


onMounted(() => {

  checkLogin()

})

</script>


<style scoped>

* {
  box-sizing: border-box;
}


.root-page {

  width: 100%;

  min-height: 100vh;

  display: flex;

  justify-content: center;

  align-items: center;

  background: #f4f6fb;

}


.root-card {

  width: 380px;

  padding: 48px 40px;

  background: #ffffff;

  border-radius: 24px;

  text-align: center;

  box-shadow:
    0 15px 45px rgba(44, 62, 110, 0.08);

}


.logo {

  width: 58px;

  height: 58px;

  margin: 0 auto 18px;

  border-radius: 16px;

  display: flex;

  justify-content: center;

  align-items: center;

  background: #3d66e8;

  color: white;

  font-size: 26px;

  font-weight: 700;

}


h1 {

  margin: 0;

  font-size: 24px;

  color: #1d2939;

}


p {

  margin-top: 7px;

  color: #98a2b3;

  font-size: 13px;

}


.loading {

  margin-top: 35px;

  display: flex;

  flex-direction: column;

  align-items: center;

  gap: 14px;

  color: #667085;

  font-size: 13px;

}


/* loading circle */

.spinner {

  width: 30px;

  height: 30px;

  border: 3px solid #e8ecf8;

  border-top-color: #3d66e8;

  border-radius: 50%;

  animation: spin 0.8s linear infinite;

}


@keyframes spin {

  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }

}

</style>