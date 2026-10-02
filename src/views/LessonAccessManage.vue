<script setup>
import { onMounted, ref } from 'vue'
import request from '../api/request'
import { getCurrentUser } from '../api/lessons'
const allowed = ref(false)
const loading = ref(true)
const busy = ref(false)
const search = ref('')
const accounts = ref([])
const groups = ref([])
const accountId = ref('')
const lessonId = ref('')
const message = ref('')
let searchVersion = 0
async function loadAccounts() {
  const version = ++searchVersion
  try {
    const response = await request.get('/api/lessons/access_accounts', { params: { search: search.value } })
    if (version !== searchVersion) return
    accounts.value = response.data
    if (!accounts.value.some(item => item.account_id === accountId.value)) accountId.value = ''
  } catch (error) {
    if (version === searchVersion) message.value = error.response?.status === 403 ? '只有管理员可以管理课程授权。' : '学员查询失败，请重新登录或稍后再试。'
  }
}
async function updateAccess(grant) {
  if (!accountId.value || !lessonId.value || busy.value) return
  busy.value = true
  message.value = ''
  try {
    const url = `/api/lessons/${lessonId.value}/access/${accountId.value}`
    if (grant) await request.put(url)
    else await request.delete(url)
    message.value = grant ? '已授权。学员现在可以查看这门课程，视频就绪后可以播放。' : '已撤销。新的播放授权会被拒绝，已发令牌最多等到到期后失效。'
  } catch (error) {
    message.value = error.response?.status === 403 ? '管理员权限或登录校验失败，请刷新或重新登录。' : '操作失败，请检查登录、课程和学员后重试。'
  } finally { busy.value = false }
}
onMounted(async () => {
  try {
    const user = await getCurrentUser()
    if (user.role !== 'administer') { message.value = '只有管理员可以管理课程授权。'; return }
    allowed.value = true
    groups.value = (await request.get('/api/lessons/alllessons')).data
    await loadAccounts()
  } catch (error) { message.value = '请先登录管理员账号。' }
  finally { loading.value = false }
})
</script>
<template>
  <main class="access-page">
    <RouterLink to="/dashboard">← 返回工作台</RouterLink>
    <h1>课程授权</h1>
    <p v-if="loading">正在检查管理员权限…</p>
    <template v-else-if="allowed">
      <p>选定学员和课程后，可以授予或撤销观看权限。</p>
      <form @submit.prevent="loadAccounts">
        <label for="search">搜索学员姓名或邮箱</label>
        <div class="search"><input id="search" v-model="search" maxlength="100" :disabled="busy" placeholder="例如学员姓名或邮箱" /><button :disabled="busy">搜索</button></div>
      </form>
      <label for="account">学员账号</label>
      <select id="account" v-model="accountId" :disabled="busy">
        <option value="">请选择学员（最多显示 100 条，可搜索缩小范围）</option>
        <option v-for="item in accounts" :key="item.account_id" :value="item.account_id" :disabled="!item.is_active">{{ item.user_name }} · {{ item.email }}{{ item.is_active ? '' : '（已禁用）' }}</option>
      </select>
      <label for="lesson">课程</label>
      <select id="lesson" v-model="lessonId" :disabled="busy">
        <option value="">请选择课程</option>
        <optgroup v-for="group in groups" :key="group.system_name" :label="group.system_name">
          <option v-for="lesson in group.lessons" :key="lesson.lesson_id" :value="lesson.lesson_id">{{ lesson.lesson_name }}</option>
        </optgroup>
      </select>
      <div class="actions"><button :disabled="busy || !accountId || !lessonId" @click="updateAccess(true)">授予观看权限</button><button class="revoke" :disabled="busy || !accountId || !lessonId" @click="updateAccess(false)">撤销观看权限</button></div>
    </template>
    <p v-if="message" class="message" role="status">{{ message }}</p>
  </main>
</template>
<style scoped>
.access-page{max-width:720px;margin:35px auto;padding:30px;background:white;border:1px solid #e1e7f0;border-radius:16px;color:#23364e}
a{color:#3d66e8}h1{font-size:26px}p{line-height:1.7}label{display:block;margin:20px 0 8px;font-weight:600}
input,select{box-sizing:border-box;width:100%;padding:12px;border:1px solid #c7d5e4;border-radius:8px;font:inherit}.search,.actions{display:flex;gap:12px}.actions{margin-top:25px;flex-wrap:wrap}
button{padding:11px 16px;border:0;border-radius:8px;background:#3d66e8;color:white;cursor:pointer;white-space:nowrap}.revoke{background:#b64040}button:disabled{opacity:.5;cursor:not-allowed}.message{margin-top:24px}@media(max-width:760px){.access-page{margin:15px;padding:20px}}
</style>
