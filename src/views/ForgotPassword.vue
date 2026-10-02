<template>
  <main class="page-shell">
    <Message
      :visible="messageBox.visible"
      :message="messageBox.message"
      :type="messageBox.type"
    />

    <section class="reset-card" aria-labelledby="reset-title">
      <div class="card-topbar">
        <button class="back-link" type="button" @click="goToLogin">
          <span aria-hidden="true">←</span> {{ text.backToLogin }}
        </button>
        <div class="language-switch" :aria-label="text.languageSetting">
          <button
            v-for="option in languages"
            :key="option.value"
            type="button"
            :class="{ active: language === option.value }"
            :aria-pressed="language === option.value"
            @click="language = option.value"
          >
            {{ option.label }}
          </button>
        </div>
      </div>

      <div class="step-mark" aria-hidden="true">{{ step === 'email' ? '1' : '2' }}</div>
      <h1 id="reset-title">{{ step === 'email' ? text.resetTitle : text.verifyTitle }}</h1>
      <p class="intro">
        {{ step === 'email'
          ? text.resetIntro
          : text.verifyIntro(form.email) }}
      </p>

      <form v-if="step === 'email'" class="reset-form" @submit.prevent="sendResetCode">
        <div class="form-field">
          <label for="reset-email">{{ text.email }}</label>
          <input
            id="reset-email"
            v-model.trim="form.email"
            type="email"
            autocomplete="email"
            :placeholder="text.emailPlaceholder"
            required
            :disabled="loading"
          />
        </div>

        <div class="form-field">
          <label for="new-password">{{ text.newPassword }}</label>
          <input
            id="new-password"
            v-model="form.newPassword"
            type="password"
            autocomplete="new-password"
            :placeholder="text.newPasswordPlaceholder"
            required
            :disabled="loading"
          />
        </div>

        <div class="form-field">
          <label for="confirm-password">{{ text.confirmPassword }}</label>
          <input
            id="confirm-password"
            v-model="form.confirmPassword"
            type="password"
            autocomplete="new-password"
            :placeholder="text.confirmPasswordPlaceholder"
            required
            :disabled="loading"
            @keyup.enter="sendResetCode"
          />
        </div>

        <button class="primary-button" type="submit" :disabled="loading">
          {{ loading ? text.sending : text.sendCode }}
        </button>
      </form>

      <form v-else class="reset-form" @submit.prevent="verifyResetCode">
        <div class="form-field">
          <label for="reset-code">{{ text.emailCode }}</label>
          <input
            id="reset-code"
            v-model.trim="form.code"
            type="text"
            inputmode="numeric"
            autocomplete="one-time-code"
            :placeholder="text.codePlaceholder"
            required
            :disabled="loading"
            @keyup.enter="verifyResetCode"
          />
        </div>

        <button class="primary-button" type="submit" :disabled="loading">
          {{ loading ? text.verifying : text.confirmReset }}
        </button>
        <button class="secondary-button" type="button" :disabled="loading" @click="step = 'email'">
          {{ text.editEmailOrPassword }}
        </button>
      </form>
    </section>
  </main>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import request from '../api/request.js'
import Message from '../components/Message.vue'

const router = useRouter()
const language = ref('ch')
const languages = [
  { value: 'ch', label: '中文' },
  { value: 'en', label: 'EN' },
  { value: 'thai', label: 'ไทย' }
]
const step = ref('email')
const loading = ref(false)
const challengeId = ref('')

const translations = {
  ch: {
    languageSetting: '语言设置',
    backToLogin: '返回登录',
    resetTitle: '重置密码',
    verifyTitle: '验证邮箱',
    resetIntro: '填写账号邮箱和新密码，我们会向该邮箱发送验证码。',
    verifyIntro: email => `验证码已发送至 ${email}，请输入验证码以完成密码重置。`,
    email: '邮箱',
    emailPlaceholder: '请输入注册邮箱',
    newPassword: '新密码',
    newPasswordPlaceholder: '请输入新密码',
    confirmPassword: '确认新密码',
    confirmPasswordPlaceholder: '请再次输入新密码',
    sending: '正在发送…',
    sendCode: '发送验证码',
    emailCode: '邮箱验证码',
    codePlaceholder: '请输入邮箱收到的验证码',
    verifying: '正在验证…',
    confirmReset: '确认重置密码',
    editEmailOrPassword: '修改邮箱或密码',
    emailRequired: '请输入注册邮箱',
    newPasswordRequired: '请输入新密码',
    passwordMismatch: '两次输入的新密码不一致',
    missingChallenge: '验证码请求已提交，但服务器未返回 challenge_id，请检查后端响应格式。',
    codeSent: '验证码已发送，请查收邮箱。',
    sendFailed: '发送验证码失败，请稍后重试。',
    codeRequired: '请输入邮箱验证码',
    expired: '重置请求已失效，请重新填写邮箱和新密码。',
    resetSuccess: '密码重置成功，请使用新密码登录。',
    verifyFailed: '验证码校验失败，请检查验证码后重试。'
  },
  en: {
    languageSetting: 'Language settings',
    backToLogin: 'Back to login',
    resetTitle: 'Reset password',
    verifyTitle: 'Verify your email',
    resetIntro: 'Enter your account email and a new password. We’ll send a verification code to that email.',
    verifyIntro: email => `A verification code was sent to ${email}. Enter it to finish resetting your password.`,
    email: 'Email',
    emailPlaceholder: 'Enter your registered email',
    newPassword: 'New password',
    newPasswordPlaceholder: 'Enter a new password',
    confirmPassword: 'Confirm new password',
    confirmPasswordPlaceholder: 'Enter the new password again',
    sending: 'Sending…',
    sendCode: 'Send verification code',
    emailCode: 'Email verification code',
    codePlaceholder: 'Enter the code sent to your email',
    verifying: 'Verifying…',
    confirmReset: 'Reset password',
    editEmailOrPassword: 'Change email or password',
    emailRequired: 'Enter your registered email.',
    newPasswordRequired: 'Enter a new password.',
    passwordMismatch: 'The passwords do not match.',
    missingChallenge: 'The server did not return a challenge_id. Please check the backend response.',
    codeSent: 'The verification code was sent. Check your email.',
    sendFailed: 'Could not send the verification code. Please try again.',
    codeRequired: 'Enter the email verification code.',
    expired: 'This reset request has expired. Enter your email and new password again.',
    resetSuccess: 'Your password has been reset. You can now sign in with the new password.',
    verifyFailed: 'Could not verify the code. Check it and try again.'
  },
  thai: {
    languageSetting: 'การตั้งค่าภาษา',
    backToLogin: 'กลับไปหน้าเข้าสู่ระบบ',
    resetTitle: 'ตั้งรหัสผ่านใหม่',
    verifyTitle: 'ยืนยันอีเมล',
    resetIntro: 'กรอกอีเมลบัญชีและรหัสผ่านใหม่ เราจะส่งรหัสยืนยันไปยังอีเมลนี้',
    verifyIntro: email => `ส่งรหัสยืนยันไปที่ ${email} แล้ว กรอกรหัสเพื่อดำเนินการตั้งรหัสผ่านใหม่ให้เสร็จสิ้น`,
    email: 'อีเมล',
    emailPlaceholder: 'กรอกอีเมลที่ลงทะเบียนไว้',
    newPassword: 'รหัสผ่านใหม่',
    newPasswordPlaceholder: 'กรอกรหัสผ่านใหม่',
    confirmPassword: 'ยืนยันรหัสผ่านใหม่',
    confirmPasswordPlaceholder: 'กรอกรหัสผ่านใหม่อีกครั้ง',
    sending: 'กำลังส่ง…',
    sendCode: 'ส่งรหัสยืนยัน',
    emailCode: 'รหัสยืนยันทางอีเมล',
    codePlaceholder: 'กรอกรหัสที่ได้รับทางอีเมล',
    verifying: 'กำลังตรวจสอบ…',
    confirmReset: 'ยืนยันการตั้งรหัสผ่านใหม่',
    editEmailOrPassword: 'แก้ไขอีเมลหรือรหัสผ่าน',
    emailRequired: 'กรอกอีเมลที่ลงทะเบียนไว้',
    newPasswordRequired: 'กรอกรหัสผ่านใหม่',
    passwordMismatch: 'รหัสผ่านทั้งสองช่องไม่ตรงกัน',
    missingChallenge: 'เซิร์ฟเวอร์ไม่ได้ส่ง challenge_id กลับมา โปรดตรวจสอบการตอบกลับของระบบ',
    codeSent: 'ส่งรหัสยืนยันแล้ว โปรดตรวจสอบอีเมล',
    sendFailed: 'ส่งรหัสยืนยันไม่สำเร็จ โปรดลองอีกครั้ง',
    codeRequired: 'กรอกรหัสยืนยันทางอีเมล',
    expired: 'คำขอตั้งรหัสผ่านหมดอายุแล้ว โปรดกรอกอีเมลและรหัสผ่านใหม่อีกครั้ง',
    resetSuccess: 'ตั้งรหัสผ่านใหม่สำเร็จ เข้าสู่ระบบด้วยรหัสผ่านใหม่ได้เลย',
    verifyFailed: 'ตรวจสอบรหัสไม่สำเร็จ โปรดตรวจสอบแล้วลองอีกครั้ง'
  }
}

const text = computed(() => translations[language.value])

const form = reactive({
  email: '',
  newPassword: '',
  confirmPassword: '',
  code: ''
})

const messageBox = reactive({
  visible: false,
  message: '',
  type: 'warning'
})

let messageTimer

const showMessage = (message, type = 'warning') => {
  messageBox.message = message
  messageBox.type = type
  messageBox.visible = true
  clearTimeout(messageTimer)
  messageTimer = setTimeout(() => {
    messageBox.visible = false
  }, 3000)
}

const responseMessage = (error, fallback) => {
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map(item => item.msg).filter(Boolean).join('；') || fallback
  return fallback
}

const sendResetCode = async () => {
  if (!form.email) {
    showMessage(text.value.emailRequired)
    return
  }
  if (!form.newPassword) {
    showMessage(text.value.newPasswordRequired)
    return
  }
  if (form.newPassword !== form.confirmPassword) {
    showMessage(text.value.passwordMismatch)
    return
  }

  loading.value = true
  try {
    const response = await request.post('/api/auth/pre_reset', {
      email: form.email,
      new_password: form.newPassword
    })

    // Some backend versions return the challenge id directly as a string;
    // others return it in a JSON object, like the registration endpoint.
    challengeId.value = typeof response.data === 'string'
      ? response.data
      : response.data?.challenge_id || response.data?.data?.challenge_id || ''
    if (!challengeId.value) {
      showMessage(text.value.missingChallenge, 'error')
      return
    }

    step.value = 'code'
    const message = typeof response.data === 'object' ? response.data?.message : ''
    showMessage(message || text.value.codeSent, 'success')
  } catch (error) {
    showMessage(responseMessage(error, text.value.sendFailed), 'error')
  } finally {
    loading.value = false
  }
}

const verifyResetCode = async () => {
  if (!form.code) {
    showMessage(text.value.codeRequired)
    return
  }
  if (!challengeId.value) {
    showMessage(text.value.expired, 'error')
    step.value = 'email'
    return
  }

  loading.value = true
  try {
    const response = await request.post('/api/auth/verify_reset', null, {
      params: {
        code: form.code,
        challenge_id: challengeId.value
      }
    })

    const message = typeof response.data === 'object' ? response.data?.message : ''
    showMessage(message || text.value.resetSuccess, 'success')
    window.setTimeout(() => router.push({ name: 'Login' }), 900)
  } catch (error) {
    showMessage(responseMessage(error, text.value.verifyFailed), 'error')
  } finally {
    loading.value = false
  }
}

const goToLogin = () => router.push({ name: 'Login' })
</script>

<style scoped>
.page-shell {
  min-height: 100vh;
  min-height: 100dvh;
  display: grid;
  place-items: center;
  box-sizing: border-box;
  padding: 24px;
  background: #f4f7fc;
}

.reset-card {
  width: 100%;
  max-width: 440px;
  box-sizing: border-box;
  padding: 32px clamp(22px, 5vw, 40px) 40px;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
}

.card-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.back-link {
  padding: 0;
  border: 0;
  background: transparent;
  color: #667085;
  font-size: 14px;
  cursor: pointer;
}

.language-switch {
  display: flex;
  gap: 3px;
  padding: 3px;
  border-radius: 7px;
  background: #f3f5f9;
}

.language-switch button {
  padding: 5px 7px;
  border: 0;
  border-radius: 5px;
  background: transparent;
  color: #7b8494;
  font-size: 12px;
  cursor: pointer;
}

.language-switch button:hover {
  color: #3663e8;
}

.language-switch button.active {
  background: #3663e8;
  color: #fff;
}

.back-link:hover,
.secondary-button:hover {
  color: #2c52cc;
}

.step-mark {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  margin: 28px auto 14px;
  border-radius: 50%;
  background: #edf2ff;
  color: #3663e8;
  font-weight: 700;
}

h1 {
  margin: 0;
  color: #1f2937;
  font-size: 25px;
  text-align: center;
}

.intro {
  margin: 10px 0 28px;
  color: #8a94a6;
  font-size: 14px;
  line-height: 1.7;
  text-align: center;
}

.form-field {
  margin-bottom: 18px;
}

.form-field label {
  display: block;
  margin-bottom: 8px;
  color: #374151;
  font-size: 14px;
}

.form-field input {
  width: 100%;
  box-sizing: border-box;
  padding: 12px 14px;
  border: 1px solid #d8dbe5;
  border-radius: 8px;
  outline: none;
  font-size: 16px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-field input:focus {
  border-color: #3663e8;
  box-shadow: 0 0 0 3px rgba(54, 99, 232, 0.1);
}

.form-field input:disabled {
  background: #f8fafc;
}

.primary-button,
.secondary-button {
  width: 100%;
  border: 0;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
}

.primary-button {
  margin-top: 8px;
  padding: 13px;
  background: #3663e8;
  color: white;
  transition: background 0.2s, transform 0.2s;
}

.primary-button:hover:not(:disabled) {
  background: #2c52cc;
}

.primary-button:active:not(:disabled) {
  transform: scale(0.99);
}

.primary-button:disabled,
.secondary-button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.secondary-button {
  margin-top: 14px;
  padding: 8px;
  background: transparent;
  color: #667085;
}

@media (max-width: 480px) {
  .page-shell {
    padding: 16px;
  }

  .reset-card {
    padding-top: 26px;
    border-radius: 12px;
  }
}
</style>
