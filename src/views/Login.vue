<template>
  <div class="background">

    <Message
      :visible="messageBox.visible"
      :message="messageBox.message"
      :type="messageBox.type"
    />

    <div class="login-wrapper">

      
      
      <div class="login-card">

        <!-- 语言切换 -->
        <!-- 如果 language 等于 'ch'，就给这个按钮加上 active 样式。-->
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

        <h2 class="title">{{ text.title }}</h2>
        <p class="subtitle">{{ text.subtitle }}</p>

        <div class="form-item">
          <label>{{ text.username }}</label>
          <input
            v-model="loginForm.username"
            type="text"
            :placeholder="text.usernamePlaceholder"
          />
        </div>

        <div class="form-item">
          <label>{{ text.password }}</label>
          <input
            v-model="loginForm.password"
            type="password"
            :placeholder="text.passwordPlaceholder"
            @keyup.enter="handleLogin"
          />

          <div class="register-link">
            <span>{{ text.noAccount }}</span>

            <button @click="goRegister">
              {{ text.register }}
            </button>
          </div>

          <!-- 忘记密码 -->
          <div class="forgot-password">
            <span @click="handleForgotPassword">
              {{ text.forgotPassword }}
            </span>
          </div>



        </div>

        <button class="login-btn" @click="handleLogin">
          {{ text.login }}
        </button>

      </div>
    </div>
  </div>
</template>


<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import Message from '../components/Message.vue'

/* =========================
   当前语言
   ch   = 中文
   en   = 英语
   thai = 泰语
========================= */

const language = ref('ch')


/* =========================
   语言内容
========================= */

const languageData = {

  ch: {
    title: '系统登录',
    subtitle: '请输入账号和密码',
    username: '账号',
    password: '密码',
    usernamePlaceholder: '请输入账号',
    passwordPlaceholder: '请输入密码',
    login: '登录',
    usernameRequired: '请输入账号',
    passwordRequired: '请输入密码',
    forgotPassword: '忘记密码？',
    noAccount: '没有账号？',
    register: '注册账号'
  },

  en: {
    title: 'System Login',
    subtitle: 'Please enter your username and password',
    username: 'Username',
    password: 'Password',
    usernamePlaceholder: 'Enter username',
    passwordPlaceholder: 'Enter password',
    login: 'Login',
    usernameRequired: 'Please enter your username',
    passwordRequired: 'Please enter your password',
    forgotPassword: 'Forgot password?',
    noAccount: "Don't have an account?",
    register: 'Register'
  },

  thai: {
    title: 'เข้าสู่ระบบ',
    subtitle: 'กรุณากรอกชื่อผู้ใช้และรหัสผ่าน',
    username: 'ชื่อผู้ใช้',
    password: 'รหัสผ่าน',
    usernamePlaceholder: 'กรุณากรอกชื่อผู้ใช้',
    passwordPlaceholder: 'กรุณากรอกรหัสผ่าน',
    login: 'เข้าสู่ระบบ',
    usernameRequired: 'กรุณากรอกชื่อผู้ใช้',
    passwordRequired: 'กรุณากรอกรหัสผ่าน',
    forgotPassword: 'ลืมรหัสผ่าน?',
    noAccount: 'ยังไม่มีบัญชี?',
    register: 'สมัครบัญชี'
  }

}

const router = useRouter()
const goRegister = () => {
  router.push('/register')
}


/* 根据 language 自动获取语言 */

const text = computed(() => {
  return languageData[language.value]
})

/* 定义message */
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


/* 登录数据 */
const loginForm = reactive({
  username: '',
  password: ''
})


/* 登录 */
const handleLogin = () => {

  if (!loginForm.username) {
    showMessage(text.value.usernameRequired, 'warning')
    return
  }

  if (!loginForm.password) {
    showMessage(text.value.passwordRequired, 'warning')
    return
  }

  // 跳转首页
  router.push('/home')
}

const handleForgotPassword = () => {
  router.push('/forgot-password')
}

</script>

<style scoped>

.background {
  width: 100%;
  min-height: 100vh;
  min-height: 100dvh;
  background: #f4f7fc;
}

.login-wrapper {
  width: 100%;
  min-height: 100vh;
  min-height: 100dvh;

  display: flex;
  justify-content: center;
  align-items: center;

  box-sizing: border-box;
  padding: 24px;
}

.login-card {
  position: relative;

  width: 100%;
  max-width: 400px;

  padding: clamp(24px, 4vw, 40px);

  box-sizing: border-box;

  background: #ffffff;
  border-radius: 16px;

  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
}


/* 语言切换 */

.language {
  display: flex;
  justify-content: flex-end;
  gap: 5px;

  margin-bottom: 20px;
}

.language button {
  padding: 5px 8px;

  border: none;
  border-radius: 5px;

  background: transparent;
  color: #8a94a6;

  cursor: pointer;
}

.language button:hover {
  color: #3663e8;
}

.language button.active {
  background: #3663e8;
  color: #ffffff;
}


/* 标题 */

.title {
  margin: 0;

  text-align: center;

  font-size: clamp(22px, 3vw, 26px);

  color: #1f2937;
}

.subtitle {
  margin: 10px 0 32px;

  text-align: center;

  font-size: 14px;

  color: #8a94a6;
}


/* 表单 */

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

  border: 1px solid #d8dbe5;
  border-radius: 8px;

  font-size: 16px;

  outline: none;

  transition: 0.2s;
}

.form-item input:focus {
  border-color: #3663e8;

  box-shadow: 0 0 0 3px rgba(54, 99, 232, 0.1);
}

.password-item {
  margin-bottom: 28px;
}


/* 登录按钮 */

.login-btn {
  width: 100%;

  margin-top: 12px;
  padding: 13px;

  background: #3663e8;
  color: #ffffff;

  border: none;
  border-radius: 8px;

  font-size: 16px;

  cursor: pointer;

  transition: 0.2s;
}

.login-btn:hover {
  background: #2c52cc;
}

.login-btn:active {
  transform: scale(0.98);
}


/* 平板 */

@media (max-width: 768px) {

  .login-wrapper {
    padding: 20px;
  }

}


/* 手机 */

@media (max-width: 480px) {

  .login-wrapper {
    padding: 16px;
  }

  .login-card {
    padding: 28px 20px;
    border-radius: 12px;
  }

  .subtitle {
    margin-bottom: 26px;
  }

  .form-item {
    margin-bottom: 16px;
  }

}

/* 忘记密码 */
.forgot-password {
  width: 100%;
  display: flex;
  justify-content: flex-end;

  margin-top: 12px;
  margin-bottom: 24px;
}

.forgot-password span {
  color: #3663e8;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  /* transition: color 0.2s ease; */
}

.forgot-password span:hover {
  color: #2c52cc;
  text-decoration: underline;
}



/* 手机 */

@media (max-width: 480px) {
  .forgot-password {
    margin-top: 8px;
    margin-bottom: 22px;
  }

  .forgot-password button {
    padding: 5px 8px;
    font-size: 13px;
  }
}

.register-link {
  width: 100%;

  margin-top: 20px;

  display: flex;
  justify-content: center;
  align-items: center;

  gap: 6px;

  font-size: 14px;
  color: #8a94a6;
}

.register-link button {
  padding: 0;

  border: none;

  background: transparent;

  color: #3663e8;

  font-size: 14px;

  cursor: pointer;
}

.register-link button:hover {
  color: #2c52cc;
  text-decoration: underline;
}


/* 超小屏幕 */

@media (max-width: 360px) {

  .login-wrapper {
    padding: 12px;
  }

  .login-card {
    padding: 24px 16px;
  }

  .register-link {
    margin-top: 16px;

    flex-wrap: wrap;

    font-size: 13px;
  }

  .register-link button {
    font-size: 13px;
  }

}




</style>