<script setup>
  import { watch } from 'vue'
  import { useRoute } from 'vue-router'
  import request,{ setCsrfToken } from './api/request'
  const route = useRoute()
  watch(() => route.meta.requiresAuth, async (requiresAuth) => {
    if (!requiresAuth) return
    try {
      const response = await request.get('/api/user/user_info')

      setCsrfToken(response.data.csrf_token)
    } catch (error) {
      console.log('Not logged in')
    }
  }, { immediate: true })
</script>



<template>
  <router-view />
</template>
