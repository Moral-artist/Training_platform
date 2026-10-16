<script setup>
  import { onMounted, ref, reactive, computed } from "vue";
  import request from "../api/request";
  import { getCatalog } from "../api/lessons";
  import { t } from "../i18n";
  import { useTask } from "../composables/useTask";
  import PageState from "../components/PageState.vue";
  import { deletePersonalPlan } from "../api/plan.js";

  const courses = ref([]),
    plans = ref([]),
    { busy, error, run } = useTask();

  /* async function load() {
    await run(async () => {
      const [catalog, result] = await Promise.all([
        getCatalog(),
        request.get("/api/plan/mine"),
      ]);
      console.log("mylesson: ", result)
      courses.value = catalog.flatMap((s) =>
        s.lessons.filter((l) => l.can_access),
      );
      plans.value = result.data;
    });
  } */
  async function load() {
    await run(async () => {
      const result = await request.get("/api/plan/mine");
      plans.value = result.data;
    });
  }
  // 每页显示课程数
  const PAGE_SIZE = 5;

  // 各计划是否展开
  const expandedPlans = reactive({});

  // 各计划当前页码
  const planPages = reactive({});

  // 展开或收起某个计划
  function togglePlan(planId) {
    expandedPlans[planId] = !expandedPlans[planId];

    if (!planPages[planId]) {
      planPages[planId] = 1;
    }
  }

  // 获取计划当前页
  function getCurrentPage(planId) {
    return planPages[planId] || 1;
  }

  // 计算计划总页数
  function getTotalPages(plan) {
    return Math.ceil((plan.lessons?.length || 0) / PAGE_SIZE);
  }

  // 获取当前页课程
  function getPagedLessons(plan) {
    const page = getCurrentPage(plan.plan_id);
    const start = (page - 1) * PAGE_SIZE;

    return (plan.lessons || []).slice(
      start,
      start + PAGE_SIZE
    );
  }

  // 切换某个计划的页码
  function changePlanPage(plan, newPage) {
    const total = getTotalPages(plan);

    if (newPage < 1 || newPage > total) return;

    planPages[plan.plan_id] = newPage;
  }

  // 已完成课程数量
  function getCompletedCount(plan) {
    return (plan.lessons || []).filter(
      lesson => lesson.completed
    ).length;
  }

  // 课程完成百分比
  function getProgress(plan) {
    const total = plan.lessons?.length || 0;

    if (!total) return 0;

    return Math.round(
      getCompletedCount(plan) / total * 100
    );
  }

const deletingPlanId = ref(null);

async function removePlan(plan) {
  if (deletingPlanId.value !== null) return;

  const confirmed = window.confirm(
    `确定删除培训计划「${plan.plan_name}」吗？`
  );

  if (!confirmed) return;

  deletingPlanId.value = plan.plan_id;

  try {
    await deletePersonalPlan(plan.plan_id);

    plans.value = plans.value.filter(
      item => item.plan_id !== plan.plan_id
    );
  } catch (err) {
    alert(err.response?.data?.detail || "删除失败");
  } finally {
    deletingPlanId.value = null;
  }
}
    
onMounted(load);
</script>


<template>
  <PageState :busy="busy" :error="error" @retry="load" />
  <section class="card hero">
    <h2>{{ t("dashboard") }}</h2>
    <p>
      {{ t("allCourses") }}: {{ courses.length }} · {{ t("plans") }}:
      {{ plans.length }}
    </p>
  </section>
<!--   <div class="grid">
    <article v-for="l in courses" :key="l.lesson_id" class="card course-card">
      <h3>{{ l.lesson_name }}</h3>
      <span class="tag">{{ t(l.video_status) }}</span
      ><RouterLink class="button" :to="`/lessons/${l.lesson_id}/detail`">{{
        t("allowed")
      }}</RouterLink>
    </article>
  </div> -->

  <section class="plans-section">
    <div class="plans-header">
      <h2>{{ t("myTrainingPlans") }}</h2>
      <span class="plans-count">
        {{ plans.length }} {{ t("planCount") }}
      </span>
    </div>
    <div class="plans-grid">
      <article
        v-for="plan in plans"
        :key="plan.plan_id"
        class="plan-card"
      >
        <!-- 计划标题：点击折叠 -->
        <button
          type="button"
          class="plan-top plan-toggle"
          :aria-expanded="!!expandedPlans[plan.plan_id]"
          @click="togglePlan(plan.plan_id)"
        >
          <div>
            <h3>{{ plan.plan_name }}</h3>
            <p class="plan-subtitle">
              {{ t("totalCoursesPrefix") }}
              {{ plan.lessons?.length || 0 }}
              {{ t("courseUnit") }}
              ·
              {{ t("completedPrefix") }}
              {{ getCompletedCount(plan) }}
              {{ t("completedUnit") }}
            </p>
          </div>

          <div class="plan-top-right">
            <span
              class="plan-status"
              :class="{ finished: plan.status === 'completed' }"
            >
            {{ t(plan.status) }}
            </span>

            <span
              class="expand-arrow"
              :class="{ expanded: expandedPlans[plan.plan_id] }"
            >
              ▼
            </span>

            <!-- 计划状态与删除 -->
            <div class="plan-top-actions">

              <span
                class="plan-status"
                :class="{
                  finished: plan.status === 'completed'
                }"
              >
              {{ t(plan.status) }}
              </span>

              <button
                type="button"
                class="delete-plan-button"
                :disabled="deletingPlanId === plan.plan_id"
                @click="removePlan(plan)"
              >
                {{
                  deletingPlanId === plan.plan_id
                    ? t("deleteInProgress")
                    : t("delete")
                }}
              </button>
            </div>

          </div>
        </button>

        <!-- 学习进度：折叠后仍然显示 -->
        <div class="progress-header">
          <span>{{ t("learningProgress") }}</span>
          <strong>{{ getProgress(plan) }}%</strong>
        </div>

        <div class="progress-track">
          <div
            class="progress-fill"
            :style="{ width: getProgress(plan) + '%' }"
          ></div>
        </div>

        <!-- 展开后的课程列表 -->
        <div
          v-if="expandedPlans[plan.plan_id]"
          class="plan-content"
        >
          <div class="plan-lessons">
            <div
              v-for="(lesson, index) in getPagedLessons(plan)"
              :key="lesson.lesson_id"
              class="plan-lesson"
            >
              <span class="lesson-number">
                {{
                  String(
                    (getCurrentPage(plan.plan_id) - 1) * PAGE_SIZE
                    + index + 1
                  ).padStart(2, '0')
                }}
              </span>

              <div class="lesson-info">
                <h4>{{ lesson.lesson_name }}</h4>

                <span
                  class="lesson-state"
                  :class="{
                    completed: lesson.completed,
                    archived: lesson.archived
                  }"
                >
                  {{
                    lesson.archived
                      ? t("archived")
                      : lesson.completed
                        ? '✓ ' + t("completed")
                        : '○ ' + t("incomplete")
                  }}
                </span>
              </div>

              <RouterLink
                v-if="!lesson.archived"
                class="lesson-action"
                :to="{
                  path: `/lessons/${lesson.lesson_id}/detail`,
                  query: {
                    plan_id: plan.plan_id
                  }
                }"
              >
                {{ lesson.completed ? t("reviewLesson") : t("startLearning") }}
                <span>→</span>
              </RouterLink>

              <span v-else class="lesson-unavailable">
                {{ t("unavailable") }}
              </span>
            </div>

            <p
              v-if="!plan.lessons?.length"
              class="empty-lessons"
            >
              {{ t("planNoLessons") }}
            </p>
          </div>

          <!-- 每个计划独立分页 -->
          <div
            v-if="getTotalPages(plan) > 1"
            class="plan-pagination"
          >
            <button
              type="button"
              :disabled="getCurrentPage(plan.plan_id) === 1"
              @click="changePlanPage(
                plan,
                getCurrentPage(plan.plan_id) - 1
              )"
            >
              {{ t("previousPage") }}
            </button>

            <span class="page-info">
              {{ getCurrentPage(plan.plan_id) }}
              /
              {{ getTotalPages(plan) }}
            </span>

            <button
              type="button"
              :disabled="getCurrentPage(plan.plan_id) >= getTotalPages(plan)"
              @click="changePlanPage(
                plan,
                getCurrentPage(plan.plan_id) + 1
              )"
            >
              {{ t("nextPage") }}
            </button>
          </div>
        </div>
      </article>
    </div>
    <div v-if="!plans.length" class="plans-empty">
      <h3>{{ t("noTrainingPlans") }}</h3>
      <p>{{ t("createPlanPrompt") }}</p>
    </div>
  </section>
  <div v-if="deletingPlanId !== null" class="deleting-overlay">
      <div class="deleting-message">
        <span class="spinner"></span>
        {{ t("deletingPlanMessage") }}
      </div>
  </div>
<!--   <p v-if="!courses.length">{{ t("empty") }}</p> -->
</template>

<style scoped>

  .plans-section {
    margin-top: 30px;
  }

  .plans-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .plans-header h2 {
    margin: 0;
    font-size: 24px;
    color: #172b4d;
    font-weight: 700;
  }

  .plans-count {
    background: #e8efff;
    color: #3563dc;
    font-size: 13px;
    font-weight: 600;
    padding: 7px 14px;
    border-radius: 20px;
  }

  /* 计划列表 */
  .plans-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 22px;
  }

  /* 计划卡片 */
  .plan-card {
    min-width: 0;
    padding: 26px;
    background: #fff;
    border: 1px solid #e5eaf3;
    border-radius: 18px;
    box-shadow: 0 6px 24px rgba(31, 56, 100, 0.04);
    transition: box-shadow 0.2s ease;
  }

  .plan-card:hover {
    box-shadow: 0 10px 30px rgba(31, 56, 100, 0.09);
  }

  .plan-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 28px;
  }

  .plan-top h3 {
    margin: 0 0 9px;
    font-size: 20px;
    font-weight: 700;
    color: #182b49;
    overflow-wrap: anywhere;
  }

  .plan-subtitle {
    margin: 0;
    font-size: 13px;
    color: #8591a6;
  }

  .plan-status {
    flex-shrink: 0;
    padding: 6px 12px;
    border-radius: 20px;
    background: #eef3ff;
    color: #4169dc;
    font-size: 12px;
    font-weight: 600;
  }

  .plan-status.finished {
    color: #16835c;
    background: #e8f8f0;
  }

  /* 学习进度 */
  .progress-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
    color: #65748d;
    font-size: 13px;
  }

  .progress-header strong {
    color: #3563dc;
  }

  .progress-track {
    width: 100%;
    height: 8px;
    background: #edf1f8;
    border-radius: 20px;
    overflow: hidden;
    margin-bottom: 24px;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #3363e9, #6a8cff);
    border-radius: inherit;
    transition: width 0.3s ease;
  }

  /* 课程列表 */
  .plan-lessons {
    border-top: 1px solid #edf0f6;
  }

  .plan-lesson {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px 0;
    border-bottom: 1px solid #f0f2f7;
  }

  .plan-lesson:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }

  .lesson-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    flex-shrink: 0;
    background: #f2f5fa;
    border-radius: 10px;
    color: #74829a;
    font-size: 13px;
    font-weight: 600;
  }

  .lesson-info {
    min-width: 0;
    flex: 1;
  }

  .lesson-info h4 {
    margin: 0 0 6px;
    font-size: 14px;
    font-weight: 600;
    color: #263754;
    overflow-wrap: anywhere;
  }

  .lesson-state {
    color: #94a0b2;
    font-size: 12px;
  }

  .lesson-state.completed {
    color: #169766;
  }

  .lesson-state.archived {
    color: #dc7777;
  }

  .lesson-action {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
    padding: 9px 12px;
    border-radius: 9px;
    background: #eef3ff;
    color: #3563dc;
    font-size: 13px;
    font-weight: 600;
    text-decoration: none;
    transition: background 0.2s ease;
  }

  .lesson-action:hover {
    background: #dce7ff;
  }

  .lesson-unavailable {
    color: #a0aaba;
    font-size: 13px;
  }

  .empty-lessons {
    color: #94a0b2;
    font-size: 13px;
    padding: 14px 0;
  }

  .plans-empty {
    padding: 60px 24px;
    text-align: center;
    background: white;
    border: 1px dashed #d9e2ef;
    border-radius: 18px;
  }

  .plans-empty h3 {
    color: #243855;
  }

  .plans-empty p {
    color: #8c9ab0;
  }

  /* 响应式 */
  @media (max-width: 900px) {
    .plans-grid {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 600px) {
    .plan-card {
      padding: 18px;
    }

    .plan-top h3 {
      font-size: 18px;
    }

    .plan-lesson {
      gap: 10px;
    }

    .lesson-action {
      font-size: 12px;
      padding: 8px;
    }
  }
  /* 计划标题可点击 */
  .plan-toggle {
    width: 100%;
    padding: 0;
    border: none;
    background: transparent;
    text-align: left;
    cursor: pointer;
    font: inherit;
  }

  .plan-toggle:hover h3 {
    color: #3865e9;
  }

  .plan-toggle:focus-visible {
    outline: 2px solid #3865e9;
    outline-offset: 5px;
    border-radius: 6px;
  }

  .plan-top-right {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .expand-arrow {
    display: inline-block;
    color: #7b8ba5;
    font-size: 13px;
    transition: transform 0.25s ease;
  }

  .expand-arrow.expanded {
    transform: rotate(180deg);
  }

  /* 展开后的课程区域 */
  .plan-content {
    margin-top: 8px;
  }

  /* 独立分页 */
  .plan-pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 14px;
    padding-top: 20px;
  }

  .plan-pagination button {
    padding: 8px 14px;
    background: #fff;
    border: 1px solid #dce5f7;
    border-radius: 8px;
    color: #3865e9;
    font-size: 13px;
    cursor: pointer;
    transition: background 0.2s ease;
  }

  .plan-pagination button:hover:not(:disabled) {
    background: #edf2ff;
  }

  .plan-pagination button:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .page-info {
    min-width: 45px;
    text-align: center;
    color: #64748b;
    font-size: 13px;
  }

  .plan-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex: 1;
  min-width: 0;
  padding: 0;
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
  }

  .plan-top-actions {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }

  .delete-plan-button {
    padding: 8px 14px;
    border: 1px solid #fecaca;
    border-radius: 8px;
    background: #fff1f2;
    color: #dc2626;
    font-size: 13px;
    cursor: pointer;
  }

  .delete-plan-button:hover:not(:disabled) {
    background: #ffe4e6;
  }

  .delete-plan-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .deleting-overlay {
    position: fixed;
    inset: 0;
    z-index: 9999;
    background: rgba(255, 255, 255, 0.65);

    display: flex;
    align-items: center;
    justify-content: center;
  }

  .deleting-message {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 22px 30px;
    background: white;
    border-radius: 14px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
    color: #3563dc;
    font-weight: 600;
  }

  .spinner {
    width: 20px;
    height: 20px;
    border: 3px solid #dbe5ff;
    border-top-color: #3563dc;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
</style>
