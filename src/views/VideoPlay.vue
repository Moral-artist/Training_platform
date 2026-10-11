<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import SecureVideoPlayer from "../components/SecureVideoPlayer.vue";
import PageState from "../components/PageState.vue";
import { getLesson } from "../api/lessons";
import { t } from "../i18n";
import { useTask } from "../composables/useTask";
const route = useRoute(),
  lesson = ref(null),
  { busy, error, run } = useTask();
async function load() {
  await run(async () => {
    lesson.value = await getLesson(route.params.lessonId);
  });
}
onMounted(load);
</script>
<template>
  <RouterLink
    class="button secondary"
    :to="`/lessons/${route.params.lessonId}/detail`"
    >{{ t("back") }}</RouterLink
  ><PageState :busy="busy" :error="error" @retry="load" />
  <section v-if="lesson && !error" class="card">
    <h2>{{ lesson.lesson_name }}</h2>
    <SecureVideoPlayer :lesson-id="Number(lesson.lesson_id)" autoplay />
    <p>{{ t("playHint") }}</p>
  </section>
</template>
