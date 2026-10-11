<script setup>
import {
  computed,
  onMounted,
  onBeforeUnmount,
  ref,
  watch
} from "vue";

import { useRoute, useRouter } from "vue-router";
import { getLesson } from "../api/lessons";
import {
  getLessonExams,
  startExam,
  submitExam,
  getMyAttempts
} from "../api/exam";
import request from "../api/request";
import SecureVideoPlayer from "../components/SecureVideoPlayer.vue";
import PageState from "../components/PageState.vue";
import { t } from "../i18n";
import { useTask } from "../composables/useTask";



const route = useRoute();
const router = useRouter();

function goBack() {
  router.back();
}

const { busy, error, reference, run } = useTask();

const lesson = ref(null);
const exams = ref([]);
const selectedExam = ref(null);

const attempt = ref(null);
const answers = ref({});
const result = ref(null);

const examLoading = ref(false);
const examError = ref("");
const attempts = ref([]);
const attemptedLoading = ref(false);

let timer = null;
let alive = true;
let loadVersion = 0;

const lessonId = computed(() =>
  Number(route.params.lessonId)
);

const planId = computed(() => {
  const value = route.query.plan_id;

  if (value == null || value === "") return null;

  const id = Number(value);

  return Number.isSafeInteger(id) && id > 0
    ? id
    : null;
});

const videoReady = computed(() =>
  lesson.value?.video_status === "ready"
);

const questions = computed(() =>
  selectedExam.value?.questions ?? []
);

const examStarted = computed(() =>
  attempt.value !== null
);

const isSubmitted = computed(() =>
  result.value !== null
);

function getErrorMessage(err) {
  return (
    err.response?.data?.detail ||
    err.message ||
    "操作失败，请稍后重试"
  );
}

// ======================
// 加载课程及考试
// ======================
async function load() {
  clearTimeout(timer);
  const version = ++loadVersion;
  const id = lessonId.value;

  // 切换课程时重置考试状态
  selectedExam.value = null;
  attempt.value = null;
  result.value = null;
  answers.value = {};
  exams.value = [];
  lesson.value = null;
  attempts.value = [];
  examError.value = "";

  await run(async () => {
    const data = await getLesson(id);

    if (!alive || version !== loadVersion) return;

    lesson.value = data;
  });

  if (!alive || version !== loadVersion || error.value) {
    return;
  }

  await loadExams(id, version);
  await loadAttempts(id, version);
  scheduleVideoRefresh(version);
}

// ======================
// 视频状态轮询
// ======================
function scheduleVideoRefresh(version) {
  clearTimeout(timer);

  if (
    !alive ||
    version !== loadVersion ||
    !["uploaded", "processing"].includes(
      lesson.value?.video_status
    )
  ) return;

  timer = setTimeout(
    () => refreshVideoStatus(version),
    5000
  );
}

async function refreshVideoStatus(version) {
  if (!alive || version !== loadVersion) return;

  try {
    const data = await getLesson(lessonId.value);

    if (!alive || version !== loadVersion) return;

    lesson.value = data;
  } catch (err) {
    console.error("刷新视频状态失败:", err);
  }

  scheduleVideoRefresh(version);
}

async function retryVideo() {
  if (!lesson.value?.video_asset_id) return;

  await run(async () => {
    await request.post(
      `/api/lessons_video/${lesson.value.video_asset_id}/retry`
    );

    lesson.value.video_status = "uploaded";
  });

  if (!error.value) {
    scheduleVideoRefresh(loadVersion);
  }
}

// ======================
// 加载试卷
// ======================
async function loadExams(id, version) {
  try {
    examLoading.value = true;
    examError.value = "";

    const data = await getLessonExams(id);

    if (!alive || version !== loadVersion) return;

    exams.value = Array.isArray(data) ? data : [];

  } catch (err) {
    if (!alive || version !== loadVersion) return;

    if (err.response?.status === 404) {
      exams.value = [];
    } else {
      examError.value = getErrorMessage(err);
    }
  } finally {
    if (alive && version === loadVersion) {
      examLoading.value = false;
    }
  }
}

// ======================
// 加载考试历史
// ======================
async function loadAttempts(id, version) {
  try {
    attemptedLoading.value = true;

    const data = await getMyAttempts();

    if (!alive || version !== loadVersion) return;

    attempts.value = Array.isArray(data) ? data : [];

  } catch (err) {
    console.error("加载考试记录失败:", err);
  } finally {
    if (alive && version === loadVersion) {
      attemptedLoading.value = false;
    }
  }
}

function getExamAttempts(examId) {
  return attempts.value.filter(
    item => Number(item.exam_id) === Number(examId)
  );
}

// ======================
// 选择试卷
// ======================
function selectExam(exam) {
  if (examLoading.value) return;

  selectedExam.value = exam;
  attempt.value = null;
  result.value = null;
  answers.value = {};
  examError.value = "";
}

// ======================
// 开始考试
// ======================
async function beginExam() {
  if (!selectedExam.value || examLoading.value) return;

  examLoading.value = true;
  examError.value = "";

  try {
    const data = await startExam(
      lessonId.value,
      selectedExam.value.exam_id,
      planId.value
    );

    attempt.value = data;
    answers.value = {};
    result.value = null;

  } catch (err) {
    examError.value = getErrorMessage(err);
  } finally {
    examLoading.value = false;
  }
}

// ======================
// 用户答案
// ======================
function getAnswer(questionId) {
  return answers.value[questionId] ?? "";
}

function setAnswer(questionId, value) {
  answers.value[questionId] = value;
}

function isMultiSelected(questionId, optionKey) {
  const current = getAnswer(questionId);

  return current.split(",").includes(optionKey);
}

function toggleMultiAnswer(questionId, optionKey) {
  const current = getAnswer(questionId)
    .split(",")
    .filter(Boolean);

  const values = new Set(current);

  if (values.has(optionKey)) {
    values.delete(optionKey);
  } else {
    values.add(optionKey);
  }

  answers.value[questionId] =
    Array.from(values).sort().join(",");
}

// ======================
// 提交考试
// ======================
async function finishExam() {
  if (!attempt.value || examLoading.value || result.value) {
    return;
  }

  if (!window.confirm("确定提交当前试卷吗？")) {
    return;
  }

  examLoading.value = true;
  examError.value = "";

  try {
    const payload = questions.value.map(q => ({
      q_id: Number(q.question_id),
      answer: getAnswer(q.question_id)
    }));

    result.value = await submitExam(
      attempt.value.attempt_id,
      payload
    );

    // 刷新考试历史
    const data = await getMyAttempts();
    attempts.value = Array.isArray(data) ? data : [];

  } catch (err) {
    examError.value = getErrorMessage(err);
  } finally {
    examLoading.value = false;
  }
}

function resetExam() {
  attempt.value = null;
  result.value = null;
  answers.value = {};
  examError.value = "";
}

watch(
  () => route.params.lessonId,
  () => load()
);

onMounted(load);

onBeforeUnmount(() => {
  alive = false;
  loadVersion++;
  clearTimeout(timer);
});
</script>

<template>
  <div class="lesson-detail-page">

    <PageState
      :busy="busy && !lesson"
      :error="error"
      :reference="reference"
      @retry="load"
    />

    <template v-if="lesson && !error">
      <div class="page-header">
        <button class="back-button" @click="goBack">
          <span class="back-arrow">←</span>
          返回
        </button>

        <div>
          <span class="page-label">TRAINING SYSTEM</span>
          <h1>视频详情</h1>
        </div>
      </div>

      <!-- ========================= -->
      <!-- 课程基本信息 -->
      <!-- ========================= -->
      <section class="card lesson-header">
        <span class="tag">
          {{ t(lesson.video_status) }}
        </span>

        <h1>{{ lesson.lesson_name }}</h1>

        <p class="description">
          {{ lesson.description }}
        </p>
      </section>

      <!-- ========================= -->
      <!-- 视频区域 -->
      <!-- ========================= -->
      <section class="card video-section">
        <h2>课程视频</h2>

        <SecureVideoPlayer
          v-if="videoReady"
          :key="lesson.lesson_id"
          :lesson-id="Number(lesson.lesson_id)"
        />

        <div
          v-else-if="['uploaded', 'processing'].includes(lesson.video_status)"
          class="video-notice"
        >
          <span class="spinner"></span>
          {{ t("videoNotReady") }}
        </div>

        <div v-else class="video-notice">
          视频暂时不可播放
        </div>

        <div v-if="lesson.can_manage" class="video-actions">
          <button
            v-if="lesson.video_status === 'failed'"
            :disabled="busy"
            @click="retryVideo"
          >
            {{ t("retry") }}
          </button>

          <RouterLink
            class="button secondary"
            :to="`/lessons/${lesson.lesson_id}/edit`"
          >
            {{ t("editLesson") }}
          </RouterLink>
        </div>
      </section>

      <!-- ========================= -->
      <!-- 课程考试 -->
      <!-- ========================= -->
      <section class="card exam-section">

        <h2>课程考试</h2>

        <p v-if="examLoading && !selectedExam">
          正在加载考试...
        </p>

        <p v-if="examError" class="error-message">
          {{ examError }}
        </p>

        <button
          v-if="examError && !selectedExam"
          @click="loadExams(lessonId, loadVersion)"
        >
          重新加载考试
        </button>

        <p
          v-if="!examLoading && !examError && !exams.length"
          class="empty-message"
        >
          当前课程暂无考试
        </p>

        <!-- 试卷选择 -->
        <div v-if="!selectedExam" class="exam-list">
          <article
            v-for="exam in exams"
            :key="exam.exam_id"
            class="exam-row"
          >
            <div class="exam-info">
              <h3>{{ exam.exam_name }}</h3>
              <span>
                {{ exam.questions.length }} 道题目
              </span>

              <span class="history-count">
                已提交
                {{ getExamAttempts(exam.exam_id).filter(a => a.submitted).length }}
                次
              </span>
            </div>

            <button @click="selectExam(exam)">
              进入考试
            </button>
          </article>
        </div>

        <!-- 进入试卷 -->
        <div v-else class="exam-content">

          <div class="exam-heading">
            <div>
              <h3>{{ selectedExam.exam_name }}</h3>
              <p>共 {{ questions.length }} 道题</p>
            </div>

            <button
              v-if="!examStarted"
              class="secondary-button"
              @click="selectedExam = null"
            >
              返回试卷列表
            </button>
          </div>

          <!-- 未开始 -->
          <div v-if="!examStarted" class="exam-start">
            <p>点击开始考试后，系统将创建考试记录。</p>

            <button
              :disabled="examLoading"
              @click="beginExam"
            >
              {{ examLoading ? "正在开始..." : "开始考试" }}
            </button>
          </div>

          <!-- 答题区 -->
          <template v-else-if="!isSubmitted">

            <div
              v-for="(question, index) in questions"
              :key="question.question_id"
              class="question-card"
            >
              <div class="question-heading">
                <strong>
                  {{ index + 1 }}. {{ question.question_name }}
                </strong>

                <span class="question-type">
                  {{
                    question.question_type === "singleQuestion"
                      ? "单选题"
                      : question.question_type === "multipleQuestions"
                        ? "多选题"
                        : "简答题"
                  }}
                </span>
              </div>

              <!-- 单选题 -->
              <div
                v-if="question.question_type === 'singleQuestion'"
                class="option-list"
              >
                <label
                  v-for="option in question.options"
                  :key="option.option_id"
                  class="option-item"
                >
                  <input
                    type="radio"
                    :name="`question-${question.question_id}`"
                    :value="option.option_key"
                    :checked="getAnswer(question.question_id) === option.option_key"
                    @change="setAnswer(question.question_id, option.option_key)"
                  />

                  <span>
                    {{ option.option_key }}.
                    {{ option.option_value }}
                  </span>
                </label>
              </div>

              <!-- 多选题 -->
              <div
                v-else-if="question.question_type === 'multipleQuestions'"
                class="option-list"
              >
                <label
                  v-for="option in question.options"
                  :key="option.option_id"
                  class="option-item"
                >
                  <input
                    type="checkbox"
                    :checked="isMultiSelected(question.question_id, option.option_key)"
                    @change="toggleMultiAnswer(question.question_id, option.option_key)"
                  />

                  <span>
                    {{ option.option_key }}.
                    {{ option.option_value }}
                  </span>
                </label>
              </div>

              <!-- 简答题 -->
              <textarea
                v-else-if="question.question_type === 'shortAnswer'"
                class="short-answer"
                rows="4"
                placeholder="请输入你的答案"
                :value="getAnswer(question.question_id)"
                @input="setAnswer(question.question_id, $event.target.value)"
              ></textarea>

              <p v-else class="error-message">
                不支持的题目类型：{{ question.question_type }}
              </p>
            </div>

            <div class="exam-submit">
              <button
                :disabled="examLoading"
                @click="finishExam"
              >
                {{ examLoading ? "正在提交..." : "提交试卷" }}
              </button>
            </div>
          </template>

          <!-- 结果区 -->
          <div v-else class="result-section">
            <div class="score">
              {{ Number(result.score ?? 0).toFixed(1) }}
              <small>分</small>
            </div>

            <h3 :class="result.passed ? 'passed' : 'failed'">
              {{ result.passed ? "考试通过" : "考试未通过" }}
            </h3>

            <p>
              答对 {{ result.total_correct ?? "-" }}
              / {{ result.total_questions ?? "-" }} 题
            </p>

            <button @click="resetExam">
              再次考试
            </button>
          </div>

        </div>

      </section>
    </template>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 18px;

  background: white;
  color: #3865e9;
  border: 1px solid #dce5f7;
  border-radius: 10px;

  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.back-button:hover {
  background: #edf2ff;
  border-color: #3865e9;
}

.back-arrow {
  font-size: 22px;
  line-height: 1;
}

.page-label {
  color: #3865e9;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 2px;
}

.page-header h1 {
  margin: 8px 0 0;
  color: #203451;
  font-size: 30px;
}

.lesson-detail-page {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.lesson-header,
.video-section,
.exam-section {
  padding: 28px;
}

.lesson-header h1 {
  font-size: 28px;
  margin: 16px 0;
}

.description {
  color: #64748b;
  line-height: 1.8;
  white-space: pre-wrap;
}

.video-section h2,
.exam-section h2 {
  margin: 0 0 20px;
}

.video-notice {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 240px;
  border-radius: 14px;
  background: #f1f5f9;
  color: #64748b;
}

.video-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 18px;
}

.exam-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.exam-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}

.exam-info h3 {
  margin: 0 0 8px;
}

.exam-info span {
  font-size: 13px;
  color: #64748b;
  margin-right: 16px;
}

.exam-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.exam-start {
  text-align: center;
  padding: 30px 0;
}

.question-card {
  padding: 24px 0;
  border-bottom: 1px solid #e2e8f0;
}

.question-heading {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.question-heading strong {
  line-height: 1.6;
}

.question-type {
  flex-shrink: 0;
  color: #64748b;
  font-size: 13px;
}

.option-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px;
  border: 1px solid #e2e8f0;
  border-radius: 9px;
  cursor: pointer;
}

.option-item:hover {
  background: #f8faff;
}

.option-item input {
  margin-top: 4px;
}

.short-answer {
  box-sizing: border-box;
  width: 100%;
  padding: 14px;
  border: 1px solid #cbd5e1;
  border-radius: 9px;
  resize: vertical;
  font: inherit;
}

.exam-submit {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
}

.result-section {
  text-align: center;
  padding: 40px 0;
}

.score {
  font-size: 64px;
  font-weight: 700;
  color: #3159db;
}

.score small {
  font-size: 20px;
}

.passed {
  color: #16a34a;
}

.failed,
.error-message {
  color: #dc2626;
}

.empty-message {
  padding: 20px;
  color: #64748b;
  text-align: center;
}

button {
  padding: 10px 20px;
  border: 0;
  border-radius: 9px;
  background: #3865e9;
  color: white;
  cursor: pointer;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.secondary-button {
  background: #edf2ff;
  color: #3865e9;
}

@media (max-width: 600px) {
  .lesson-header,
  .video-section,
  .exam-section {
    padding: 16px;
  }

  .exam-row,
  .exam-heading {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
