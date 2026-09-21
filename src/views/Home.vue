<template>
  <div class="home">
    <h1>首页</h1>
    <p>登录成功，欢迎进入系统。</p>

    <button @click="logout">
      退出登录
    </button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const logout = () => {
  router.push('/login')
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  padding: 40px;
  box-sizing: border-box;
  background: #f4f7fc;
}

h1 {
  color: #1f2937;
}

button {
  margin-top: 20px;
  padding: 10px 20px;

  border: none;
  border-radius: 8px;

  background: #3663e8;
  color: white;

  cursor: pointer;
}
</style>