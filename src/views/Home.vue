<script setup>
import {
  computed,
  onMounted,
  onBeforeUnmount,
  ref,
  watch
} from "vue";
import { useRoute } from "vue-router";

import { getSystems, getSystemLessons } from "../api/lessons";
import { auth } from "../stores/auth";
import { t } from "../i18n";
import { useTask } from "../composables/useTask";
import PageState from "../components/PageState.vue";

const route = useRoute();

const systems = ref([]);
const selected = ref(null);
const lessons = ref([]);

const currentPage = ref(1);
const pageSize = 10;
const totalPages = ref(0);
const totalLessons = ref(0);

const { busy, error, reference, run } = useTask();

// 固定的优先顺序，匹配数据库专业名称
const priority = ["电气", "暖通", "弱电", "消防"];

const sortedSystems = computed(() => {
  return [...systems.value].sort((a, b) => {
    const aIndex = priority.indexOf(a.system_name.trim());
    const bIndex = priority.indexOf(b.system_name.trim());

    if (aIndex !== -1 && bIndex !== -1) {
      return aIndex - bIndex;
    }

    if (aIndex !== -1) return -1;
    if (bIndex !== -1) return 1;

    return a.system_name.localeCompare(
      b.system_name,
      "en",
      { sensitivity: "base" }
    );
  });
});

const currentSystem = computed(() =>
  systems.value.find(
    s => s.system_id === selected.value
  )
);

const canPrev = computed(() => currentPage.value > 1);
const canNext = computed(() =>
  currentPage.value < totalPages.value
);

// 标识当前请求，避免快速切换时旧响应覆盖新响应
let requestVersion = 0;

async function loadLessons() {
  if (selected.value === null) return;

  const version = ++requestVersion;
  const systemId = selected.value;
  const page = currentPage.value;

  await run(async () => {
    const data = await getSystemLessons(
      systemId,
      page,
      pageSize
    );

    if (version !== requestVersion) return;

    lessons.value = data.lessonlist ?? [];
    totalLessons.value = data.total_lessons ?? 0;
    totalPages.value = data.total_pages ?? 0;
  });
}

// 初始化：只加载专业名称
async function load() {
  await run(async () => {
    const data = await getSystems();
    systems.value = Array.isArray(data) ? data : data.systems ?? [];
  });

  if (!systems.value.length) return;

  const routeId = Number(route.params.systemId);

  const exists = systems.value.some(
    s => s.system_id === routeId
  );

  const electrical = sortedSystems.value.find(
    s => s.system_name.trim() === "电气"
  );

  selected.value = exists
    ? routeId
    : electrical?.system_id ??
      sortedSystems.value[0].system_id;
}

// 切换专业时重置为第一页
function selectSystem(systemId) {
  if (selected.value === systemId) return;

  selected.value = systemId;
  currentPage.value = 1;
}

// 点击翻页
function changePage(page) {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
}

// 专业或者页码变化，重新请求后端
watch(
  [selected, currentPage],
  () => {
    if (selected.value !== null) {
      loadLessons();
    }
  }
);

// 路由变化时同步专业
watch(
  () => route.params.systemId,
  (id) => {
    const systemId = Number(id);

    if (systems.value.some(s => s.system_id === systemId)) {
      selectSystem(systemId);
    }
  }
);

function onLogout() {
  loadLessons();
}

onMounted(() => {
  load();
  window.addEventListener("training-logout", onLogout);
});

onBeforeUnmount(() => {
  requestVersion++;
  window.removeEventListener("training-logout", onLogout);
});
</script>

<template>
  <section class="course-page">

    <!-- 专业导航 -->
    <nav class="tabs">
      <button
        v-for="system in sortedSystems"
        :key="system.system_id"
        type="button"
        class="tab-button"
        :class="{ selected: selected === system.system_id }"
        @click="selectSystem(system.system_id)"
      >
        {{ system.system_name }}
      </button>
    </nav>

    <!-- 课程标题 -->
    <div class="course-heading">
      <h2>
        {{ currentSystem?.system_name || "课程列表" }}
      </h2>

      <span v-if="!busy && !error" class="course-total">
        共 {{ totalLessons }} 门课程
      </span>
    </div>

    <PageState
      :busy="busy"
      :error="error"
      :reference="reference"
      @retry="loadLessons"
    />

    <!-- 一行一条课程 -->
    <div v-if="!busy && !error" class="lesson-list">

      <article
        v-for="(lesson, index) in lessons"
        :key="lesson.lesson_id"
        class="lesson-row"
      >
        <span class="lesson-index">
          {{ String((currentPage - 1) * pageSize + index + 1).padStart(2, "0") }}
        </span>

        <div class="lesson-info">
          <h3>{{ lesson.lesson_name }}</h3>

          <span class="lesson-status">
            {{ t(lesson.video_status) }}
          </span>
        </div>

<!--         <RouterLink
          v-if="auth.user && lesson.can_access"
          class="lesson-button"
          :to="`/lessons/${lesson.lesson_id}/detail`"
        >
          {{ t("allowed") }}
        </RouterLink> -->

        <span v-if="!auth.user || !lesson.can_access" class="locked-button">
          {{ t("locked") }}
        </span>
      </article>

      <p v-if="!lessons.length" class="empty-message">
        {{ t("empty") }}
      </p>
    </div>

    <!-- 分页 -->
    <div
      v-if="!busy && !error && totalPages > 1"
      class="pagination"
    >
      <button
        type="button"
        :disabled="!canPrev"
        @click="changePage(currentPage - 1)"
      >
        上一页
      </button>

      <span>
        第 {{ currentPage }} / {{ totalPages }} 页
      </span>

      <button
        type="button"
        :disabled="!canNext"
        @click="changePage(currentPage + 1)"
      >
        下一页
      </button>
    </div>

  </section>
</template>

<style scoped>
.course-page {
  display: flex;
  flex-direction: column;
  gap: 26px;
}

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.tab-button {
  padding: 12px 24px;
  border: 1px solid #dce5f7;
  border-radius: 12px;
  background: white;
  color: #4565ef;
  font-size: 16px;
  cursor: pointer;
  transition: 0.2s;
}

.tab-button:hover {
  background: #edf2ff;
}

.tab-button.selected {
  background: #3865e9;
  border-color: #3865e9;
  color: white;
}

.course-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.course-heading h2 {
  margin: 0;
  font-size: 24px;
  color: #203451;
}

.course-total {
  color: #8190a7;
  font-size: 14px;
}

.lesson-list {
  border: 1px solid #dce5f7;
  border-radius: 16px;
  background: white;
  overflow: hidden;
}

.lesson-row {
  display: flex;
  align-items: center;
  gap: 20px;
  min-height: 84px;
  padding: 18px 28px;
  border-bottom: 1px solid #edf1f7;
}

.lesson-row:last-of-type {
  border-bottom: none;
}

.lesson-row:hover {
  background: #f8faff;
}

.lesson-index {
  width: 35px;
  flex-shrink: 0;
  color: #9aa8bd;
  font-size: 15px;
}

.lesson-info {
  flex: 1;
  min-width: 0;
}

.lesson-info h3 {
  margin: 0 0 7px;
  font-size: 16px;
  color: #203451;
  overflow-wrap: anywhere;
}

.lesson-status {
  color: #647a9c;
  font-size: 13px;
}

.lesson-button,
.locked-button {
  flex-shrink: 0;
  padding: 10px 18px;
  border-radius: 9px;
  font-size: 14px;
  text-decoration: none;
}

.lesson-button {
  background: #3865e9;
  color: white;
}

.locked-button {
  background: #edf1f8;
  color: #96a3b7;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 18px;
}

.pagination button {
  padding: 10px 20px;
  background: white;
  border: 1px solid #dce5f7;
  border-radius: 9px;
  color: #3865e9;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.empty-message {
  padding: 32px;
  text-align: center;
  color: #8190a7;
}

@media (max-width: 600px) {
  .lesson-row {
    padding: 16px 12px;
    gap: 10px;
  }

  .tab-button {
    padding: 10px 14px;
  }
}
</style>
