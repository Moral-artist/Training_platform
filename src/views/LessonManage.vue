<script setup>
import { onMounted, ref } from "vue";
import request from "../api/request";
import { getCatalog, getLesson } from "../api/lessons";
import { t } from "../i18n";
import { useTask } from "../composables/useTask";
import PageState from "../components/PageState.vue";
import { notify } from "../stores/notices";
const rows = ref([]),
  deleting = ref(null),
  { busy, error, run } = useTask();
async function load() {
  await run(async () => {
    const systems = await getCatalog(),
      all = systems.flatMap((s) => s.lessons.filter((l) => l.can_access));
    const details = [];
    // 有界批量查询，避免课程多时一次发出过多请求。
    for (let start = 0; start < all.length; start += 8) {
      const batch = await Promise.all(
        all.slice(start, start + 8).map((l) => getLesson(l.lesson_id)),
      );
      details.push(...batch.filter((l) => l.can_manage));
    }
    rows.value = details;
  });
}
async function remove() {
  await run(async () => {
    await request.delete(`/api/lessons/${deleting.value.lesson_id}`, {
      params: { revision: deleting.value.revision },
    });
    rows.value = rows.value.filter(
      (l) => l.lesson_id !== deleting.value.lesson_id,
    );
    deleting.value = null;
    notify("saved", "success");
  });
}
onMounted(load);
</script>
<template>
  <PageState :busy="busy" :error="error" @retry="load" />
  <section class="card table-wrap">
    <table>
      <thead>
        <tr>
          <th>{{ t("lessonName") }}</th>
          <th>{{ t("status") }}</th>
          <th>{{ t("editLesson") }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="l in rows" :key="l.lesson_id">
          <td>{{ l.lesson_name }}</td>
          <td>{{ t(l.video_status) }}</td>
          <td>
            <div class="actions">
              <RouterLink
                class="button secondary"
                :to="`/lessons/${l.lesson_id}/edit`"
                >{{ t("editLesson") }}</RouterLink
              ><button class="danger" :disabled="busy" @click="deleting = l">
                {{ t("delete") }}
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="!rows.length">{{ t("empty") }}</p>
    <div v-if="deleting" class="notice warning delete-confirm" role="alert">
      <div>
        <p>{{ deleting.lesson_name }} · {{ t("deleteConfirm") }}</p>
        <div class="actions">
          <button class="danger" :disabled="busy" @click="remove">
            {{ t("confirm") }}</button
          ><button class="secondary" @click="deleting = null">
            {{ t("cancel") }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
