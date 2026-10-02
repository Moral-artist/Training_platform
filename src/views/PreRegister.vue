/* =========================
PreRegister.vue
    ↓
填写用户名 / 邮箱 / 密码
    ↓
POST /api/auth/pre_register
    ↓
获得 challenge_id
    ↓
Pinia 保存
    ↓
VerifyEmail.vue
    ↓
输入验证码
    ↓
正式注册
========================= */



<template>
  <div class="background">
    <Message
      :visible="messageBox.visible"
      :message="messageBox.message"
      :type="messageBox.type"
    />

    <div class="register-wrapper">

      <div class="register-card">

        <!-- 语言切换 -->
        <div class="language">
          <button
            :class="{ active: language === 'ch' }"
            @click="language = 'ch'"
          >
            中文
          </button>

          <button
            :class="{ active: language === 'en' }"
            @click="language = 'en'"
          >
            EN
          </button>

          <button
            :class="{ active: language === 'thai' }"
            @click="language = 'thai'"
          >
            ไทย
          </button>
        </div>


        <!-- 标题 -->
        <h2 class="title">
          {{ text.title }}
        </h2>

        <p class="subtitle">
          {{ text.subtitle }}
        </p>

        <!-- 用户名 -->
        <div class="form-item">
          <label>
            {{ text.userName }}
          </label>

          <input
            v-model="registerForm.user_name"
            type="text"
            :placeholder="text.userNamePlaceholder"
          />
        </div>


        <!-- 邮箱 -->
        <div class="form-item">
          <label>
            {{ text.email }}
          </label>

          <input
            v-model="registerForm.email"
            type="text"
            :placeholder="text.emailPlaceholder"
          />
        </div>

        <!-- 岗位 -->
        <div class="form-item">

          <label>
            岗位
          </label>

          <select v-model="registerForm.character">

            <option value="" disabled>
              请选择岗位
            </option>

            <option value="engineer">
              工程师
            </option>

            <option value="operator">
              值班员
            </option>

            <option value="shiftleader">
              值班长
            </option>

          </select>

        </div>


        <!-- 密码 -->
        <div class="form-item">
          <label>
            {{ text.password }}
          </label>

          <input
            v-model="registerForm.password"
            type="password"
            :placeholder="text.passwordPlaceholder"
          />
        </div>


        <!-- 确认密码 -->
        <div class="form-item">
          <label>
            {{ text.confirmPassword }}
          </label>

          <input
            v-model="registerForm.confirmPassword"
            type="password"
            :placeholder="text.confirmPasswordPlaceholder"
            @keyup.enter="handleRegister"
          />
        </div>


        <!-- 注册按钮 -->
        <!--防止用户-->
        <button
          class="register-btn"
          :disabled="loading"
          @click="handleRegister"
        >
          {{ loading ? '...' : text.register }}
        </button>


        <!-- 返回登录 -->
        <div class="login-link">
          <span>{{ text.haveAccount }}</span>

          <button @click="goLogin">
            {{ text.goLogin }}
          </button>
        </div>

      </div>

    </div>
  </div>
</template>


<script setup>

import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import Message from '../components/Message.vue'
import request from '../api/request'
import { useRegisterStore } from '../stores/register'


/* =========================
   Router
========================= */

const router = useRouter()


/* =========================
   当前语言
========================= */

const language = ref('ch')


/* =========================
   多语言
========================= */

const languageData = {

  ch: {
    title: '账号注册',
    subtitle: '请输入注册信息',
    userName: '用户名',
    userNamePlaceholder: '请输入用户名',
    userNameRequired: '请输入用户名',

    email: '邮箱',
    password: '密码',
    confirmPassword: '确认密码',

    emailPlaceholder: '请输入邮箱',
    passwordPlaceholder: '请输入密码',
    confirmPasswordPlaceholder: '请再次输入密码',

    register: '注册',
    registerFailed: '注册失败',

    haveAccount: '已有账号？',
    goLogin: '返回登录',

    emailRequired: '请输入邮箱',
    passwordRequired: '请输入密码',
    confirmPasswordRequired: '请确认密码',
    passwordNotMatch: '两次输入的密码不一致'
  },


  en: {
    title: 'Register',
    subtitle: 'Please enter your information',

    email: 'Email',
    password: 'Password',
    confirmPassword: 'Confirm Password',
    userName: 'Username',
    userNamePlaceholder: 'Enter username',
    userNameRequired: 'Please enter your username',

    emailPlaceholder: 'Enter email',
    passwordPlaceholder: 'Enter password',
    confirmPasswordPlaceholder: 'Enter password again',

    register: 'Register',
    registerFailed: 'Registration failed',

    haveAccount: 'Already have an account?',
    goLogin: 'Login',

    emailRequired: 'Please enter your email',
    passwordRequired: 'Please enter your password',
    confirmPasswordRequired: 'Please confirm your password',
    passwordNotMatch: 'Passwords do not match'
  },


  thai: {
    title: 'สมัครบัญชี',
    subtitle: 'กรุณากรอกข้อมูลสำหรับการสมัคร',

    email: 'อีเมล',
    password: 'รหัสผ่าน',
    confirmPassword: 'ยืนยันรหัสผ่าน',

    userName: 'ชื่อผู้ใช้',
    userNamePlaceholder: 'กรุณากรอกชื่อผู้ใช้',
    userNameRequired: 'กรุณากรอกชื่อผู้ใช้',

    emailPlaceholder: 'กรุณากรอกอีเมล',
    passwordPlaceholder: 'กรุณากรอกรหัสผ่าน',
    confirmPasswordPlaceholder: 'กรุณากรอกรหัสผ่านอีกครั้ง',

    register: 'สมัคร',
    registerFailed: 'สมัครไม่สำเร็จ',

    haveAccount: 'มีบัญชีแล้ว?',
    goLogin: 'เข้าสู่ระบบ',

    emailRequired: 'กรุณากรอกอีเมล',
    passwordRequired: 'กรุณากรอกรหัสผ่าน',
    confirmPasswordRequired: 'กรุณายืนยันรหัสผ่าน',
    passwordNotMatch: 'รหัสผ่านไม่ตรงกัน'
  }

}


/* =========================
   当前语言文字
========================= */

const text = computed(() => {
  return languageData[language.value]
})


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
   注册数据
========================= */

const registerStore = useRegisterStore()

const registerForm = reactive({
  user_name: '',
  email: '',
  password: '',
  confirmPassword: '',
  character: ''
})


/* =========================
   注册
========================= */



const handleRegister = async () => {

  // 用户名
  if (!registerForm.user_name) {
    showMessage(text.value.userNameRequired, 'warning')
    return
  }

  if (!registerForm.email) {
    showMessage(text.value.emailRequired, 'warning')
    return
  }


  if (!registerForm.password) {
    showMessage(text.value.passwordRequired, 'warning')
    return
  }


  if (!registerForm.confirmPassword) {
    showMessage(text.value.confirmPasswordRequired, 'warning')
    return
  }


  if (
    registerForm.password !== registerForm.confirmPassword
  ) {
    showMessage(text.value.passwordNotMatch, 'warning')
    return
  }

  if (!registerForm.character) {
    showMessage('请选择岗位', 'warning')
    return
  }


  try {

    loading.value = true

    const response = await request.post(
    '/api/auth/pre_register',
    {
        user_name: registerForm.user_name,
        email: registerForm.email,
        password: registerForm.password,
        character: registerForm.character
      }
    )

    // 可删
    console.log('后端返回：', response.data)

    // 保存 challenge_id
    registerStore.setChallengeId(
      response.data.challenge_id
    )

    // 可删
    console.log(
      'challenge_id:',
      registerStore.challengeId
    )

    // 去邮箱验证码页面
    router.push('/verify_register')

  } catch (error) {

    console.error(
      '注册失败：',
      error
    )

    // 如果后端有返回 detail，就显示后端的 detail；如果没有，就显示中文“注册失败”
    showMessage(
      error.response?.data?.detail || text.value.registerFailed,
      'warning'
    )
  }
}


/* =========================
   loading
========================= */
const loading = ref(false)


/* =========================
   返回登录
========================= */

const goLogin = () => {

  router.push('/login')

}

</script>


<style scoped>

/* =========================
   背景
========================= */

.background {

  width: 100%;

  min-height: 100vh;
  min-height: 100dvh;

  background: #f4f7fc;

}


/* =========================
   页面居中
========================= */

.register-wrapper {

  width: 100%;

  min-height: 100vh;
  min-height: 100dvh;

  display: flex;

  justify-content: center;

  align-items: center;

  box-sizing: border-box;

  padding: 24px;

}


/* =========================
   注册卡片
========================= */

.register-card {

  width: 100%;

  max-width: 440px;

  padding: 40px;

  box-sizing: border-box;

  background: #ffffff;

  border-radius: 16px;

  box-shadow:
    0 8px 30px
    rgba(0, 0, 0, 0.08);

}


/* =========================
   语言
========================= */

.language {

  display: flex;

  justify-content: flex-end;

  gap: 6px;

  margin-bottom: 26px;

}


.language button {

  padding: 6px 10px;

  border: none;

  border-radius: 6px;

  background: transparent;

  color: #8a94a6;

  font-size: 14px;

  cursor: pointer;

}


.language button.active {

  background: #3663e8;

  color: #ffffff;

}


/* =========================
   标题
========================= */

.title {

  margin: 0;

  text-align: center;

  font-size: 26px;

  color: #1f2937;

}


.subtitle {

  margin:

    10px
    0
    32px;

  text-align: center;

  font-size: 14px;

  color: #8a94a6;

}


/* =========================
   表单
========================= */

.form-item {

  width: 100%;

  margin-bottom: 20px;

}


.form-item label {

  display: block;

  margin-bottom: 8px;

  font-size: 14px;

  color: #374151;

}


.form-item input {

  width: 100%;

  box-sizing: border-box;

  padding: 12px 14px;

  border:
    1px solid
    #d8dbe5;

  border-radius: 8px;

  font-size: 16px;

  outline: none;

  transition: 0.2s;

}


.form-item input:focus {

  border-color: #3663e8;

  box-shadow:
    0 0 0 3px
    rgba(54, 99, 232, 0.1);

}


/* =========================
   注册按钮
========================= */

.register-btn {

  width: 100%;

  margin-top: 8px;

  padding: 13px;

  border: none;

  border-radius: 8px;

  background: #3663e8;

  color: #ffffff;

  font-size: 16px;

  cursor: pointer;

  transition: 0.2s;

}


.register-btn:hover {

  background: #2c52cc;

}


.register-btn:active {

  transform: scale(0.98);

}


/* =========================
   返回登录
========================= */

.login-link {

  margin-top: 20px;

  display: flex;

  justify-content: center;

  align-items: center;

  gap: 5px;

  font-size: 14px;

  color: #8a94a6;

}


.login-link button {

  padding: 0;

  border: none;

  background: transparent;

  color: #3663e8;

  font-size: 14px;

  cursor: pointer;

}


.login-link button:hover {

  text-decoration: underline;

}


/* =========================
   手机响应式
========================= */

@media (max-width: 480px) {

  .register-wrapper {

    padding: 16px;

    align-items: center;

  }


  .register-card {

    max-width: 100%;

    padding: 28px 20px;

    border-radius: 12px;

  }


  .language {

    margin-bottom: 22px;

  }


  .title {

    font-size: 22px;

  }


  .subtitle {

    margin-bottom: 26px;

  }


  .form-item {

    margin-bottom: 16px;

  }

  .login-link {

    flex-wrap: wrap;

  }

}

</style>