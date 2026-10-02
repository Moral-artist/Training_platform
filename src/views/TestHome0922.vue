<template>
  <div>
    <h2>CSRF 测试</h2>

    <button @click="testCsrf">
      测试 CSRF
    </button>
  </div>
</template>

<script setup>
import request, { setCsrfToken } from '../api/request'

const testCsrf = async () => {

  // 假装这是登录成功后后端返回的 csrf_token
  setCsrfToken('test-csrf-123')

  try {
    await request.post('/test', {
      name: 'test'
    })
  } catch (error) {
    console.log('请求失败是正常的，因为现在没有后端')
  }
}
</script>