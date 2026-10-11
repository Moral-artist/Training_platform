<script setup>
import { onMounted, onBeforeUnmount, ref } from "vue";
import { useRoute } from "vue-router";
import { getLesson } from "../api/lessons";
import request from "../api/request";
import { t } from "../i18n";
import { useTask } from "../composables/useTask";
import PageState from "../components/PageState.vue";
const route = useRoute(),
  lesson = ref(null),
  { busy, error, reference, run } = useTask();
let timer,
  alive = true;
async function load() {
  await run(async () => {
    const data = await getLesson(route.params.lessonId);
    if (alive) lesson.value = data;
  });
  clearTimeout(timer);
  if (
    alive &&
    !error.value &&
    ["uploaded", "processing"].includes(lesson.value?.video_status)
  )
    timer = setTimeout(load, 5000);
}
async function retryVideo() {
  await run(async () => {
    await request.post(
      `/api/lessons_video/${lesson.value.video_asset_id}/retry`,
    );
    lesson.value.video_status = "uploaded";
  });
  if (!error.value) await load();
}
onMounted(load);
onBeforeUnmount(() => {
  alive = false;
  clearTimeout(timer);
});
</script>
<template>
  <PageState
    :busy="busy && !lesson"
    :error="error"
    :reference="reference"
    @retry="load"
  />
  <section v-if="lesson && !error" class="card">
    <span class="tag">{{ t(lesson.video_status) }}</span>
    <h2>{{ lesson.lesson_name }}</h2>
    <p class="description">{{ lesson.description }}</p>
    <div
      v-if="['uploaded', 'processing'].includes(lesson.video_status)"
      class="notice"
    >
      <span><span class="spinner"></span>{{ t("videoNotReady") }}</span>
    </div>
    <div class="actions">
      <RouterLink
        v-if="lesson.video_status === 'ready'"
        class="button"
        :to="`/video_play/${lesson.lesson_id}`"
        >{{ t("playVideo") }}</RouterLink
      ><button v-else disabled>{{ t("playVideo") }}</button>
      <button
        v-if="lesson.can_manage && lesson.video_status === 'failed'"
        :disabled="busy"
        @click="retryVideo"
      >
        {{ t("retry") }}
      </button>
      <RouterLink
        v-if="lesson.can_manage"
        class="button secondary"
        :to="`/lessons/${lesson.lesson_id}/edit`"
        >{{ t("editLesson") }}</RouterLink
      >
      <RouterLink
        class="button secondary"
        :to="{ path: '/exams', query: { lesson: lesson.lesson_id } }"
        >{{ t("exams") }}</RouterLink
      >
    </div>
  </section>
</template>
