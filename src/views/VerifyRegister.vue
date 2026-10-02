<template>

  <div class="background">

    <Message
      :visible="messageBox.visible"
      :message="messageBox.message"
      :type="messageBox.type"
    />

    <div class="verify-wrapper">

      <div class="verify-card">

        <h2>
          邮箱验证
        </h2>

        <p>
          请输入邮箱验证码
        </p>

        <div class="form-item">

          <label>
            验证码
          </label>

          <input
            v-model="verifyForm.code"
            type="text"
            placeholder="请输入验证码"
            @keyup.enter="handleVerify"
          />

        </div>

        <button
          class="verify-btn"
          :disabled="loading"
          @click="handleVerify"
        >
          {{ loading ? '验证中...' : '确认' }}
        </button>

      </div>

    </div>

  </div>

</template>


<script setup>

import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import request from '../api/request'
import Message from '../components/Message.vue'
import { useRegisterStore } from '../stores/register'


const router = useRouter()

const registerStore = useRegisterStore()


/* =========================
   验证码
========================= */

const verifyForm = reactive({
  code: ''
})


/* =========================
   Loading
========================= */

const loading = ref(false)


/* =========================
   Message
========================= */

const messageBox = reactive({
  visible: false,
  message: '',
  type: 'warning'
})

let messageTimer = null

const showMessage = (message, type = 'warning') => {

  messageBox.message = message
  messageBox.type = type
  messageBox.visible = true

  clearTimeout(messageTimer)

  messageTimer = setTimeout(() => {
    messageBox.visible = false
  }, 2500)
}


/* =========================
   验证注册
========================= */

const handleVerify = async () => {

  if (!verifyForm.code) {
    showMessage('请输入验证码', 'warning')
    return
  }

  if (!registerStore.challengeId) {
    showMessage('注册信息已失效，请重新注册', 'warning')
    return
  }

  try {

    loading.value = true

    const response = await request.post(
      '/api/auth/verify_register',
      null,
      {
        params: {
          code: verifyForm.code,
          challenge_id: registerStore.challengeId
        }
      }
    )

    console.log(
      '注册成功：',
      response.data
    )

    // 清除 challenge_id
    registerStore.clearChallengeId()

    // 返回登录页面
    router.push('/login')

  } catch (error) {

    console.error(
      '验证失败：',
      error
    )

    showMessage(
      error.response?.data?.detail || '验证失败',
      'warning'
    )

  } finally {

    loading.value = false

  }

}

</script>


<style scoped>

.background {
  width: 100%;
  min-height: 100vh;
  background: #f4f7fc;
}

.verify-wrapper {
  min-height: 100vh;

  display: flex;
  justify-content: center;
  align-items: center;

  padding: 24px;
  box-sizing: border-box;
}

.verify-card {
  width: 100%;
  max-width: 440px;

  padding: 40px;
  box-sizing: border-box;

  background: white;

  border-radius: 16px;

  box-shadow:
    0 8px 30px
    rgba(0, 0, 0, 0.08);
}

.form-item {
  margin: 30px 0 20px;
}

.form-item label {
  display: block;

  margin-bottom: 8px;
}

.form-item input {
  width: 100%;

  box-sizing: border-box;

  padding: 12px 14px;

  border: 1px solid #d8dbe5;
  border-radius: 8px;

  font-size: 16px;
}

.verify-btn {
  width: 100%;

  padding: 13px;

  border: none;
  border-radius: 8px;

  background: #3663e8;
  color: white;

  font-size: 16px;

  cursor: pointer;
}

.verify-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

</style>