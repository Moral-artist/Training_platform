<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  majors,
  getCurrentUser,
  getSystems,
  findSystemForMajor,
  getAuthorizedLessons
} from '../api/lessons.js'

const router = useRouter()

// 是否完成登录状态检查
const authChecked = ref(false)

// 是否已登录
const isLoggedIn = ref(false)

// 当前选择的专业
const selectedMajor = ref(null)

// 后端专业列表
const systems = ref([])

// 当前用户可以看到的视频
const lessons = ref([])

// 加载状态
const loadingLessons = ref(false)

// 错误信息
const errorMessage = ref('')

/* =========================
   检查登录状态
========================= */

async function checkLogin() {
  try {
    await getCurrentUser()

    isLoggedIn.value = true
  } catch (error) {

    // 401：未登录
    // 404：你现在后端可能还是返回404
    if (
      error.response?.status === 401 ||
      error.response?.status === 404
    ) {
      isLoggedIn.value = false
    } else {
      console.error('Check login error:', error)

      isLoggedIn.value = false
    }
  } finally {
    authChecked.value = true
  }
}

/* =========================
   获取专业列表
========================= */

async function ensureSystems() {

  // 已经获取过，不重复请求
  if (systems.value.length > 0) {
    return
  }

  systems.value = await getSystems()
}

/* =========================
   选择专业
========================= */

async function selectMajor(major) {

  selectedMajor.value = major

  lessons.value = []

  errorMessage.value = ''

  /*
    未登录：

    不请求真实课程列表。

    所以用户在浏览器 Network 中，
    也拿不到 lesson_name、
    description、video_url。
  */

  if (!isLoggedIn.value) {
    return
  }

  loadingLessons.value = true

  try {

    await ensureSystems()

    const system = findSystemForMajor(
      systems.value,
      major
    )

    if (!system) {

      errorMessage.value =
        `没有找到“${major.name}”对应的专业。`

      return
    }

    /*
      登录后才访问课程列表接口。

      后端以后需要根据当前 user_id
      只返回这个用户有权限看的课程。
    */

    lessons.value =
      await getAuthorizedLessons(
        system.system_id
      )

  } catch (error) {

    // Session过期
    if (error.response?.status === 401) {

      isLoggedIn.value = false

      lessons.value = []

      return
    }

    // 没有权限
    if (error.response?.status === 403) {

      errorMessage.value =
        '你没有查看该专业课程的权限。'

      return
    }

    // 没有课程
    if (error.response?.status === 404) {

      lessons.value = []

      return
    }

    console.error(error)

    errorMessage.value =
      '课程加载失败，请稍后重试。'

  } finally {

    loadingLessons.value = false
  }
}

/* =========================
   打开课程详情
========================= */

async function openLesson(lesson) {

  await ensureSystems()

  const system = findSystemForMajor(
    systems.value,
    selectedMajor.value
  )

  if (!system) {
    return
  }

  router.push({
    name: 'VideoDetail',
    params: { major: selectedMajor.value.code, lessonId: lesson.lesson_id }
  })
}

/* =========================
   登录
========================= */

function goLogin() {

  router.push({
    name: 'Login',

    query: {
      redirect: '/home'
    }
  })
}

/* =========================
   注册
========================= */

function goRegister() {

  router.push({
    name: 'PreRegister'
  })
}

/* =========================
   页面打开
========================= */

onMounted(async () => {

  // 先确认有没有登录
  await checkLogin()

  // 默认选中电气
  selectedMajor.value = majors[0]

  // 已登录才加载真实课程
  if (isLoggedIn.value) {

    await selectMajor(
      majors[0]
    )
  }
})
</script>


<template>

  <div class="home-page">

    <!-- ======================
         顶部
    ======================= -->

    <header class="site-header">

      <!-- Logo -->

      <RouterLink
        class="brand"
        to="/home"
      >

        <span class="brand-mark">
          T
        </span>

        <span>

          <strong>
            培训平台
          </strong>

          <small>
            Training System
          </small>

        </span>

      </RouterLink>


      <!-- 登录 / 注册 -->

      <nav class="header-actions">

        <!-- 未登录 -->

        <template
          v-if="
            authChecked &&
            !isLoggedIn
          "
        >

          <button
            class="login-button"
            type="button"
            @click="goLogin"
          >
            登录
          </button>

          <button
            class="register-button"
            type="button"
            @click="goRegister"
          >
            注册
          </button>

        </template>


        <!-- 已登录 -->

        <span
          v-else-if="
            authChecked &&
            isLoggedIn
          "
          class="logged-badge"
        >
          ✓ 已登录
        </span>

      </nav>

    </header>


    <!-- ======================
         页面内容
    ======================= -->

    <main class="main-content">


      <!-- ======================
           首页介绍
      ======================= -->

      <section class="intro-card">

        <div>

          <span class="eyebrow">
            DATA CENTER TRAINING
          </span>

          <h1>
            专业培训
          </h1>


          <!-- 未登录 -->

          <p v-if="!isLoggedIn">

            登录后可查看你有权限学习的培训视频。

          </p>


          <!-- 已登录 -->

          <p v-else>

            选择专业，查看你当前有权限学习的培训视频。

          </p>

        </div>


        <!-- 右侧图标 -->

        <div
          class="intro-art"
          aria-hidden="true"
        >

          <span v-if="isLoggedIn">
            ▶
          </span>

          <span v-else>
            🔒
          </span>

        </div>

      </section>


      <!-- ======================
           专业培训
      ======================= -->

      <section class="training-section">


        <!-- 标题 + 四个专业按钮 -->

        <div class="section-title-row">


          <div>

            <h2>
              专业培训
            </h2>

            <p>
              选择专业查看培训课程
            </p>

          </div>


          <!-- 专业按钮 -->

          <div class="major-buttons">

            <button
              v-for="major in majors"
              :key="major.code"

              type="button"

              class="major-button"

              :class="{
                active:
                  selectedMajor?.code ===
                  major.code
              }"

              @click="
                selectMajor(major)
              "
            >

              {{ major.name }}

            </button>

          </div>

        </div>


        <!-- ==================================
             未登录
             不加载真实课程
        =================================== -->

        <section
          v-if="
            authChecked &&
            !isLoggedIn
          "
          class="locked-area"
        >


          <!-- 模糊课程卡片 -->

          <div
            class="fake-list"
            aria-hidden="true"
          >

            <div
              v-for="n in 6"
              :key="n"

              class="fake-video-card"
            >

              <!-- 左边编号 -->

              <span
                class="fake-number"
              ></span>


              <!-- 中间文字 -->

              <span
                class="fake-copy"
              >

                <span
                  class="fake-title"
                ></span>

                <span
                  class="fake-description"
                ></span>

                <span
                  class="
                    fake-description
                    short
                  "
                ></span>

              </span>


              <!-- 播放图标 -->

              <span
                class="fake-play"
              >
                ▶
              </span>

            </div>

          </div>


          <!-- 锁 -->

          <div class="lock-panel">

            <div class="lock-icon">
              🔒
            </div>


            <h3>
              登录后查看培训视频
            </h3>


            <p>

              视频名称、课程内容和播放入口，

              仅对已登录并具有相应权限的培训人员开放。

            </p>


            <div class="lock-actions">

              <button
                class="primary-action"
                type="button"
                @click="goLogin"
              >
                登录
              </button>


              <button
                class="secondary-action"
                type="button"
                @click="goRegister"
              >
                注册账号
              </button>

            </div>

          </div>

        </section>


        <!-- ==================================
             已登录
        =================================== -->

        <section
          v-else-if="
            authChecked &&
            isLoggedIn
          "
        >


          <!-- 当前专业 -->

          <div class="video-heading">

            <div>

              <h3>

                {{
                  selectedMajor?.name ||
                  '培训视频'
                }}

              </h3>


              <span
                v-if="!loadingLessons"
              >

                {{ lessons.length }}
                个可学习视频

              </span>

            </div>

          </div>


          <!-- 加载 -->

          <div
            v-if="loadingLessons"
            class="state-box"
          >

            正在加载你有权限的课程...

          </div>


          <!-- 错误 -->

          <div
            v-else-if="errorMessage"
            class="
              state-box
              error
            "
          >

            {{ errorMessage }}

          </div>


          <!-- 没有课程 -->

          <div
            v-else-if="
              lessons.length === 0
            "
            class="state-box"
          >

            当前专业暂无你可以学习的视频。

          </div>


          <!-- ======================
               视频列表
          ======================= -->

          <div
            v-else
            class="video-list"
          >

            <article
              v-for="
                (lesson, index)
                in lessons
              "

              :key="
                lesson.lesson_id
              "

              class="video-card"
            >


              <button
                type="button"

                class="video-link"

                @click="
                  openLesson(lesson)
                "
              >


                <!-- 编号 -->

                <span
                  class="video-number"
                >

                  {{
                    String(
                      index + 1
                    ).padStart(
                      2,
                      '0'
                    )
                  }}

                </span>


                <!-- 课程信息 -->

                <span
                  class="video-content"
                >

                  <strong>

                    {{
                      lesson.lesson_name
                    }}

                  </strong>


                  <small>

                    {{
                      lesson.description ||
                      '暂无课程简介'
                    }}

                  </small>


                  <span
                    class="detail-link"
                  >

                    查看视频详情 →

                  </span>

                </span>


                <!-- 播放图标 -->

                <span
                  class="play-icon"
                  aria-hidden="true"
                >
                  ▶
                </span>

              </button>

            </article>

          </div>

        </section>


        <!-- 登录检查中 -->

        <div
          v-else
          class="state-box"
        >

          正在检查登录状态...

        </div>

      </section>

    </main>

  </div>

</template>


<style scoped>

/* =========================
   基础
========================= */

* {
  box-sizing: border-box;
}

.home-page {

  min-height: 100vh;

  background: #f4f7fc;

  color: #1f2937;
}


/* =========================
   Header
========================= */

.site-header {

  width:
    min(
      1360px,
      calc(100% - 48px)
    );

  min-height: 82px;

  margin: 0 auto;

  display: flex;

  align-items: center;

  justify-content: space-between;
}


.brand {

  display: flex;

  align-items: center;

  gap: 12px;

  color: #1f2937;

  text-decoration: none;
}


.brand-mark {

  width: 44px;

  height: 44px;

  display: grid;

  place-items: center;

  border-radius: 12px;

  background: #3d66e8;

  color: #ffffff;

  font-size: 22px;

  font-weight: 700;
}


.brand strong,
.brand small {

  display: block;
}


.brand strong {

  font-size: 18px;
}


.brand small {

  margin-top: 2px;

  color: #98a2b3;

  font-size: 11px;
}


/* =========================
   登录按钮
========================= */

.header-actions {

  display: flex;

  align-items: center;

  gap: 10px;
}


.header-actions button {

  padding: 10px 19px;

  border-radius: 9px;

  font-size: 14px;

  font-weight: 700;

  cursor: pointer;
}


.login-button {

  border:
    1px solid #dce4fa;

  background: #ffffff;

  color: #3d66e8;
}


.register-button {

  border:
    1px solid #3d66e8;

  background: #3d66e8;

  color: #ffffff;
}


.logged-badge {

  padding: 9px 15px;

  border:
    1px solid #cfe5dd;

  border-radius: 999px;

  background: #effaf6;

  color: #16845b;

  font-size: 13px;

  font-weight: 700;
}


/* =========================
   Main
========================= */

.main-content {

  width:
    min(
      1360px,
      calc(100% - 48px)
    );

  margin: 0 auto;

  padding-bottom: 70px;
}


/* =========================
   Hero
========================= */

.intro-card {

  min-height: 230px;

  padding: 42px 52px;

  display: flex;

  align-items: center;

  justify-content: space-between;

  border-radius: 24px;

  background:
    linear-gradient(
      110deg,
      #ffffff 0%,
      #ffffff 70%,
      #e9efff 100%
    );

  box-shadow:
    0 12px 32px
    rgba(
      42,
      61,
      107,
      0.05
    );
}


.eyebrow {

  color: #3d66e8;

  font-size: 12px;

  font-weight: 700;

  letter-spacing: 0.08em;
}


.intro-card h1 {

  margin: 12px 0;

  font-size: 42px;
}


.intro-card p {

  margin: 0;

  color: #667085;
}


.intro-art {

  width: 130px;

  height: 130px;

  margin-right: 50px;

  display: grid;

  place-items: center;

  border-radius: 50%;

  background: #dfe8ff;

  font-size: 38px;

  box-shadow:
    0 0 0 20px #eaf0ff,
    0 0 0 40px #f3f6ff;
}


/* =========================
   培训区域
========================= */

.training-section {

  margin-top: 25px;

  padding: 38px 48px;

  border-radius: 24px;

  background: #ffffff;

  box-shadow:
    0 12px 32px
    rgba(
      42,
      61,
      107,
      0.05
    );
}


.section-title-row {

  padding-bottom: 28px;

  display: flex;

  align-items: center;

  justify-content: space-between;

  gap: 24px;

  border-bottom:
    1px solid #edf0f5;
}


.section-title-row h2 {

  margin: 0 0 8px;

  font-size: 25px;
}


.section-title-row p {

  margin: 0;

  color: #98a2b3;

  font-size: 14px;
}


/* =========================
   专业按钮
========================= */

.major-buttons {

  display: flex;

  flex-wrap: wrap;

  justify-content: flex-end;

  gap: 10px;
}


.major-button {

  min-width: 78px;

  padding: 10px 17px;

  border:
    1px solid #d8e0ee;

  border-radius: 9px;

  background: #ffffff;

  color: #475467;

  font-size: 14px;

  font-weight: 700;

  cursor: pointer;

  transition: 0.2s;
}


.major-button:hover {

  border-color: #3d66e8;

  color: #3d66e8;
}


.major-button.active {

  border-color: #3d66e8;

  background: #3d66e8;

  color: #ffffff;
}


/* =========================
   未登录锁定区域
========================= */

.locked-area {

  position: relative;

  min-height: 455px;

  margin-top: 28px;

  overflow: hidden;

  border:
    1px solid #edf0f5;

  border-radius: 18px;

  background: #f8faff;
}


/* 模糊背景 */

.fake-list {

  padding: 20px;

  display: grid;

  grid-template-columns:
    repeat(
      2,
      minmax(0, 1fr)
    );

  gap: 14px;

  filter: blur(6px);

  opacity: 0.45;

  user-select: none;

  pointer-events: none;
}


.fake-video-card {

  min-height: 125px;

  padding: 20px;

  display: flex;

  align-items: center;

  gap: 17px;

  border:
    1px solid #e5e9f2;

  border-radius: 15px;

  background: #ffffff;
}


.fake-number {

  width: 46px;

  height: 46px;

  flex: none;

  border-radius: 12px;

  background: #dde6fa;
}


.fake-copy {

  flex: 1;

  display: flex;

  flex-direction: column;

  gap: 10px;
}


.fake-title {

  width: 62%;

  height: 14px;

  border-radius: 4px;

  background: #b9c5dc;
}


.fake-description {

  width: 92%;

  height: 10px;

  border-radius: 4px;

  background: #d2d9e6;
}


.fake-description.short {

  width: 55%;
}


.fake-play {

  width: 36px;

  height: 36px;

  flex: none;

  display: grid;

  place-items: center;

  border-radius: 50%;

  background: #b8c6e9;

  color: #ffffff;
}


/* 中间锁 */

.lock-panel {

  position: absolute;

  inset: 0;

  z-index: 2;

  padding: 30px;

  display: flex;

  align-items: center;

  justify-content: center;

  flex-direction: column;

  text-align: center;

  background:
    rgba(
      248,
      250,
      255,
      0.62
    );

  backdrop-filter:
    blur(2px);
}


.lock-icon {

  width: 72px;

  height: 72px;

  display: grid;

  place-items: center;

  border-radius: 50%;

  background: #ffffff;

  box-shadow:
    0 12px 32px
    rgba(
      54,
      99,
      232,
      0.14
    );

  font-size: 31px;
}


.lock-panel h3 {

  margin:
    18px 0 9px;

  font-size: 23px;
}


.lock-panel p {

  max-width: 540px;

  margin: 0;

  color: #667085;

  line-height: 1.7;
}


.lock-actions {

  margin-top: 23px;

  display: flex;

  gap: 10px;
}


.lock-actions button {

  min-width: 105px;

  padding: 11px 18px;

  border-radius: 9px;

  font-size: 14px;

  font-weight: 700;

  cursor: pointer;
}


.primary-action {

  border:
    1px solid #3d66e8;

  background: #3d66e8;

  color: #ffffff;
}


.secondary-action {

  border:
    1px solid #d8e0ee;

  background: #ffffff;

  color: #3d66e8;
}


/* =========================
   登录后视频
========================= */

.video-heading {

  margin:
    28px 0 16px;
}


.video-heading > div {

  display: flex;

  align-items: baseline;

  gap: 12px;
}


.video-heading h3 {

  margin: 0;

  font-size: 20px;
}


.video-heading span {

  color: #98a2b3;

  font-size: 13px;
}


.video-list {

  display: grid;

  grid-template-columns:
    repeat(
      2,
      minmax(0, 1fr)
    );

  gap: 14px;
}


.video-card {

  overflow: hidden;

  border:
    1px solid #e8edf5;

  border-radius: 15px;

  background: #ffffff;
}


.video-link {

  width: 100%;

  min-height: 130px;

  padding: 20px;

  display: flex;

  align-items: center;

  gap: 17px;

  border: none;

  background: transparent;

  text-align: left;

  cursor: pointer;

  transition: 0.2s;
}


.video-link:hover {

  background: #f8faff;
}


.video-number {

  width: 46px;

  height: 46px;

  flex: none;

  display: grid;

  place-items: center;

  border-radius: 12px;

  background: #edf2ff;

  color: #3d66e8;

  font-weight: 800;
}


.video-content {

  min-width: 0;

  flex: 1;

  display: flex;

  flex-direction: column;

  gap: 7px;
}


.video-content strong {

  overflow: hidden;

  color: #1f2937;

  font-size: 16px;

  text-overflow: ellipsis;

  white-space: nowrap;
}


.video-content small {

  min-height: 36px;

  display: -webkit-box;

  overflow: hidden;

  color: #667085;

  line-height: 1.5;

  -webkit-box-orient:
    vertical;
    
  line-clamp: 2;
  -webkit-line-clamp: 2;
}


.detail-link {

  margin-top: 3px;

  color: #3d66e8;

  font-size: 13px;

  font-weight: 700;
}


.play-icon {

  width: 36px;

  height: 36px;

  flex: none;

  display: grid;

  place-items: center;

  border-radius: 50%;

  background: #3d66e8;

  color: #ffffff;

  font-size: 12px;
}


/* =========================
   状态
========================= */

.state-box {

  margin-top: 28px;

  padding: 45px 20px;

  border:
    1px dashed #d8e0ee;

  border-radius: 14px;

  color: #667085;

  text-align: center;
}


.state-box.error {

  border-color: #fecaca;

  background: #fff7f7;

  color: #b42318;
}


/* =========================
   平板
========================= */

@media (max-width: 860px) {

  .section-title-row {

    align-items: flex-start;

    flex-direction: column;
  }


  .major-buttons {

    justify-content:
      flex-start;
  }


  .video-list,
  .fake-list {

    grid-template-columns:
      1fr;
  }


  .intro-art {

    display: none;
  }
}


/* =========================
   手机
========================= */

@media (max-width: 560px) {

  .site-header,
  .main-content {

    width:
      min(
        100% - 28px,
        1360px
      );
  }


  .site-header {

    min-height: 70px;
  }


  .brand small {

    display: none;
  }


  .intro-card {

    min-height: 190px;

    padding:
      28px 24px;
  }


  .intro-card h1 {

    font-size: 34px;
  }


  .training-section {

    padding:
      26px 20px;
  }


  .major-buttons {

    width: 100%;
  }


  .major-button {

    flex: 1;
  }


  .lock-actions {

    width: 100%;

    flex-direction: column;
  }


  .lock-actions button {

    width: 100%;
  }
}

</style>