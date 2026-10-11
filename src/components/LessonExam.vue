<template>
  <div class="exam-container">

    <!-- 加载 -->
    <div v-if="loading" class="state-box">
      正在加载考试...
    </div>

    <!-- 错误 -->
    <div v-else-if="errorMessage" class="state-box error">
      {{ errorMessage }}
    </div>

    <!-- 没有考试 -->
    <div
      v-else-if="!currentExam && exams.length === 0"
      class="state-box"
    >
      当前课程暂无考试
    </div>

    <!-- 考试列表 -->
    <div v-else-if="!currentExam && !result">
      <div class="header">
        <h2>课程考试</h2>
        <div v-if="exams.length">
          {{ exams[0].lesson_name }}
        </div>
      </div>

      <div
        v-for="exam in exams"
        :key="exam.exam_id"
        class="exam-card"
      >
        <div>
          <h3>{{ exam.exam_name }}</h3>

          <p>
            共 {{ exam.questions.length }} 道题
          </p>
        </div>

        <button
          class="primary-btn"
          @click="beginExam(exam)"
        >
          开始考试
        </button>
      </div>
    </div>

    <!-- 答题区域 -->
    <div v-else-if="currentExam && !result">

      <div class="exam-title">
        <div>
          <h2>{{ currentExam.exam_name }}</h2>

          <p>
            {{ currentExam.lesson_name }}
          </p>
        </div>

        <div class="attempt-info">
          第 {{ attemptNo }} 次考试
        </div>
      </div>

      <div
        v-for="(question, index) in currentExam.questions"
        :key="question.question_id"
        class="question-card"
      >

        <div class="question-title">
          <span class="question-number">
            {{ index + 1 }}
          </span>

          <span>
            {{ question.question_name }}
          </span>

          <span class="question-type">
            {{ getQuestionTypeName(question.question_type) }}
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
              v-model="answers[question.question_id]"
              type="radio"
              :name="'question-' + question.question_id"
              :value="option.option_key"
            />

            <span class="option-key">
              {{ option.option_key }}.
            </span>

            <span>
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
              v-model="answers[question.question_id]"
              type="checkbox"
              :value="option.option_key"
            />

            <span class="option-key">
              {{ option.option_key }}.
            </span>

            <span>
              {{ option.option_value }}
            </span>
          </label>
        </div>

        <!-- 简答题 -->
        <div
          v-else-if="question.question_type === 'shortAnswer'"
          class="short-answer"
        >
          <textarea
            v-model="answers[question.question_id]"
            rows="4"
            placeholder="请输入答案"
          />
        </div>

      </div>

      <div class="submit-area">
        <button
          class="submit-btn"
          :disabled="submitting"
          @click="handleSubmit"
        >
          {{ submitting ? '提交中...' : '提交考试' }}
        </button>
      </div>
    </div>

    <!-- 考试结果 -->
    <div
      v-else-if="result"
      class="result-card"
    >
      <div
        class="result-icon"
        :class="result.passed ? 'passed' : 'failed'"
      >
        {{ result.passed ? '✓' : '×' }}
      </div>

      <h2>
        {{ result.passed ? '考试通过' : '考试未通过' }}
      </h2>

      <div class="score">
        {{ formatScore(result.score) }}
      </div>

      <div class="result-details">

        <div>
          <span>题目数量</span>
          <strong>
            {{ result.total_questions }}
          </strong>
        </div>

        <div>
          <span>答对</span>
          <strong>
            {{ result.total_correct }}
          </strong>
        </div>

        <div>
          <span>通过标准</span>
          <strong>60%</strong>
        </div>

      </div>

      <button
        class="primary-btn"
        @click="restart"
      >
        返回考试列表
      </button>
    </div>

  </div>
</template>

<script setup>
import {
  onMounted,
  ref,
  watch
} from 'vue'

import {
  getExams,
  startExam,
  submitExam
} from '../api/exams'


const props = defineProps({
  lessonId: {
    type: Number,
    required: true
  }
})


const emit = defineEmits([
  'passed',
  'submitted'
])


const exams = ref([])

const currentExam = ref(null)

const loading = ref(false)

const submitting = ref(false)

const errorMessage = ref('')

const attemptId = ref(null)

const attemptNo = ref(null)

const answers = ref({})

const result = ref(null)


/**
 * 加载考试
 */
async function loadExams() {

  loading.value = true

  errorMessage.value = ''

  exams.value = []

  try {

    const data = await getExams(props.lessonId)

    exams.value = data

  } catch (error) {

    if (error.response?.status === 404) {

      exams.value = []

      return
    }

    errorMessage.value =
      error.response?.data?.detail ||
      '获取考试失败'

  } finally {

    loading.value = false
  }
}


/**
 * 开始考试
 */
async function beginExam(exam) {

  errorMessage.value = ''

  try {

    const data = await startExam(exam.exam_id)

    attemptId.value = data.attempt_id

    attemptNo.value = data.attempt_no

    currentExam.value = exam

    answers.value = {}

    /*
     * 初始化答案
     */
    exam.questions.forEach(question => {

      if (
        question.question_type ===
        'multipleQuestions'
      ) {

        answers.value[question.question_id] = []

      } else {

        answers.value[question.question_id] = ''
      }

    })

  } catch (error) {

    errorMessage.value =
      error.response?.data?.detail ||
      '开始考试失败'
  }
}


/**
 * 提交考试
 */
async function handleSubmit() {

  if (!attemptId.value) {
    return
  }

  submitting.value = true

  errorMessage.value = ''

  try {

    /*
     * 转换为后端要求：
     *
     * {
     *   attempt_id: xxx,
     *   questions: [
     *      {
     *        q_id: 1,
     *        answer: "A"
     *      }
     *   ]
     * }
     */

    const questions =
      currentExam.value.questions.map(question => {

        let answer =
          answers.value[question.question_id]

        /*
         * 多选题后端：
         *
         * user_answer.split(",")
         *
         * 因此数组需要转换：
         *
         * ["A","B"] → "A,B"
         */
        if (
          question.question_type ===
          'multipleQuestions'
        ) {

          answer = Array.isArray(answer)
            ? answer.join(',')
            : ''
        }

        return {
          q_id: question.question_id,
          answer: answer ?? ''
        }

      })


    const data = await submitExam({
      attempt_id: attemptId.value,
      questions
    })


    result.value = data

    emit('submitted', data)

    if (data.passed) {

      emit('passed', {
        lessonId: props.lessonId,
        examId: data.exam_id,
        result: data
      })

    }

  } catch (error) {

    errorMessage.value =
      error.response?.data?.detail ||
      '提交考试失败'

  } finally {

    submitting.value = false
  }
}


function restart() {

  currentExam.value = null

  attemptId.value = null

  attemptNo.value = null

  answers.value = {}

  result.value = null
}


function getQuestionTypeName(type) {

  const names = {

    singleQuestion: '单选题',

    multipleQuestions: '多选题',

    shortAnswer: '简答题'

  }

  return names[type] || type
}


function formatScore(score) {

  const number = Number(score)

  if (Number.isNaN(number)) {
    return '0%'
  }

  return `${number.toFixed(1)}%`
}


onMounted(() => {

  loadExams()

})


watch(
  () => props.lessonId,

  () => {

    restart()

    loadExams()

  }
)
</script>

<style scoped>
.exam-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.header {
  margin-bottom: 24px;
}

.header h2 {
  margin: 0 0 8px;
}

.exam-card {
  display: flex;
  justify-content: space-between;
  align-items: center;

  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;

  padding: 20px;
  margin-bottom: 16px;
}

.exam-card h3 {
  margin: 0 0 8px;
}

.exam-card p {
  color: #6b7280;
  margin: 0;
}

.exam-title {
  display: flex;
  justify-content: space-between;
  align-items: center;

  margin-bottom: 24px;
}

.exam-title h2 {
  margin-bottom: 5px;
}

.exam-title p {
  margin: 0;
  color: #6b7280;
}

.attempt-info {
  background: #f3f4f6;
  padding: 8px 14px;
  border-radius: 20px;
  font-size: 14px;
}

.question-card {
  background: white;

  border: 1px solid #e5e7eb;
  border-radius: 12px;

  padding: 22px;

  margin-bottom: 18px;
}

.question-title {
  display: flex;
  align-items: center;
  gap: 10px;

  font-weight: 600;

  margin-bottom: 18px;
}

.question-number {
  display: flex;
  align-items: center;
  justify-content: center;

  width: 28px;
  height: 28px;

  flex-shrink: 0;

  border-radius: 50%;

  background: #2563eb;
  color: white;

  font-size: 14px;
}

.question-type {
  margin-left: auto;

  color: #6b7280;

  font-size: 13px;
  font-weight: 400;
}

.option-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 8px;

  padding: 12px 14px;

  border: 1px solid #e5e7eb;
  border-radius: 8px;

  cursor: pointer;

  transition: 0.2s;
}

.option-item:hover {
  background: #f9fafb;
  border-color: #2563eb;
}

.option-key {
  font-weight: 600;
}

.short-answer textarea {
  width: 100%;

  box-sizing: border-box;

  padding: 12px;

  border: 1px solid #d1d5db;
  border-radius: 8px;

  resize: vertical;

  font-family: inherit;
}

.primary-btn,
.submit-btn {
  border: none;
  border-radius: 8px;

  padding: 10px 20px;

  background: #2563eb;
  color: white;

  cursor: pointer;

  font-size: 14px;
}

.primary-btn:hover,
.submit-btn:hover {
  background: #1d4ed8;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.submit-area {
  display: flex;
  justify-content: flex-end;

  margin-top: 24px;
}

.submit-btn {
  min-width: 140px;
  padding: 12px 24px;
}

.result-card {
  max-width: 500px;

  margin: 50px auto;

  text-align: center;

  background: white;

  border: 1px solid #e5e7eb;
  border-radius: 16px;

  padding: 40px;
}

.result-icon {
  width: 70px;
  height: 70px;

  margin: auto;

  border-radius: 50%;

  display: flex;
  align-items: center;
  justify-content: center;

  font-size: 40px;
  color: white;
}

.result-icon.passed {
  background: #16a34a;
}

.result-icon.failed {
  background: #dc2626;
}

.score {
  font-size: 44px;
  font-weight: 700;

  margin: 20px 0;

  color: #2563eb;
}

.result-details {
  display: grid;
  grid-template-columns: repeat(3, 1fr);

  margin-bottom: 30px;

  border-top: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb;

  padding: 18px 0;
}

.result-details div {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.result-details span {
  font-size: 13px;
  color: #6b7280;
}

.state-box {
  padding: 40px;
  text-align: center;

  color: #6b7280;
}

.state-box.error {
  color: #dc2626;
}
</style>