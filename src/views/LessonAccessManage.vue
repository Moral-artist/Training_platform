<script setup>
import { onMounted, ref } from "vue";
import request from "../api/request";
import { getCatalog } from "../api/lessons";
import { t } from "../i18n";
import { useTask } from "../composables/useTask";
import PageState from "../components/PageState.vue";
import { notify } from "../stores/notices";
const courses = ref([]),
  course = ref(0),
  search = ref(""),
  accounts = ref([]),
  grants = ref([]),
  { busy, error, run } = useTask();
async function load() {
  await run(async () => {
    courses.value = (await getCatalog()).flatMap((s) => s.lessons);
    accounts.value = (
      await request.get("/api/lessons/access_accounts", {
        params: { search: search.value },
      })
    ).data;
    if (course.value)
      grants.value = (
        await request.get(`/api/lessons/${course.value}/access`)
      ).data;
  });
}
async function toggle(id) {
  await run(async () => {
    const path = `/api/lessons/${course.value}/access/${id}`;
    if (grants.value.includes(id)) {
      await request.delete(path);
      grants.value = grants.value.filter((v) => v !== id);
    } else {
      await request.put(path);
      grants.value.push(id);
    }
    notify("saved", "success");
  });
}
onMounted(load);
</script>
<template>
  <section class="card">
    <p>{{ t("revocationHint") }}</p>
    <label class="field"
      ><span>{{ t("selectCourse") }}</span
      ><select v-model.number="course" @change="load">
        <option :value="0">—</option>
        <option v-for="l in courses" :key="l.lesson_id" :value="l.lesson_id">
          {{ l.lesson_name }}
        </option>
      </select></label
    >
    <form class="actions" @submit.prevent="load">
      <input
        v-model="search"
        :aria-label="t('search')"
        class="compact"
      /><button :disabled="busy">{{ t("search") }}</button>
    </form>
    <PageState :busy="busy" :error="error" @retry="load" />
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>{{ t("userName") }}</th>
            <th>{{ t("email") }}</th>
            <th>{{ t("access") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in accounts" :key="a.account_id">
            <td>{{ a.user_name }}</td>
            <td>{{ a.email }}</td>
            <td>
              <button
                :disabled="!course || busy || !a.is_active"
                :class="grants.includes(a.account_id) ? 'secondary' : ''"
                @click="toggle(a.account_id)"
              >
                {{ t(grants.includes(a.account_id) ? "revoke" : "grant") }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
