<script setup>
import { onMounted, ref } from "vue";
import { getCatalog } from "../api/lessons";
import { t } from "../i18n";
import request from "../api/request";
import { useTask } from "../composables/useTask";
import PageState from "../components/PageState.vue";
import { notify } from "../stores/notices";
const systems = ref([]),
  name = ref(""),
  { busy, error, run } = useTask();
async function load() {
  await run(async () => {
    systems.value = await getCatalog();
  });
}
async function save() {
  await run(async () => {
    await request.post("/api/lessons/systemsubmit", null, {
      params: { system_name: name.value.trim() },
    });
    name.value = "";
    systems.value = await getCatalog();
    notify("saved", "success");
  });
}
onMounted(load);
</script>
<template>
  <section class="card">
    <div class="tabs">
      <span v-for="s in systems" :key="s.system_id" class="tag">{{
        s.system_name
      }}</span>
    </div>
    <form class="form" @submit.prevent="save">
      <label class="field"
        ><span>{{ t("systemName") }}</span
        ><input v-model="name" required maxlength="200" /></label
      ><button :disabled="busy">{{ t("save") }}</button>
    </form>
    <PageState :error="error" @retry="load" />
  </section>
</template>
