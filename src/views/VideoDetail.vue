<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getMajor, getAuthorizedLessonById } from '../api/lessons.js'
import SecureVideoPlayer from '../components/SecureVideoPlayer.vue'

const route = useRoute()
const major = computed(() => getMajor(route.params.major))
const lesson = ref(null)
const loading = ref(false)
const error = ref('')
let requestVersion = 0

async function loadLesson() {
  const version = ++requestVersion
  loading.value = true
  error.value = ''
  lesson.value = null
  try {
    const data = await getAuthorizedLessonById(null, Number(route.params.lessonId))
    if (version !== requestVersion) return
    lesson.value = { ...data, id: data.lesson_id, title: data.lesson_name }
    if (!lesson.value) error.value = '没有找到这个视频。'
  } catch (err) {
    if (version === requestVersion) error.value = err.response?.status === 401 ? '请先登录，再查看课程详情。' : err.response?.status === 403 ? '你还没有这门课程的权限，请联系管理员。' : '课程详情加载失败，请稍后重试。'
  } finally {
    if (version === requestVersion) loading.value = false
  }
}

watch(() => [route.params.major, route.params.lessonId], loadLesson, { immediate: true })
</script>

<template>
  <div class="detail-page">
    <header class="top-bar">
      <RouterLink class="back-link" :to="{ name: 'LessonList', params: { major: route.params.major } }">← 返回{{ major?.name || '' }}视频列表</RouterLink>
      <nav class="account-actions" aria-label="账户入口">
        <RouterLink to="/login">登录</RouterLink>
        <RouterLink class="primary-link" to="/pre_register">注册</RouterLink>
      </nav>
    </header>

    <main class="content">
      <div v-if="loading" class="state">正在加载视频详情...</div>
      <div v-else-if="error" class="state error" role="alert">{{ error }}<button type="button" @click="loadLesson">重新加载</button></div>
      <template v-else-if="lesson">
        <div class="heading"><span class="eyebrow">{{ major?.name }} · 视频详情</span><h1>{{ lesson.title }}</h1><p>视频状态：{{ lesson.video_status }}。转码完成后即可播放。</p></div>
        <section class="detail-card">
          <SecureVideoPlayer :key="lesson.id" :lesson-id="Number(lesson.id)" />
          <div class="video-info"><span class="tag">{{ major?.name }}培训</span><h2>{{ lesson.title }}</h2><h3>视频简介</h3><p>{{ lesson.description || '暂无视频简介。' }}</p></div>
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
*{box-sizing:border-box}
.detail-page{min-height:100vh;background:#f4f6fb;color:#1d2939;padding:22px 36px 75px}
.top-bar,.content{max-width:1160px;margin:auto}.top-bar{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:28px}
.back-link,.account-actions a{text-decoration:none;font-size:14px;font-weight:700}.back-link{color:#3d66e8}.back-link:hover{text-decoration:underline}
.account-actions{display:flex;align-items:center;gap:10px}.account-actions a{color:#3d66e8;padding:10px 17px;border-radius:9px;background:white;border:1px solid #dce4fa}.account-actions .primary-link{background:#3d66e8;color:#fff;border-color:#3d66e8}
.heading{margin-bottom:25px}.eyebrow{color:#3d66e8;font-size:13px;font-weight:700}.heading h1{font-size:30px;margin:11px 0}.heading p{color:#98a2b3;font-size:14px;margin:0}
.detail-card{overflow:hidden;background:white;border-radius:22px;box-shadow:0 9px 27px #2c3e6e0a}
.player-preview{min-height:430px;background:linear-gradient(130deg,#132140,#263f77);color:white;display:flex;align-items:center;justify-content:center;flex-direction:column;text-align:center;padding:30px}
.play-symbol{width:76px;height:76px;display:grid;place-items:center;border-radius:50%;background:#ffffff23;color:white;font-size:30px;padding-left:5px;margin-bottom:20px}.player-preview strong{font-size:21px}.player-preview p{color:#c2d0ed;font-size:14px;margin:10px 0 22px}
.player-actions{display:flex;flex-wrap:wrap;justify-content:center;gap:10px}.player-actions a{text-decoration:none;background:#3d66e8;color:#fff;border:1px solid #3d66e8;border-radius:9px;padding:11px 20px;font-size:14px;font-weight:700}.player-actions a.secondary{background:transparent;border-color:#8195c0}
.video-info{padding:29px 34px 37px}.tag{display:inline-block;background:#edf2ff;color:#3d66e8;border-radius:6px;padding:5px 10px;font-size:12px;font-weight:700}.video-info h2{font-size:23px;margin:15px 0 27px}.video-info h3{font-size:17px;margin:0 0 11px}.video-info p{font-size:14px;color:#667085;line-height:1.8;margin:0;white-space:pre-wrap}
.state{background:#fff;border-radius:18px;text-align:center;padding:80px 25px;color:#8793a6}.state.error{color:#c24747}.state button{display:block;margin:18px auto 0;border:1px solid #dce4fa;border-radius:8px;padding:9px 15px;background:white;color:#3d66e8;cursor:pointer}
@media(max-width:700px){.detail-page{padding:18px 16px 55px}.heading h1{font-size:24px}.player-preview{min-height:350px}.video-info{padding:23px 20px}.top-bar{gap:10px}.account-actions a{padding:9px 12px}}
</style>
