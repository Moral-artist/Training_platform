<template>
  <div class="page">

    <!-- 左侧导航 -->
    <aside class="sidebar">

      <!-- Logo -->
      <div class="logo-area">
        <div class="logo-icon">T</div>

        <div>
          <div class="logo-title">培训平台</div>
          <div class="logo-subtitle">Training System</div>
        </div>
      </div>


      <!-- 用户信息 -->
      <div class="user-card">

        <div class="avatar">
          {{ user.name.charAt(0) }}
        </div>

        <div>
          <div class="user-name">
            {{ user.name }}
          </div>

          <div class="user-role">
            学员
          </div>
        </div>

      </div>


      <!-- 菜单 -->
      <nav class="menu">

        <div class="menu-item active">
          <span class="menu-icon">⌂</span>
          首页
        </div>


        <div class="menu-title">
          管理课程
        </div>
        
        <div
          v-if="isManager"
          class="sub-item"
          @click="goSystemCreate"
        >
          系统创建
        </div>

        <div
          v-if="isManager"
          class="sub-item"
          @click="goLessonCreate"
        >
          课程创建
        </div>


        <RouterLink v-if="user.role === 'administer'" class="sub-item" to="/lessons/accessmanage">课程授权</RouterLink>

        <div class="menu-title">
          我的课程
        </div>

        <div class="sub-item">
          在学课程
        </div>

        <div class="sub-item">
          已完成课程
        </div>


        <div class="menu-title">
          学习任务
        </div>

        <div class="sub-item">
          待学任务
        </div>

        <div class="sub-item">
          考试测验
        </div>

        <div class="sub-item">
          作业提交
        </div>

        <div class="menu-title">
          个人中心
        </div>

        <div class="sub-item">
          个人资料
        </div>

        <div class="sub-item">
          学习档案
        </div>

        <div class="sub-item">
          修改密码
        </div>


        <div class="menu-item">
          <span class="menu-icon">?</span>
          帮助中心
        </div>

      </nav>


      <div
        class="logout"
        @click="logout"
      >
        退出登录
      </div>

    </aside>



    <!-- 右侧内容 -->
    <main class="main-content">

      <!-- 顶部 -->
      <header class="header">

        <div>
          <h1>首页</h1>

          <p>
            欢迎回来，{{ user.name }}
          </p>
        </div>


        <!-- 语言 -->
        <div class="languages">

          <button
            class="language"
            :class="{ 'active-language': language === 'zh' }"
            @click="changeLanguage('zh')"
          >
            中文
          </button>

          <button
            class="language"
            :class="{ 'active-language': language === 'en' }"
            @click="changeLanguage('en')"
          >
            EN
          </button>

          <button
            class="language"
            :class="{ 'active-language': language === 'th' }"
            @click="changeLanguage('th')"
          >
            ไทย
          </button>

        </div>

      </header>



      <!-- 学习进度 -->
      <section class="progress-section">

        <div class="progress-header">

          <div>
            <h2>学习进度</h2>

            <p>
              查看当前培训学习进度
            </p>
          </div>

          <div class="progress-percent">
            {{ learningProgress }}%
          </div>

        </div>


        <div class="big-progress">

          <div
            class="big-progress-value"
            :style="{ width: learningProgress + '%' }"
          ></div>

        </div>


        <div class="progress-bottom">

          <span>
            已完成 {{ completedLessons }} 个培训视频
          </span>

          <span>
            共 {{ totalLessons }} 个培训视频
          </span>

        </div>

      </section>



      <!-- 专业 -->
      <section class="major-section">

        <div class="section-title">

          <h2>专业培训</h2>

          <p>
            请选择专业
          </p>

        </div>


        <div class="major-grid">

          <div
            v-for="major in majors"
            :key="major.code"
            class="major-card"
            @click="openMajor(major)"
          >

            <div
              class="major-icon"
              :class="major.className"
            >
              {{ major.short }}
            </div>


            <div class="major-info">

              <div class="major-name">
                {{ major.name }}
              </div>

              <div class="major-en">
                {{ major.english }}
              </div>


              <div class="lesson-number">
                {{ major.lessonCount }} 个培训视频
              </div>


              <!-- 专业学习进度 -->
              <div class="major-progress">

                <div class="progress-text">

                  <span>
                    学习进度
                  </span>

                  <span>
                    {{ major.progress }}%
                  </span>

                </div>


                <div class="small-progress">

                  <div
                    class="small-progress-value"
                    :style="{ width: major.progress + '%' }"
                  ></div>

                </div>

              </div>

            </div>


            <div class="arrow">
              ›
            </div>

          </div>

        </div>

      </section>

    </main>

  </div>
</template>


<script setup>

import {
  ref,
  computed,
  reactive,
  onMounted
} from 'vue'
import { useRouter } from 'vue-router'
import request from '../api/request'


const language = ref('zh')

const languageData = {

  zh: {
    backHome: '返回首页',
    professionalTraining: '专业培训',
    training: '培训',
    progress: '专业学习进度',
    totalVideos: '培训视频',
    videos: '个视频',
    lesson: '第',
    lessonEnd: '课',
    learningProgress: '学习进度',
    startLearning: '开始学习',
    continueLearning: '继续学习',
    learnAgain: '重新学习',
    loading: '正在加载...',
    empty: '暂无培训视频',
    previous: '上一页',
    next: '下一页',
    page: '页',
    total: '共'
  },

  en: {
    backHome: 'Back to Home',
    professionalTraining: 'Professional Training',
    training: 'Training',
    progress: 'Learning Progress',
    totalVideos: 'Training Videos',
    videos: 'videos',
    lesson: 'Lesson',
    lessonEnd: '',
    learningProgress: 'Progress',
    startLearning: 'Start',
    continueLearning: 'Continue',
    learnAgain: 'Review',
    loading: 'Loading...',
    empty: 'No training videos',
    previous: 'Previous',
    next: 'Next',
    page: 'Page',
    total: 'Total'
  },

  th: {
    backHome: 'กลับหน้าหลัก',
    professionalTraining: 'การฝึกอบรมวิชาชีพ',
    training: 'การฝึกอบรม',
    progress: 'ความคืบหน้าการเรียน',
    totalVideos: 'วิดีโอฝึกอบรม',
    videos: 'วิดีโอ',
    lesson: 'บทที่',
    lessonEnd: '',
    learningProgress: 'ความคืบหน้า',
    startLearning: 'เริ่มเรียน',
    continueLearning: 'เรียนต่อ',
    learnAgain: 'เรียนอีกครั้ง',
    loading: 'กำลังโหลด...',
    empty: 'ไม่มีวิดีโอฝึกอบรม',
    previous: 'ก่อนหน้า',
    next: 'ถัดไป',
    page: 'หน้า',
    total: 'ทั้งหมด'
  }

}

const text = computed(() => {
  return languageData[language.value]
})

function changeLanguage(lang) {
  language.value = lang
}

const router = useRouter()

const goSystemCreate = ()=>{
  router.push('/lessons/systemcreate')
}

const goLessonCreate=()=>{
  router.push('/lessons/lessoncreate')
}

const user = ref({
  name: '',
  role: ''
})


/*
  后面这里从 FastAPI 获取
*/
const completedLessons = ref(18)

const totalLessons = ref(40)

const learningProgress = ref(45)


/*
  四个专业

  后面也可以从 FastAPI 获取
*/
const majors = ref([

  {
    name: '电气',
    english: 'Electrical',
    code: 'electrical',
    short: 'E',
    lessonCount: 12,
    progress: 60,
    className: 'electrical'
  },

  {
    name: '暖通',
    english: 'HVAC',
    code: 'hvac',
    short: 'H',
    lessonCount: 12,
    progress: 45,
    className: 'hvac'
  },

  {
    name: '弱电',
    english: 'ELV',
    code: 'elv',
    short: 'L',
    lessonCount: 8,
    progress: 40,
    className: 'elv'
  },

  {
    name: '消防',
    english: 'Fire',
    code: 'fire',
    short: 'F',
    lessonCount: 10,
    progress: 40,
    className: 'fire'
  }

])



function openMajor(major) {

  router.push({
    name: 'LessonList',

    params: {
      major: major.code
    }
  })

}


function logout() {

  router.push('/login')

}

const getUserInfo = async () => {
  try {
    const response = await request.get('/api/user/user_info')

    user.value.name = response.data.user_name
    user.value.role = response.data.role

  } catch (error) {
    console.error('Get user info failed:', error)

    router.push('/login')
  }
}

onMounted(() => {
  getUserInfo()
})

const isManager = computed(() => {
  return ['manager', 'administer'].includes(user.value.role)
})

</script>


<style scoped>

* {
  box-sizing: border-box;
}


.page {

  min-height: 100vh;

  display: flex;

  gap: 22px;

  padding: 22px;

  background: #f4f6fb;

  color: #1d2939;

}


/* =========================
   sidebar
========================= */

.sidebar {

  width: 260px;

  min-width: 260px;

  height: calc(100vh - 44px);

  position: sticky;

  top: 22px;

  background: #ffffff;

  border-radius: 24px;

  padding: 26px 20px;

  box-shadow:
    0 15px 40px rgba(44, 62, 110, 0.08);

  display: flex;

  flex-direction: column;

}


.logo-area {

  display: flex;

  align-items: center;

  gap: 12px;

  padding: 0 8px 24px;

}


.logo-icon {

  width: 44px;

  height: 44px;

  border-radius: 12px;

  background: #3d66e8;

  color: #ffffff;

  display: flex;

  align-items: center;

  justify-content: center;

  font-size: 22px;

  font-weight: 700;

}


.logo-title {

  font-size: 18px;

  font-weight: 700;

}


.logo-subtitle {

  font-size: 12px;

  color: #98a2b3;

  margin-top: 3px;

}


/* user */

.user-card {

  display: flex;

  align-items: center;

  gap: 12px;

  background: #f7f8fc;

  border-radius: 16px;

  padding: 14px;

  margin-bottom: 22px;

}


.avatar {

  width: 42px;

  height: 42px;

  border-radius: 50%;

  background: #3d66e8;

  color: white;

  display: flex;

  justify-content: center;

  align-items: center;

  font-weight: 700;

}


.user-name {

  font-weight: 600;

}


.user-role {

  font-size: 12px;

  margin-top: 3px;

  color: #98a2b3;

}


/* menu */

.menu {

  flex: 1;

  overflow-y: auto;

}


.menu-item {

  min-height: 45px;

  display: flex;

  align-items: center;

  padding: 0 14px;

  border-radius: 11px;

  color: #475467;

  font-size: 14px;

  cursor: pointer;

}


.menu-item.active {

  background: #edf2ff;

  color: #3d66e8;

  font-weight: 600;

}


.menu-icon {

  width: 30px;

}


.menu-title {

  font-size: 13px;

  font-weight: 600;

  color: #344054;

  margin-top: 18px;

  margin-bottom: 7px;

  padding-left: 14px;

}


.sub-item {

  padding: 9px 14px 9px 43px;

  font-size: 13px;

  border-radius: 9px;

  color: #667085;

  cursor: pointer;

}


.sub-item:hover {

  background: #f5f7ff;

  color: #3d66e8;

}


.logout {

  height: 44px;

  display: flex;

  justify-content: center;

  align-items: center;

  border-radius: 11px;

  background: #f7f8fa;

  color: #667085;

  cursor: pointer;

}



/* =========================
   main
========================= */

.main-content {

  flex: 1;

  padding: 5px 8px 50px;

}


.header {

  height: 90px;

  display: flex;

  align-items: center;

  justify-content: space-between;

}


.header h1 {

  margin: 0;

  font-size: 28px;

}


.header p {

  margin: 7px 0 0;

  color: #98a2b3;

}


.languages {

  display: flex;

  gap: 5px;

}


.language {

  border: none;

  background: transparent;

  border-radius: 9px;

  padding: 9px 13px;

  font-size: 14px;

  color: #98a2b3;

}


.active-language {

  background: #3d66e8;

  color: white;

}



/* =========================
   总学习进度
========================= */

.progress-section {

  background: white;

  border-radius: 22px;

  padding: 28px;

  margin-bottom: 24px;

  box-shadow:
    0 10px 30px rgba(44, 62, 110, 0.05);

}


.progress-header {

  display: flex;

  justify-content: space-between;

  align-items: center;

}


.progress-header h2 {

  margin: 0;

  font-size: 21px;

}


.progress-header p {

  margin: 7px 0 0;

  color: #98a2b3;

  font-size: 13px;

}


.progress-percent {

  font-size: 32px;

  font-weight: 700;

  color: #3d66e8;

}


.big-progress {

  height: 12px;

  background: #edf0f6;

  border-radius: 20px;

  margin-top: 26px;

  overflow: hidden;

}


.big-progress-value {

  height: 100%;

  background: #3d66e8;

  border-radius: 20px;

  transition: width 0.4s;

}


.progress-bottom {

  margin-top: 13px;

  display: flex;

  justify-content: space-between;

  font-size: 13px;

  color: #667085;

}



/* =========================
   专业
========================= */

.major-section {

  background: white;

  border-radius: 22px;

  padding: 28px;

  box-shadow:
    0 10px 30px rgba(44, 62, 110, 0.05);

}


.section-title h2 {

  margin: 0;

  font-size: 21px;

}


.section-title p {

  color: #98a2b3;

  font-size: 13px;

  margin-top: 7px;

}


.major-grid {

  margin-top: 25px;

  display: grid;

  grid-template-columns:
    repeat(2, minmax(300px, 1fr));

  gap: 18px;

}


.major-card {

  min-height: 180px;

  border: 1px solid #eaecf0;

  border-radius: 18px;

  padding: 23px;

  display: flex;

  align-items: flex-start;

  cursor: pointer;

  transition: 0.2s;

}


.major-card:hover {

  transform: translateY(-3px);

  border-color: #b9c7f9;

  box-shadow:
    0 12px 25px rgba(61, 102, 232, 0.08);

}


.major-icon {

  width: 55px;

  height: 55px;

  border-radius: 15px;

  display: flex;

  justify-content: center;

  align-items: center;

  font-weight: 700;

  font-size: 21px;

  margin-right: 17px;

}


.electrical {

  background: #edf2ff;

  color: #3d66e8;

}


.hvac {

  background: #eaf8fa;

  color: #269cab;

}


.elv {

  background: #f3efff;

  color: #7658df;

}


.fire {

  background: #fff0ef;

  color: #e5635e;

}


.major-info {

  flex: 1;

}


.major-name {

  font-size: 18px;

  font-weight: 600;

}


.major-en {

  font-size: 13px;

  margin-top: 3px;

  color: #98a2b3;

}


.lesson-number {

  margin-top: 15px;

  font-size: 13px;

  color: #667085;

}


.major-progress {

  margin-top: 16px;

}


.progress-text {

  display: flex;

  justify-content: space-between;

  font-size: 11px;

  color: #98a2b3;

}


.small-progress {

  height: 6px;

  border-radius: 10px;

  background: #edf0f6;

  margin-top: 7px;

  overflow: hidden;

}


.small-progress-value {

  height: 100%;

  background: #3d66e8;

  border-radius: 10px;

}


.arrow {

  align-self: center;

  font-size: 30px;

  color: #98a2b3;

}


@media (max-width: 900px) {

  .major-grid {

    grid-template-columns: 1fr;

  }

}


@media (max-width: 700px) {

  .page {

    display: block;

  }

  .sidebar {

    width: 100%;

    min-width: 100%;

    height: auto;

    position: static;

    margin-bottom: 20px;

  }

}

</style>