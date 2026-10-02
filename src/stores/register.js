import { defineStore } from 'pinia'
import { ref } from 'vue'

// 在不同 Vue 页面之间保存和共享注册流程的数据。
export const useRegisterStore = defineStore('register', () => {

  const challengeId = ref(null)

  const setChallengeId = (id) => {
    challengeId.value = id
  }

  const clearChallengeId = () => {
    challengeId.value = null
  }

  return {
    challengeId,
    setChallengeId,
    clearChallengeId
  }
})