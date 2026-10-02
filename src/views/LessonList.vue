<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getMajor, loadAuthorizedMajorLessons, majors } from '../api/lessons.js'

const route = useRoute()
const major = computed(() => getMajor(route.params.major))
const lessons = ref([])
const search = ref('')
const loading = ref(false)
const error = ref('')
let requestVersion = 0

const visibleLessons = computed(() => {
  const query = search.value.trim().toLowerCase()
  if (!query) return lessons.value
  return lessons.value.filter((lesson) =>
    `${lesson.title} ${lesson.description}`.toLowerCase().includes(query)
  )
})

async function loadLessons() {
  const version = ++requestVersion
  loading.value = true
  error.value = ''
  lessons.value = []
  try {
    const result = await loadAuthorizedMajorLessons(route.params.major)
    if (version === requestVersion) lessons.value = result
  } catch (err) {
    if (version === requestVersion) {
      error.value = err.response?.status === 401 ? '请先登录，再查看已授权的课程。' : err.message || '获取培训视频失败，请稍后重试。'
    }
  } finally {
    if (version === requestVersion) loading.value = false
  }
}

watch(() => route.params.major, () => {
  search.value = ''
  loadLessons()
}, { immediate: true })
</script>

<template>
  <div class="lesson-page">
    <header class="top-bar">
      <RouterLink class="back-link" to="/home">← 返回首页</RouterLink>
      <nav class="account-actions" aria-label="账户入口">
        <RouterLink to="/login">登录</RouterLink>
        <RouterLink class="primary-link" to="/pre_register">注册</RouterLink>
      </nav>
    </header>

    <main class="content">
      <section class="major-header">
        <span class="major-logo" :class="major?.code">{{ major?.short || '?' }}</span>
        <div>
          <span class="eyebrow">专业培训</span>
          <h1>{{ major?.name || '未知专业' }}培训视频</h1>
          <p>{{ major?.english || '' }} Training · 选择视频标题查看详情</p>
        </div>
      </section>

      <nav class="major-tabs" aria-label="选择专业">
        <RouterLink
          v-for="item in majors"
          :key="item.code"
          :to="{ name: 'LessonList', params: { major: item.code } }"
          :class="{ active: route.params.major === item.code }"
        >{{ item.name }}</RouterLink>
      </nav>

      <section class="list-panel" aria-labelledby="list-title">
        <div class="panel-heading">
          <div><h2 id="list-title">全部视频</h2><p>共 {{ lessons.length }} 个培训视频</p></div>
          <input v-model="search" type="search" placeholder="搜索视频名称" aria-label="搜索视频名称" />
        </div>

        <div v-if="loading" class="state">正在加载培训视频...</div>
        <div v-else-if="error" class="state error" role="alert">{{ error }}<button type="button" @click="loadLessons">重新加载</button></div>
        <div v-else-if="visibleLessons.length === 0" class="state">{{ search ? '没有找到匹配的视频。' : '该专业暂无培训视频。' }}</div>
        <div v-else class="video-list">
          <article v-for="(lesson, index) in visibleLessons" :key="lesson.id" class="video-row">
            <span class="video-index">{{ String(index + 1).padStart(2, '0') }}</span>
            <span class="play-icon" aria-hidden="true">▶</span>
            <div class="video-copy">
              <h3><RouterLink :to="{ name: 'VideoDetail', params: { major: major.code, lessonId: lesson.id } }">{{ lesson.title }}</RouterLink></h3>
              <p>{{ lesson.description || '点击查看视频介绍' }}</p>
            </div>
            <RouterLink class="detail-link" :to="{ name: 'VideoDetail', params: { major: major.code, lessonId: lesson.id } }">查看详情 <span aria-hidden="true">→</span></RouterLink>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
*{box-sizing:border-box}
.lesson-page{min-height:100vh;background:#f4f6fb;color:#1d2939;padding:22px 36px 75px}
.top-bar,.content{max-width:1260px;margin:auto}.top-bar{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:27px}
.back-link,.account-actions a{text-decoration:none;font-size:14px;font-weight:700}.back-link{color:#3d66e8}.back-link:hover{text-decoration:underline}
.account-actions{display:flex;align-items:center;gap:10px}.account-actions a{color:#3d66e8;padding:10px 17px;border-radius:9px;background:white;border:1px solid #dce4fa}.account-actions .primary-link{background:#3d66e8;color:#fff;border-color:#3d66e8}
.major-header{display:flex;align-items:center;gap:20px;background:#fff;border-radius:22px;padding:30px 34px;box-shadow:0 9px 27px #2c3e6e0a}
.major-logo{height:70px;width:70px;flex:none;border-radius:17px;display:grid;place-items:center;font-size:30px;font-weight:700}
.major-logo.electrical{background:#edf2ff;color:#3d66e8}.major-logo.hvac{background:#eaf8fa;color:#269cab}.major-logo.elv{background:#f3efff;color:#7658df}.major-logo.fire{background:#fff0ef;color:#e5635e}
.eyebrow{color:#3d66e8;font-size:12px;font-weight:700}.major-header h1{font-size:27px;margin:6px 0}.major-header p{font-size:13px;color:#98a2b3;margin:0}
.major-tabs{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0}.major-tabs a{min-width:81px;text-align:center;text-decoration:none;border:1px solid #e1e7f0;color:#667085;background:white;border-radius:9px;padding:10px 17px;font-size:14px;font-weight:700}.major-tabs a:hover,.major-tabs a.active{border-color:#3d66e8;background:#edf2ff;color:#3d66e8}
.list-panel{background:#fff;border-radius:22px;box-shadow:0 9px 27px #2c3e6e0a;overflow:hidden}
.panel-heading{padding:25px 31px;display:flex;align-items:center;justify-content:space-between;gap:20px;border-bottom:1px solid #edf0f5}.panel-heading h2{font-size:20px;margin:0 0 6px}.panel-heading p{font-size:13px;color:#98a2b3;margin:0}.panel-heading input{width:245px;padding:11px 13px;border:1px solid #dce3ee;border-radius:9px;outline:none;font:inherit;font-size:13px}.panel-heading input:focus{border-color:#3d66e8}
.video-list{padding:0 31px}.video-row{display:flex;align-items:center;gap:18px;min-height:103px;border-bottom:1px solid #edf0f5}.video-row:last-child{border-bottom:0}.video-index{font-size:12px;color:#a5afbf;font-weight:700;width:27px;text-align:center;flex:none}.play-icon{width:44px;height:44px;display:grid;place-items:center;border-radius:12px;background:#edf2ff;color:#3d66e8;padding-left:3px;flex:none}.video-copy{min-width:0;flex:1}.video-copy h3{font-size:16px;margin:0 0 7px}.video-copy h3 a{color:#25324a;text-decoration:none}.video-copy h3 a:hover{color:#3d66e8;text-decoration:underline}.video-copy p{font-size:13px;color:#98a2b3;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.detail-link{font-size:13px;color:#3d66e8;font-weight:700;text-decoration:none;white-space:nowrap}.detail-link span{margin-left:8px}.detail-link:hover{text-decoration:underline}
.state{padding:66px 25px;text-align:center;color:#8793a6}.state.error{color:#c24747}.state button{display:block;margin:16px auto 0;border:1px solid #dce4fa;background:#fff;color:#3d66e8;border-radius:8px;padding:9px 15px;cursor:pointer}
@media(max-width:700px){.lesson-page{padding:18px 16px 55px}.major-header{padding:22px 18px}.major-logo{height:56px;width:56px;font-size:24px}.major-header h1{font-size:22px}.panel-heading{padding:20px;align-items:stretch;flex-direction:column}.panel-heading input{width:100%}.video-list{padding:0 17px}.video-row{gap:11px;flex-wrap:wrap;padding:16px 0}.video-copy{flex-basis:calc(100% - 85px)}.video-copy h3{font-size:15px}.detail-link{margin-left:auto}}
</style>
