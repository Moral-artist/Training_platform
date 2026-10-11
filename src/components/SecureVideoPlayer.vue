<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from "vue";
import Hls from "hls.js/light";
import { onMounted } from "vue";
import { getPlayAuthorization } from "../api/lessons";
import { t } from "../i18n";

const props = defineProps({ lessonId: { type: Number, required: true } });
const video = ref(null);
const loading = ref(false);
const started = ref(false);
const error = ref("");
const rate = ref(1);
const quality = ref(-1);
const levels = ref([]);
const buffering = ref(false);
let hls = null;
let authorization = null;
let refreshTimer = null;
let refreshPromise = null;
let generation = 0;
let disposed = false;
let mediaRecoveries = 0;

function destroyPlayer() {
  clearTimeout(refreshTimer);
  hls?.destroy();
  hls = null;
  authorization = null;
  buffering.value = false;
  levels.value = [];
  quality.value = -1;
  if (video.value) {
    video.value.pause();
    video.value.removeAttribute("src");
    video.value.load();
  }
}
function errorText(err) {
  if (err.message === "HLS unsupported") return "unsupported";
  const status = err.response?.status;
  if (status === 401) return "HTTP_401";
  if (status === 403) return "HTTP_403";
  if (status === 409) return "videoNotReady";
  if (status === 429) return "HTTP_429";
  return "playError";
}
function scheduleRefresh(data) {
  clearTimeout(refreshTimer);
  refreshTimer = setTimeout(
    () => renewAuthorization().catch(() => {}),
    data.refresh_after * 1000,
  );
}
async function loadNative(url, resume = false) {
  const player = video.value;
  if (!player) return;
  const position = resume ? player.currentTime : 0;
  const shouldPlay = !resume || !player.paused;
  player.src = url;
  player.onloadedmetadata = () => {
    if (position > 0) player.currentTime = position;
    player.playbackRate = rate.value;
    if (shouldPlay) player.play().catch(() => {});
  };
  player.load();
}
async function renewAuthorization() {
  if (refreshPromise) return refreshPromise;
  const version = generation;
  refreshPromise = (async () => {
    try {
      const data = await getPlayAuthorization(props.lessonId);
      if (disposed || generation !== version) return;
      const oldPrefix = authorization
        ? new URL(authorization.play_url).pathname.replace(/master\.m3u8$/, "")
        : null;
      const newPrefix = new URL(data.play_url).pathname.replace(
        /master\.m3u8$/,
        "",
      );
      authorization = data;
      if (!hls) await loadNative(data.play_url, true);
      else if (oldPrefix && oldPrefix !== newPrefix) {
        // 管理员更换视频版本后重新加载，保留学习位置。
        const position = video.value?.currentTime || 0;
        hls.loadSource(data.play_url);
        hls.startLoad(position);
      }
      scheduleRefresh(data);
    } catch (err) {
      if (disposed || version !== generation) return;
      error.value = errorText(err);
      destroyPlayer();
      started.value = false;
      throw err;
    }
  })().finally(() => {
    if (version === generation) refreshPromise = null;
  });
  return refreshPromise;
}
async function playVideo() {
  if (loading.value) return;
  const version = ++generation;
  refreshPromise = null;
  destroyPlayer();
  error.value = "";
  loading.value = true;
  mediaRecoveries = 0;
  try {
    const data = await getPlayAuthorization(props.lessonId);
    if (disposed || version !== generation) return;
    authorization = data;
    started.value = true;
    buffering.value = true;
    await nextTick();
    const player = video.value;
    // Safari/iOS 优先用原生 HLS；续期时恢复时间和暂停状态。
    if (player.canPlayType("application/vnd.apple.mpegurl")) {
      await loadNative(data.play_url);
    } else if (Hls.isSupported()) {
      hls = new Hls({
        xhrSetup: async (xhr, resourceUrl) => {
          if (!authorization) throw new Error("Playback stopped");
          if (authorization.expires_at - Date.now() / 1000 < 30)
            await renewAuthorization();
          if (!authorization) throw new Error("Playback stopped");
          const target = new URL(resourceUrl);
          const active = new URL(authorization.play_url);
          const prefix = active.pathname.replace(/master\.m3u8$/, "");
          if (
            target.origin !== active.origin ||
            !target.pathname.startsWith(prefix)
          )
            throw new Error("Unexpected video resource");
          // 更新每个分片请求，避免旧清单里的 Token 在长视频中途过期。
          target.searchParams.set("token", authorization.token);
          xhr.open("GET", target.href, true);
          xhr.withCredentials = false;
        },
      });
      hls.attachMedia(player);
      hls.loadSource(data.play_url);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        levels.value = hls.levels.map((level, index) => ({
          index,
          height: Math.min(level.height, level.width),
        }));
        player.playbackRate = rate.value;
        player.play().catch(() => {});
      });
      hls.on(Hls.Events.ERROR, (_, detail) => {
        if (!detail.fatal) return;
        if (
          detail.type === Hls.ErrorTypes.MEDIA_ERROR &&
          mediaRecoveries++ < 1
        ) {
          hls?.recoverMediaError();
          return;
        }
        error.value = "playError";
        destroyPlayer();
        started.value = false;
      });
    } else throw new Error("HLS unsupported");
    scheduleRefresh(data);
  } catch (err) {
    if (disposed || generation !== version) return;
    error.value = errorText(err);
    destroyPlayer();
    started.value = false;
  } finally {
    if (version === generation) loading.value = false;
  }
}
function nativeError() {
  if (started.value && !hls && !loading.value) {
    error.value = "playError";
    destroyPlayer();
    started.value = false;
  }
}
function setRate() {
  if (video.value) video.value.playbackRate = Number(rate.value);
}
function setQuality() {
  if (hls) hls.currentLevel = Number(quality.value);
}
function qualityLabel(height) {
  return height >= 2160
    ? "4K (2160p)"
    : height >= 1440
      ? "2K (1440p)"
      : `${height}p`;
}
function resumeAfterSleep() {
  if (
    document.visibilityState === "visible" &&
    authorization &&
    authorization.expires_at - Date.now() / 1000 < 60
  ) {
    renewAuthorization().catch(() => {});
  }
}
watch(
  () => props.lessonId,
  () => {
    generation++;
    refreshPromise = null;
    loading.value = false;
    started.value = false;
    error.value = "";
    destroyPlayer();
  },
);
onMounted(() => {
  if (props.autoplay) playVideo();
});
document.addEventListener("visibilitychange", resumeAfterSleep);
onBeforeUnmount(() => {
  disposed = true;
  generation++;
  destroyPlayer();
  document.removeEventListener("visibilitychange", resumeAfterSleep);
});
</script>

<template>
  <div class="video-frame">
    <video
      ref="video"
      controls
      playsinline
      preload="none"
      controlslist="nodownload"
      @error="nativeError"
      @waiting="buffering = true"
      @canplay="buffering = false"
      @playing="buffering = false"
    ></video>
    <p v-if="buffering && started" role="status">
      <span class="spinner"></span>{{ t("buffering") }}
    </p>
    <div class="player-controls">
      <label
        >{{ t("speed")
        }}<select v-model.number="rate" @change="setRate">
          <option v-for="speed in [0.9, 1, 1.5, 2]" :key="speed" :value="speed">
            {{ speed }}×
          </option>
        </select></label
      >
      <label v-if="levels.length"
        >{{ t("quality")
        }}<select v-model.number="quality" @change="setQuality">
          <option :value="-1">{{ t("auto") }}</option>
          <option
            v-for="level in levels"
            :key="level.index"
            :value="level.index"
          >
            {{ qualityLabel(level.height) }}
          </option>
        </select></label
      >
      <span v-else-if="started">{{ t("nativeQuality") }}</span>
    </div>
    <div v-if="error" class="notice warning" role="alert">{{ t(error) }}</div>
    <button
      v-if="!started"
      type="button"
      :disabled="loading"
      @click="playVideo"
    >
      {{ loading ? t("loading") : t("playVideo") }}
    </button>
  </div>
</template>
