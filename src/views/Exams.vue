<script setup>
  import { computed, onMounted, reactive, ref } from "vue";
  import { useRoute } from "vue-router";
  import request from "../api/request";
  import { getLesson } from "../api/lessons";
  import { auth } from "../stores/auth";
  import { t } from "../i18n";
  import { useTask } from "../composables/useTask";
  import PageState from "../components/PageState.vue";
  import { notify } from "../stores/notices";

  const route = useRoute();
  const { busy, error, reference, run } = useTask();

  // 课程按专业分页，不再调用 getCatalog() 获取全量课程。
  const systems = ref([]);
  const systemId = ref(0);
  const courses = ref([]);
  const course = ref(0);
  const coursePage = ref(1);
  const courseTotalPages = ref(0);
  const COURSE_PAGE_SIZE = 10;
  const selectedCourseName = ref("");

  // 答题与考试记录：保留原页面功能。
  const exams = ref([]);
  const attempts = ref([]);
  const active = ref(null);
  const result = ref(null);
  const answers = reactive({});
  const manage = ref(false);
  const deleteId = ref(null);

  // 管理员编辑器：只有当前课程无考试才可创建；有考试则修改。
  const managedExams = ref([]);
  const managementLoaded = ref(false);
  const editingExamId = ref(null);
  const name = ref("");
  const questions = ref([]);
  const formError = ref("");
  let localUid = 0;

  const eligible = computed(() => Boolean(auth.user));
  const priorities = ["电气", "暖通", "弱电", "消防"];

  const sortedSystems = computed(() =>
    [...systems.value].sort((a, b) => {
      const ai = priorities.indexOf((a.system_name || "").trim());
      const bi = priorities.indexOf((b.system_name || "").trim());
      if (ai !== -1 && bi !== -1) return ai - bi;
      if (ai !== -1) return -1;
      if (bi !== -1) return 1;
      return a.system_name.localeCompare(b.system_name, "en", {
        sensitivity: "base",
      });
    }),
  );

  const draftKey = computed(
    () =>
      `training-answers:${auth.user?.account_id ?? "user"}:${active.value?.attempt_id ?? "none"}`,
  );

  const visibleAttempts = computed(() => {
    if (!course.value) return attempts.value;
    const ids = new Set(
      [...exams.value, ...managedExams.value].map((e) => Number(e.exam_id)),
    );
    return attempts.value.filter((a) => ids.has(Number(a.exam_id)));
  });

  // 兼容普通 AxiosResponse 与响应拦截器直接返回 data 的情况。
  function body(response) {
    return response && typeof response === "object" && "data" in response
      ? response.data
      : response;
  }

  function errText(e) {
    const detail = e?.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((x) => x.msg || JSON.stringify(x)).join("；");
    return e?.message || "操作失败，请稍后重试";
  }

  function resetAnswers() {
    for (const key of Object.keys(answers)) delete answers[key];
  }

  function resetEditor() {
    managedExams.value = [];
    managementLoaded.value = false;
    editingExamId.value = null;
    name.value = "";
    questions.value = [];
    formError.value = "";
  }

  function resetCourseState() {
    exams.value = [];
    active.value = null;
    result.value = null;
    manage.value = false;
    deleteId.value = null;
    resetAnswers();
    resetEditor();
  }

  async function loadCoursePage() {
    if (!systemId.value) {
      courses.value = [];
      courseTotalPages.value = 0;
      return;
    }
    const data = body(
      await request.get(`/api/lessons/majors/${systemId.value}/lessonlist`, {
        params: {
          current_page: coursePage.value,
          page_size: COURSE_PAGE_SIZE,
        },
      }),
    );
    courses.value = data.lessonlist ?? [];
    courseTotalPages.value = data.total_pages ?? 0;
  }

  async function refreshAttempts() {
    const data = body(await request.get("/api/exams/my_attempts"));
    attempts.value = Array.isArray(data) ? data : [];
  }

  async function loadSelectedCourse() {
    resetCourseState();
    if (!course.value) return;

    const detail = body(await getLesson(course.value));
    selectedCourseName.value = detail.lesson_name || selectedCourseName.value;
    manage.value = Boolean(detail.can_manage);

    // 答题接口不返回正确答案；404 代表课程暂无可用试卷。
    if (eligible.value) {
      try {
        const data = body(
          await request.get("/api/exams/getExams", {
            params: { lesson_id: course.value },
          }),
        );
        exams.value = Array.isArray(data) ? data : [];
      } catch (e) {
        if (e.response?.status === 404) exams.value = [];
        else throw e;
      }
    }

    // 仅拥有课程管理权限时请求包含正确答案的管理接口。
    // 请求失败时 managementLoaded 仍为 false，不允许误进入创建模式。
    if (manage.value) {
      const data = body(
        await request.get("/api/exams/manageExams", {
          params: { lesson_id: course.value },
        }),
      );
      managedExams.value = Array.isArray(data) ? data : [];
      managementLoaded.value = true;

      if (managedExams.value.length) {
        editExistingExam(managedExams.value[0]);
      } else {
        addQuestion();
      }
    }
  }

  async function load() {
    await run(async () => {
      const [systemResponse, attemptResponse] = await Promise.all([
        request.get("/api/lessons/systems"),
        request.get("/api/exams/my_attempts"),
      ]);

      const systemData = body(systemResponse);
      systems.value = Array.isArray(systemData)
        ? systemData
        : systemData.systems ?? [];
      attempts.value = body(attemptResponse) ?? [];

      const initialId = Number(
        route.query.lesson ?? route.query.lesson_id ?? route.params.lessonId,
      ) || 0;

      systemId.value = sortedSystems.value[0]?.system_id ?? 0;
      course.value = 0;
      selectedCourseName.value = "";
      coursePage.value = 1;
      resetCourseState();

      if (initialId) {
        const detail = body(await getLesson(initialId));
        const possibleSystemId = Number(detail.system_id);
        if (systems.value.some((s) => s.system_id === possibleSystemId)) {
          systemId.value = possibleSystemId;
        }
        course.value = initialId;
        selectedCourseName.value = detail.lesson_name || "";
      }

      await loadCoursePage();
      if (course.value) await loadSelectedCourse();
    });
  }

  async function selectSystem() {
    if (busy.value) return;
    course.value = 0;
    selectedCourseName.value = "";
    coursePage.value = 1;
    resetCourseState();
    await run(loadCoursePage);
  }

  async function changeCoursePage(page) {
    if (busy.value || page < 1 || page > courseTotalPages.value) return;
    course.value = 0;
    selectedCourseName.value = "";
    coursePage.value = page;
    resetCourseState();
    await run(loadCoursePage);
  }

  async function selectCourse() {
    if (busy.value) return;
    selectedCourseName.value = courses.value.find(
      (l) => Number(l.lesson_id) === Number(course.value),
    )?.lesson_name ?? "";
    await run(loadSelectedCourse);
  }

  // ===================== 考试作答 =====================
  async function start(exam) {
    if (busy.value) return;
    await run(async () => {
      const data = body(
        await request.post("/api/exams/attemptExam", {
          lesson_id: Number(course.value),
          exam_id: Number(exam.exam_id),
        }),
      );
      active.value = { ...data, exam };
      result.value = null;
      resetAnswers();

      let cached = {};
      try {
        cached = JSON.parse(sessionStorage.getItem(draftKey.value) || "{}");
      } catch { /* 浏览器禁止 storage 时，仍允许答题 */ }

      for (const q of exam.questions) {
        const previous = cached[q.question_id];
        answers[q.question_id] = q.question_type === "multipleQuestions"
          ? (Array.isArray(previous) ? previous : [])
          : (typeof previous === "string" ? previous : "");
      }
    });
  }

  function persist() {
    if (!active.value) return;
    try {
      sessionStorage.setItem(draftKey.value, JSON.stringify(answers));
    } catch { /* 非关键功能：草稿保存失败不阻止答题 */ }
  }

  async function submit() {
    if (!active.value || busy.value) return;
    await run(async () => {
      const oldDraftKey = draftKey.value;
      const data = body(
        await request.post("/api/exams/submitAttempt", {
          attempt_id: Number(active.value.attempt_id),
          questions: active.value.exam.questions.map((q) => ({
            q_id: Number(q.question_id),
            answer: Array.isArray(answers[q.question_id])
              ? answers[q.question_id].join(",")
              : (answers[q.question_id] || null),
          })),
        }),
      );
      result.value = data;
      active.value = null;
      try { sessionStorage.removeItem(oldDraftKey); } catch { /* ignore */ }
      try { await refreshAttempts(); } catch (e) { console.warn("考试已提交，但成绩列表刷新失败", e); }
    });
  }

  // ===================== 编辑已有考试 =====================
  function optionModel(optionKey = "A", value = "", correct = false) {
    return {
      uid: ++localUid,
      option_key: optionKey,
      option_value: value,
      is_correct: Boolean(correct),
    };
  }

  function addQuestion() {
    if (questions.value.length >= 200) return;
    questions.value.push({
      uid: ++localUid,
      question_name: "",
      question_type: "singleQuestion",
      answer: "",
      options: [optionModel("A"), optionModel("B")],
    });
  }

  function changeQuestionType(q) {
    q.answer = "";
    q.options = q.question_type === "shortAnswer"
      ? []
      : [optionModel("A"), optionModel("B")];
  }

  function addOption(q) {
    if (q.options.length >= 26) return;
    q.options.push(optionModel(String.fromCharCode(65 + q.options.length)));
  }

  function removeOption(q, index) {
    if (q.options.length <= 2) return;
    q.options.splice(index, 1);
    q.options.forEach((o, i) => {
      o.option_key = String.fromCharCode(65 + i);
    });
  }

  function selectSingleCorrect(q, selectedUid) {
    q.options.forEach((o) => {
      o.is_correct = o.uid === selectedUid;
    });
  }

  function editExistingExam(exam) {
    if (!exam) return;
    editingExamId.value = Number(exam.exam_id);
    name.value = exam.exam_name || "";
    formError.value = "";
    questions.value = (exam.questions || []).map((q) => ({
      uid: ++localUid,
      question_name: q.question_name || "",
      question_type: q.question_type,
      answer: q.answer || "",
      options: (q.options || []).map((o) =>
        optionModel(o.option_key, o.option_value, o.is_correct),
      ),
    }));
  }

  function validateEditor() {
    if (!managementLoaded.value || !manage.value) return "没有试卷管理权限";
    if (managedExams.value.length && editingExamId.value === null) {
      return "当前课程已有考试，请选择需要修改的试卷";
    }
    if (!course.value) return "请选择课程";
    if (!name.value.trim()) return "请输入试卷名称";
    if (name.value.trim().length > 200) return "试卷名称不能超过 200 字";
    if (!questions.value.length) return "请至少添加一道题";
    if (questions.value.length > 200) return "最多允许 200 道题";

    for (let i = 0; i < questions.value.length; i++) {
      const q = questions.value[i];
      const prefix = `第 ${i + 1} 题`;
      if (!q.question_name.trim()) return `${prefix}的内容不能为空`;
      if (q.question_name.trim().length > 2000) return `${prefix}的内容超过 2000 字`;

      if (q.question_type === "shortAnswer") {
        if (!q.answer?.trim()) return `${prefix}缺少简答题参考答案`;
        continue;
      }
      if (q.options.length < 2) return `${prefix}至少有两个选项`;
      if (new Set(q.options.map((o) => o.option_key)).size !== q.options.length) {
        return `${prefix}存在重复选项编号`;
      }
      for (const o of q.options) {
        if (!o.option_value.trim()) return `${prefix}选项 ${o.option_key} 为空`;
        if (o.option_value.trim().length > 2000) return `${prefix}选项 ${o.option_key} 过长`;
      }
      const correct = q.options.filter((o) => o.is_correct).length;
      if (q.question_type === "singleQuestion" && correct !== 1) {
        return `${prefix}必须且只能选一个正确答案`;
      }
      if (q.question_type === "multipleQuestions" && correct < 2) {
        return `${prefix}至少需要两个正确答案`;
      }
    }
    return "";
  }

  async function saveExam() {
    if (busy.value) return;
    formError.value = validateEditor();
    if (formError.value) return;

    const payload = {
      lesson_id: Number(course.value),
      exam_name: name.value.trim(),
      questions: questions.value.map((q) => ({
        question_name: q.question_name.trim(),
        question_type: q.question_type,
        answer: q.question_type === "shortAnswer" ? q.answer.trim() : null,
        options: q.question_type === "shortAnswer"
          ? []
          : q.options.map((o) => ({
              option_key: o.option_key,
              option_value: o.option_value.trim(),
              is_correct: o.is_correct,
            })),
      })),
    };

    await run(async () => {
      if (editingExamId.value !== null) {
        await request.put(`/api/exams/updateExams/${editingExamId.value}`, payload);
      } else {
        // 仅 manageExams 已确认当前课程完全没有试卷时才允许创建。
        if (managedExams.value.length > 0) throw new Error("已有考试禁止新增");
        await request.post("/api/exams/createExams", payload);
      }
      await loadSelectedCourse();
      notify("saved", "success");
    });
  }

  // ===================== 删除考试 =====================
  async function remove() {
    if (!deleteId.value || busy.value) return;
    await run(async () => {
      await request.post("/api/exams/deleteExams", null, {
        params: { exam_id: deleteId.value },
      });
      await loadSelectedCourse();
      notify("saved", "success");
    });
  }

  onMounted(load);
</script>

<template>
  <div class="exams-page">
<!--     <div v-if="loading" class="loading-overlay">
      <div class="loading-message">
        <span class="spinner"></span>
        正在加载，请稍候...
      </div>
    </div> -->
    <p>{{ t("examHint") }}</p>
    <div
      v-if="busy || error"
      class="page-overlay"
    >
      <PageState
        :busy="busy"
        :error="error"
        :reference="reference"
        @retry="load"
      />
    </div>

    <!-- 按专业、分页选择课程 -->
    <section class="card">
      <h2>{{ t("selectExamCourse") }}</h2>
      <div class="course-picker">
        <label class="field">
          <span>{{ t("selectSystem") }}</span>
          <select v-model.number="systemId" :disabled="busy" @change="selectSystem">
            <option v-for="s in sortedSystems" :key="s.system_id" :value="s.system_id">
              {{ s.system_name }}
            </option>
          </select>
        </label>

        <label class="field">
          <span>{{ t("selectCourse") }}</span>
          <select v-model.number="course" :disabled="busy || !systemId" @change="selectCourse">
            <option :value="0">{{ t("chooseCourse") }}</option>
            <option v-for="l in courses" :key="l.lesson_id" :value="l.lesson_id">
              {{ l.lesson_name }}
            </option>
            <!-- 直接从详情页进入且课程不在当前分页时，保留原选择 -->
            <option
              v-if="course && !courses.some((l) => Number(l.lesson_id) === course)"
              :value="course"
            >
              {{ selectedCourseName || t("courseFallback").replace("{id}", String(course)) }}
              ({{ t("currentlySelected") }})
            </option>
          </select>
        </label>
      </div>

      <div class="pagination" v-if="systemId">
        <button type="button" class="secondary" :disabled="busy || coursePage <= 1" @click="changeCoursePage(coursePage - 1)">
          {{ t("previousPage") }}
        </button>
        <span>{{ coursePage }} / {{ courseTotalPages || 1 }}</span>
        <button type="button" class="secondary" :disabled="busy || coursePage >= courseTotalPages" @click="changeCoursePage(coursePage + 1)">
          {{ t("nextPage") }}
        </button>
      </div>

      <p v-if="!eligible" class="notice">{{ t("examHint") }}</p>
    </section>

    <!-- 当前课程的考试列表 -->
    <section class="card" v-if="course && eligible">
      <h2>{{ t("courseExams") }}</h2>
      <p v-if="!exams.length" class="muted">{{ t("empty") }}</p>

      <div v-for="e in exams" :key="e.exam_id" class="exam-row">
        <div class="exam-name">
          <h3>{{ e.exam_name }}</h3>
          <small>{{ t("questionCount").replace("{count}", String(e.questions?.length || 0)) }}</small>
        </div>
        <div class="actions">
          <button type="button" :disabled="busy" @click="start(e)">{{ t("startExam") }}</button>
          <button
            v-if="manage && managementLoaded"
            type="button"
            class="secondary"
            :disabled="busy || !managedExams.some((m) => m.exam_id === e.exam_id)"
            @click="editExistingExam(managedExams.find((m) => m.exam_id === e.exam_id))"
          >
            {{ t("editExam") }}
          </button>
          <button v-if="manage" type="button" class="danger" :disabled="busy" @click="deleteId = e.exam_id">
            {{ t("delete") }}
          </button>
        </div>
      </div>

      <div v-if="deleteId" class="delete-confirm">
        <strong>{{ t("confirmDeleteExam") }}</strong>
        <div class="actions">
          <button type="button" class="danger" :disabled="busy" @click="remove">{{ t("confirm") }}</button>
          <button type="button" class="secondary" :disabled="busy" @click="deleteId = null">{{ t("cancel") }}</button>
        </div>
      </div>
    </section>

    <!-- 保留答题功能 -->
    <form v-if="active" class="card" @submit.prevent="submit">
      <h2>{{ active.exam.exam_name }}</h2>
      <section v-for="(q, index) in active.exam.questions" :key="q.question_id" class="question">
        <h3>{{ index + 1 }}. {{ q.question_name }}</h3>
        <label v-for="o in q.options" :key="o.option_id" class="answer-option">
          <input
            v-model="answers[q.question_id]"
            :type="q.question_type === 'multipleQuestions' ? 'checkbox' : 'radio'"
            :name="`question-${q.question_id}`"
            :value="o.option_key"
            @change="persist"
          />
          {{ o.option_key }}. {{ o.option_value }}
        </label>
        <label v-if="q.question_type === 'shortAnswer'" class="field">
          <span>{{ t("shortAnswer") }}</span>
          <textarea v-model="answers[q.question_id]" @input="persist"></textarea>
        </label>
      </section>
      <button :disabled="busy" type="submit">{{ t("submitExam") }}</button>
    </form>

    <section v-if="result" class="card">
      <h2>{{ t("result") }}</h2>
      <p>{{ t("score") }}: {{ result.score }} · {{ t(result.passed ? "passed" : "notPassed") }}</p>
    </section>

    <!-- 已有试卷：只出现“修改考试”；没有试卷：才显示“创建考试” -->
    <form
      v-if="course && manage && managementLoaded && (managedExams.length === 0 || editingExamId !== null)"
      class="card editor"
      @submit.prevent="saveExam"
    >
      <div class="editor-title">
        <div>
          <h2> {{ editingExamId !== null ? t("editExistingExam") : t("createCourseExam") }} </h2>
          <p class="muted" v-if="editingExamId !== null">{{ t("examIdNotice").replace("{id}", String(editingExamId)) }}</p>
          <p class="muted" v-else>{{ t("noCourseExam") }}</p>
        </div>
        <span class="mode-chip">{{ editingExamId !== null ? t("editMode") : t("createMode") }}</span>
      </div>

      <div v-if="managedExams.length > 1" class="existing-exams">
        <strong>{{ t("selectExamToEdit") }}</strong>
        <button
          v-for="e in managedExams"
          :key="e.exam_id"
          type="button"
          :class="editingExamId === e.exam_id ? 'active-exam' : 'secondary'"
          :disabled="busy"
          @click="editExistingExam(e)"
        >{{ e.exam_name }}</button>
      </div>

      <p v-if="editingExamId !== null" class="notice">
        {{ t("examHistoryWarning") }}
      </p>
      <p v-if="formError" class="form-error" role="alert">{{ formError }}</p>

      <label class="field">
        <span>{{ t("examName") }}</span>
        <input v-model="name" required maxlength="200"  :placeholder="t('examNamePlaceholder')" />
      </label>

      <section v-for="(q, index) in questions" :key="q.uid" class="question admin-question">
        <div class="question-heading">
          <strong>{{ t("questionNumber").replace("{count}", String(index + 1)) }}</strong>
          <div class="actions">
            <select v-model="q.question_type" :aria-label="t('questions')" @change="changeQuestionType(q)">
              <option value="singleQuestion">{{ t("singleQuestion") }}</option>
              <option value="multipleQuestions">{{ t("multipleQuestions") }}</option>
              <option value="shortAnswer">{{ t("shortAnswer") }}</option>
            </select>
            <button type="button" class="text-button danger-text" :disabled="busy" @click="questions.splice(index, 1)">
              {{ t("delete") }}
            </button>
          </div>
        </div>

        <label class="field">
          <span>{{ t("questionName") }}</span>
          <textarea v-model="q.question_name" required maxlength="2000" rows="2" placeholder="输入题目内容"></textarea>
        </label>

        <label v-if="q.question_type === 'shortAnswer'" class="field">
          <span>{{ t("shortAnswerReference") }}</span>
          <textarea
            v-model="q.question_name"
            required
            maxlength="2000"
            rows="2"
            :placeholder="t('questionContentPlaceholder')"
          ></textarea>
        </label>
        <template v-else>
          <p class="muted">
            {{
              q.question_type === "singleQuestion"
                ? t("singleAnswerHint")
                : t("multipleAnswerHint")
            }}
          </p>
          <div v-for="(o, oi) in q.options" :key="o.uid" class="option-edit-row">
            <label class="correct-picker">
              <input
                v-if="q.question_type === 'singleQuestion'"
                type="radio"
                :name="`correct-answer-${q.uid}`"
                :checked="o.is_correct"
                @change="selectSingleCorrect(q, o.uid)"
              />
              <input v-else v-model="o.is_correct" type="checkbox" />
              <span>{{ t("correct") }}</span>
            </label>
            <span class="option-letter">{{ o.option_key }}</span>
            <input v-model="o.option_value" required maxlength="2000" :placeholder="t('optionPlaceholder').replace('{key}', o.option_key)" />
            <button type="button" class="text-button" :disabled="busy || q.options.length <= 2" @click="removeOption(q, oi)">{{ t("removeOption") }}</button>
          </div>
          <button type="button" class="secondary" :disabled="busy || q.options.length >= 26" @click="addOption(q)">{{ t("addOptionButton") }}</button>
        </template>
      </section>

      <div class="actions editor-actions">
        <button type="button" class="secondary" :disabled="busy || questions.length >= 200" @click="addQuestion">{{ t("addQuestion") }}</button>
        <button type="submit" :disabled="busy || !questions.length">
          {{
            busy
              ? t("saving")
              : editingExamId !== null
                ? t("saveChanges")
                : t("createExam")
          }}
        </button>
      </div>
    </form>

    <!-- 考试记录 -->
    <section class="card table-wrap">
      <h2>{{ t("attempts") }}</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th><th>{{ t("examName") }}</th><th>{{ t("score") }}</th><th>{{ t("status") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in visibleAttempts" :key="a.attempt_id">
            <td>{{ a.attempt_id }}</td>
            <td>{{ exams.find(e => Number(e.exam_id) === Number(a.exam_id))?.exam_name || a.exam_id }}</td>
            <td>{{ a.score ?? "—" }}</td>
            <td>{{ t(a.submitted ? (a.passed ? "passed" : "notPassed") : "in_progress") }}</td>
          </tr>
          <tr v-if="!visibleAttempts.length">
            <td colspan="4" class="muted">
              {{ t("noExamAttempts") }}
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<style scoped>
  .exams-page { display: grid; gap: 22px; }
  .course-picker { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
  .field { display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }
  .field input, .field select, .field textarea, .question-heading select, .option-edit-row > input {
    width: 100%; min-width: 0; box-sizing: border-box; padding: 10px 12px;
    border: 1px solid #d8e2ef; border-radius: 9px; background: #fff; font: inherit;
  }
  .field textarea { resize: vertical; }
  .pagination { display: flex; justify-content: center; align-items: center; gap: 12px; margin-top: 12px; }
  .pagination button { padding: 8px 14px; }
  .exam-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 16px 0; border-bottom: 1px solid #edf1f6; }
  .exam-row:last-of-type { border-bottom: 0; }
  .exam-name h3 { margin: 0 0 6px; }
  .exam-name small, .muted { color: #718198; font-size: 13px; }
  .actions { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
  .actions button, .pagination button, .existing-exams button, .option-edit-row button { cursor: pointer; }
  button:disabled { opacity: .55; cursor: not-allowed; }
  .delete-confirm { background: #fff1f2; border-radius: 10px; padding: 15px; margin-top: 14px; display: flex; justify-content: space-between; align-items: center; gap: 12px; }
  .question { border-top: 1px solid #e7edf5; margin-top: 18px; padding-top: 20px; }
  .answer-option { display: flex; align-items: center; gap: 9px; padding: 8px 0; }
  .editor-title, .question-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 18px; }
  .editor-title h2 { margin: 0 0 6px; }
  .mode-chip { color: #315cdc; background: #edf2ff; padding: 6px 10px; border-radius: 999px; white-space: nowrap; font-size: 12px; }
  .existing-exams { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; padding: 12px 0; }
  .existing-exams strong { font-size: 13px; }
  .existing-exams .active-exam { background: #315cdc; color: white; }
  .option-edit-row { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
  .option-edit-row > input { flex: 1; }
  .correct-picker { display: inline-flex; align-items: center; gap: 5px; flex-shrink: 0; font-size: 13px; }
  .option-letter { width: 22px; color: #64748b; font-weight: 600; }
  .text-button { border: 0; background: transparent; color: #315cdc; }
  .danger-text { color: #c52828; }
  .editor-actions { justify-content: space-between; margin-top: 24px; }
  .form-error { background: #fef2f2; color: #b91c1c; border-radius: 9px; padding: 12px 16px; }
  .table-wrap { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 11px 12px; border-bottom: 1px solid #e7edf5; }
  @media (max-width: 700px) {
    .course-picker { grid-template-columns: 1fr; }
    .exam-row, .editor-title, .question-heading, .delete-confirm { align-items: stretch; flex-direction: column; }
    .option-edit-row { flex-wrap: wrap; }
  }

  .loading-overlay {
    position: fixed;
    inset: 0;
    z-index: 9999;
    background: rgba(255, 255, 255, 0.65);

    display: flex;
    align-items: center;
    justify-content: center;
  }
  .loading-message {
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
  .page-overlay {
    position: fixed;
    inset: 0;
    z-index: 9999;

    display: flex;
    align-items: center;
    justify-content: center;

    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(4px);
  }
</style>
