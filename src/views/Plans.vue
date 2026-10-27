<script setup>
import { onMounted, ref } from "vue";
import request from "../api/request";
import { getCatalog } from "../api/lessons";
import { canUpload } from "../stores/auth";
import { t } from "../i18n";
import { useTask } from "../composables/useTask";
import { notify } from "../stores/notices";
import PageState from "../components/PageState.vue";
const mine = ref([]),
  templates = ref([]),
  courses = ref([]),
  selected = ref([]),
  name = ref(""),
  description = ref(""),
  { busy, error, run } = useTask();
const catalogPage = ref(1);
const catalogPages = ref(0);
const CATALOG_LIMIT = 20;
async function fetchLists() {
  const [a, b, c] = await Promise.all([
    request.get("/api/plan/mine"),
    request.get("/api/plan/preset_planlist"),
    getCatalog(catalogPage.value, CATALOG_LIMIT),
  ]);
  mine.value = a.data;
  templates.value = b.data;
  courses.value = c.items.flatMap((s) =>
    s.lessons.filter((l) => l.can_access),
  );
  catalogPages.value = c.total_pages;
}
async function load() {
  await run(fetchLists);
}
async function changeCatalogPage(page) {
  if (page < 1 || page > catalogPages.value || page === catalogPage.value)
    return;
  catalogPage.value = page;
  await load();
}
async function create(template = false) {
  await run(async () => {
    if (!selected.value.length) throw new Error("UI:selectRequired");
    await request.post(
      `/api/plan/${template ? "create_preset_plan" : "add_custom_plan"}`,
      {
        plan_name: name.value.trim(),
        description: description.value,
        lesson_list: selected.value.map((id, index) => ({
          lesson_id: id,
          order: index + 1,
        })),
      },
    );
    selected.value = [];
    name.value = "";
    await fetchLists();
    notify("saved", "success");
  });
}
async function add(plan) {
  await run(async () => {
    await request.post("/api/plan/add_template_plan", {
      plan_id: plan.plan_id,
      plan_name: plan.plan_name,
    });
    await fetchLists();
    notify("saved", "success");
  });
}
async function progress(plan, lesson) {
  await run(async () => {
    await request.put(
      `/api/plan/${plan.plan_id}/lessons/${lesson.lesson_id}/progress`,
      { completed: !lesson.completed },
    );
    await fetchLists();
  });
}
onMounted(load);
</script>
<template>
  <p>{{ t("planHint") }}</p>
  <PageState :busy="busy" :error="error" @retry="load" />
  <section class="card form">
    <h2>{{ t("createPlan") }}</h2>
    <form @submit.prevent="create(false)">
      <label class="field"
        ><span>{{ t("planName") }}</span
        ><input v-model="name" required maxlength="200" /></label
      ><label v-if="canUpload()" class="field"
        ><span>{{ t("description") }}</span
        ><textarea v-model="description"></textarea>
      </label>
      <div class="checkbox-list">
        <label v-for="l in courses" :key="l.lesson_id" class="checkbox"
          ><input v-model="selected" type="checkbox" :value="l.lesson_id" />{{
            l.lesson_name
          }}</label
        >
      </div>
      <div v-if="catalogPages > 1" class="actions">
        <button
          type="button"
          class="secondary"
          :disabled="busy || catalogPage === 1"
          @click="changeCatalogPage(catalogPage - 1)"
        >
          {{ t("previousPage") }}
        </button>
        <span>{{ catalogPage }} / {{ catalogPages }}</span>
        <button
          type="button"
          class="secondary"
          :disabled="busy || catalogPage >= catalogPages"
          @click="changeCatalogPage(catalogPage + 1)"
        >
          {{ t("nextPage") }}
        </button>
      </div>
      <div class="actions">
        <button :disabled="busy">{{ t("createPlan") }}</button
        ><button
          v-if="canUpload()"
          type="button"
          :disabled="busy || !name.trim()"
          class="secondary"
          @click="create(true)"
        >
          {{ t("createTemplate") }}
        </button>
      </div>
    </form>
  </section>
  <h2>{{ t("plans") }}</h2>
  <section v-for="p in mine" :key="p.plan_id" class="card">
    <h3>
      {{ p.plan_name }} <span class="tag">{{ t(p.status) }}</span>
    </h3>
    <div v-for="l in p.lessons" :key="l.lesson_id" class="actions">
      <span>{{ l.lesson_name }}</span
      ><span v-if="l.archived" class="tag">{{ t("archived") }}</span
      ><template v-else
        ><RouterLink :to="`/lessons/${l.lesson_id}/detail`">{{
          t("allowed")
        }}</RouterLink
        ><button class="secondary" :disabled="busy" @click="progress(p, l)">
          {{ t(l.completed ? "undoComplete" : "markComplete") }}
        </button></template
      >
    </div>
  </section>
  <h2>{{ t("templates") }}</h2>
  <section v-for="p in templates" :key="p.plan_id" class="card">
    <h3>{{ p.plan_name }}</h3>
    <p v-for="l in p.lessons" :key="l.lesson_id">
      {{ l.order }}. {{ l.lesson_name }}
    </p>
    <button :disabled="busy" @click="add(p)">{{ t("addTemplate") }}</button>
  </section>
</template>
