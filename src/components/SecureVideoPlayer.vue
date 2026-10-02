<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import Hls from 'hls.js'
import { getPlayAuthorization } from '../api/lessons'

const props = defineProps({ lessonId: { type: Number, required: true } })
const video = ref(null)
const loading = ref(false)
const started = ref(false)
const error = ref('')
let hls = null
let authorization = null
let refreshTimer = null
let refreshPromise = null
let generation = 0
let disposed = false
let mediaRecoveries = 0

function destroyPlayer() {
  clearTimeout(refreshTimer)
  hls?.destroy()
  hls = null
  authorization = null
  if (video.value) {
    video.value.pause()
    video.value.removeAttribute('src')
    video.value.load()
  }
}
function errorText(err) {
  const status = err.response?.status
  if (status === 401) return '登录已过期，请重新登录。'
  if (status === 403) return '没有课程权限，或登录校验失败。请刷新页面或联系管理员。'
  if (status === 409) return '视频正在处理或等待迁移，暂时不能播放。'
  if (status === 429) return '请求过于频繁，请稍后再试。'
  return '视频暂时无法播放，请检查网络后重新点击播放。'
}
function scheduleRefresh(data) {
  clearTimeout(refreshTimer)
  refreshTimer = setTimeout(() => renewAuthorization().catch(() => {}), data.refresh_after * 1000)
}
async function loadNative(url, resume = false) {
  const player = video.value
  if (!player) return
  const position = resume ? player.currentTime : 0
  const shouldPlay = !resume || !player.paused
  player.src = url
  player.onloadedmetadata = () => {
    if (position > 0) player.currentTime = position
    if (shouldPlay) player.play().catch(() => {})
  }
  player.load()
}
async function renewAuthorization() {
  if (refreshPromise) return refreshPromise
  const version = generation
  refreshPromise = (async () => {
    try {
      const data = await getPlayAuthorization(props.lessonId)
      if (disposed || generation !== version) return
      const oldPrefix = authorization ? new URL(authorization.play_url).pathname.replace(/master\.m3u8$/, '') : null
      const newPrefix = new URL(data.play_url).pathname.replace(/master\.m3u8$/, '')
      authorization = data
      if (!hls) await loadNative(data.play_url, true)
      else if (oldPrefix && oldPrefix !== newPrefix) {
        // 管理员更换视频版本后重新加载，保留学习位置。
        const position = video.value?.currentTime || 0
        hls.loadSource(data.play_url)
        hls.startLoad(position)
      }
      scheduleRefresh(data)
    } catch (err) {
      if (disposed || version !== generation) return
      error.value = errorText(err)
      destroyPlayer()
      started.value = false
      throw err
    }
  })().finally(() => { if (version === generation) refreshPromise = null })
  return refreshPromise
}
async function playVideo() {
  if (loading.value) return
  const version = ++generation
  refreshPromise = null
  destroyPlayer()
  error.value = ''
  loading.value = true
  mediaRecoveries = 0
  try {
    const data = await getPlayAuthorization(props.lessonId)
    if (disposed || version !== generation) return
    authorization = data
    started.value = true
    await nextTick()
    const player = video.value
    // Safari/iOS 优先用原生 HLS；续期时恢复时间和暂停状态。
    if (player.canPlayType('application/vnd.apple.mpegurl')) {
      await loadNative(data.play_url)
    } else if (Hls.isSupported()) {
      hls = new Hls({
        xhrSetup: async (xhr, resourceUrl) => {
          if (!authorization) throw new Error('Playback stopped')
          if (authorization.expires_at - Date.now() / 1000 < 30) await renewAuthorization()
          if (!authorization) throw new Error('Playback stopped')
          const target = new URL(resourceUrl)
          const active = new URL(authorization.play_url)
          const prefix = active.pathname.replace(/master\.m3u8$/, '')
          if (target.origin !== active.origin || !target.pathname.startsWith(prefix)) throw new Error('Unexpected video resource')
          // 更新每个分片请求，避免旧清单里的 Token 在长视频中途过期。
          target.searchParams.set('token', authorization.token)
          xhr.open('GET', target.href, true)
          xhr.withCredentials = false
        }
      })
      hls.attachMedia(player)
      hls.loadSource(data.play_url)
      hls.on(Hls.Events.MANIFEST_PARSED, () => player.play().catch(() => {}))
      hls.on(Hls.Events.ERROR, (_, detail) => {
        if (!detail.fatal) return
        if (detail.type === Hls.ErrorTypes.MEDIA_ERROR && mediaRecoveries++ < 1) {
          hls?.recoverMediaError()
          return
        }
        error.value = '视频加载失败，请检查网络后重新点击播放。'
        destroyPlayer()
        started.value = false
      })
    } else throw new Error('HLS unsupported')
    scheduleRefresh(data)
  } catch (err) {
    if (disposed || generation !== version) return
    error.value = errorText(err)
    destroyPlayer()
    started.value = false
  } finally {
    if (version === generation) loading.value = false
  }
}
function nativeError() {
  if (started.value && !hls && !loading.value) {
    error.value = '视频加载失败，请重新点击播放。'
    destroyPlayer()
    started.value = false
  }
}
function resumeAfterSleep() {
  if (document.visibilityState === 'visible' && authorization && authorization.expires_at - Date.now() / 1000 < 60) {
    renewAuthorization().catch(() => {})
  }
}
watch(() => props.lessonId, () => {
  generation++
  refreshPromise = null
  loading.value = false
  started.value = false
  error.value = ''
  destroyPlayer()
})
document.addEventListener('visibilitychange', resumeAfterSleep)
onBeforeUnmount(() => {
  disposed = true
  generation++
  destroyPlayer()
  document.removeEventListener('visibilitychange', resumeAfterSleep)
})
</script>

<template>
  <div class="secure-player">
    <video ref="video" controls playsinline preload="none" controlslist="nodownload" @error="nativeError"></video>
    <p v-if="error" role="alert">{{ error }}</p>
    <button v-if="!started" type="button" :disabled="loading" @click="playVideo">{{ loading ? '正在申请播放权限…' : '播放视频' }}</button>
    <small>仅已获课程授权的账号可以播放。</small>
  </div>
</template>
<style scoped>
.secure-player{padding:20px;background:#132140;color:white}
video{display:block;width:100%;max-height:70vh;background:#000}
button{margin-top:14px;padding:10px 22px;border:0;border-radius:8px;background:#3d66e8;color:white;cursor:pointer}
p{color:#ffd2d2}small{display:block;margin-top:12px;color:#c2d0ed}
</style>
