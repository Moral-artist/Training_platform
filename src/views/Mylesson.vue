<template>
  <div class="page">

    <div class="page-header">
      <div>
        <h1>我的课程</h1>
        <p>查看你的培训计划和课程学习进度。</p>
      </div>
    </div>


    <!-- Loading -->
    <div
      v-if="loading"
      class="state-box"
    >
      正在加载课程...
    </div>


    <!-- Empty -->
    <div
      v-else-if="plans.length === 0"
      class="state-box"
    >
      你还没有添加任何培训计划。
    </div>


    <!-- Plans -->
    <div
      v-else
      class="plan-list"
    >

      <div
        v-for="plan in plans"
        :key="plan.plan_name + plan.source_type"
        class="plan-card"
      >

        <!-- Plan Header -->
        <div class="plan-header">

          <div>

            <div class="plan-title-row">

              <h2>
                {{ plan.plan_name }}
              </h2>

              <span
                class="source-tag"
                :class="plan.source_type"
              >
                {{
                  plan.source_type === 'preset'
                    ? '预设计划'
                    : '自定义计划'
                }}
              </span>

            </div>

            <p>
              共 {{ plan.lessons.length }} 门课程
            </p>

          </div>


          <div class="progress-text">

            {{ getCompletedCount(plan) }}
            /
            {{ plan.lessons.length }}

          </div>

        </div>


        <!-- Progress -->
        <div class="progress-wrapper">

          <div class="progress-bar">

            <div
              class="progress-value"
              :style="{
                width:
                  getProgress(plan) + '%'
              }"
            />

          </div>

          <span>
            {{ getProgress(plan) }}%
          </span>

        </div>


        <!-- Lessons -->
        <div class="lesson-list">

          <div
            v-for="(lesson, index) in plan.lessons"
            :key="lesson.lesson_id"
            class="lesson-row"
          >

            <div
              class="lesson-order"
              :class="{
                completed:
                  lesson.completed
              }"
            >

              <span
                v-if="lesson.completed"
              >
                ✓
              </span>

              <span v-else>
                {{
                  lesson.lesson_order ??
                  index + 1
                }}
              </span>

            </div>


            <div class="lesson-info">

              <strong>
                {{ lesson.lesson_name }}
              </strong>

              <span>
                {{
                  lesson.completed
                    ? '已完成'
                    : '未完成'
                }}
              </span>

            </div>


            <button
              class="study-button"
              @click="
                goToLesson(
                  lesson.lesson_id
                )
              "
            >

              {{
                lesson.completed
                  ? '重新学习'
                  : '开始学习'
              }}

            </button>

          </div>

        </div>

      </div>

    </div>

  </div>
</template>


<script setup>

import {
  onMounted,
  ref
} from 'vue'

import {
  useRouter
} from 'vue-router'

import request from '../api/request'


const router =
  useRouter()


const loading =
  ref(false)


const plans =
  ref([])


// ========================================
// 加载我的课程
// ========================================

async function loadMyLessons() {

  loading.value = true

  try {

    const response =
      await request.get(
        '/api/user/my_lessons'
      )

    plans.value =
      response.data

  } catch (error) {

    console.error(
      '加载我的课程失败:',
      error
    )

  } finally {

    loading.value = false

  }

}


// ========================================
// 完成数量
// ========================================

function getCompletedCount(plan) {

  return plan.lessons.filter(
    lesson =>
      lesson.completed
  ).length

}


// ========================================
// 进度百分比
// ========================================

function getProgress(plan) {

  if (
    plan.lessons.length === 0
  ) {
    return 0
  }

  return Math.round(
    getCompletedCount(plan) /
    plan.lessons.length *
    100
  )

}


// ========================================
// 跳转课程
// ========================================

function goToLesson(lessonId) {

  router.push({
    name: 'LessonStudy',
    params: {
      lessonId
    }
  })

}


// ========================================
// 页面加载
// ========================================

onMounted(() => {

  loadMyLessons()

})

</script>


<style scoped>

* {
  box-sizing: border-box;
}

.page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 32px 24px 60px;
}


/* Header */

.page-header {
  margin-bottom: 28px;
}

.page-header h1 {
  margin: 0;
  font-size: 30px;
}

.page-header p {
  margin-top: 8px;
  color: #888;
}


/* State */

.state-box {
  padding: 50px;

  text-align: center;

  border: 1px dashed #ccc;

  border-radius: 12px;

  color: #888;

  background: #fafafa;
}


/* Plan */

.plan-list {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.plan-card {
  background: white;

  border: 1px solid #e5e5e5;

  border-radius: 14px;

  padding: 24px;

  box-shadow:
    0 2px 8px
    rgba(0,0,0,0.04);
}


/* Plan header */

.plan-header {
  display: flex;

  justify-content: space-between;

  align-items: flex-start;
}

.plan-title-row {
  display: flex;

  align-items: center;

  gap: 10px;
}

.plan-title-row h2 {
  margin: 0;

  font-size: 21px;
}

.plan-header p {
  margin: 7px 0 0;

  color: #888;

  font-size: 13px;
}


/* Source tag */

.source-tag {
  font-size: 11px;

  padding: 4px 9px;

  border-radius: 20px;
}

.source-tag.preset {
  background: #eef3ff;
  color: #4263d5;
}

.source-tag.manual {
  background: #f1f1f1;
  color: #555;
}


/* Progress */

.progress-text {
  font-weight: 600;
  color: #555;
}

.progress-wrapper {
  display: flex;

  align-items: center;

  gap: 12px;

  margin: 20px 0;
}

.progress-bar {
  flex: 1;

  height: 8px;

  background: #eee;

  border-radius: 10px;

  overflow: hidden;
}

.progress-value {
  height: 100%;

  background: #222;

  border-radius: 10px;

  transition: width 0.3s;
}

.progress-wrapper span {
  width: 42px;

  text-align: right;

  font-size: 12px;

  color: #777;
}


/* Lesson */

.lesson-list {
  display: flex;

  flex-direction: column;

  gap: 8px;
}

.lesson-row {
  display: flex;

  align-items: center;

  gap: 14px;

  padding: 13px 14px;

  border: 1px solid #eee;

  border-radius: 9px;

  background: #fafafa;
}

.lesson-order {
  width: 32px;

  height: 32px;

  border-radius: 50%;

  display: flex;

  align-items: center;

  justify-content: center;

  background: #ddd;

  color: #555;

  font-size: 13px;

  flex-shrink: 0;
}

.lesson-order.completed {
  background: #222;

  color: white;
}

.lesson-info {
  flex: 1;
}

.lesson-info strong {
  display: block;

  font-size: 14px;
}

.lesson-info span {
  display: block;

  margin-top: 4px;

  font-size: 11px;

  color: #999;
}


/* Button */

.study-button {
  border: 1px solid #ddd;

  background: white;

  padding: 8px 14px;

  border-radius: 7px;

  cursor: pointer;
}

.study-button:hover {
  background: #222;

  color: white;

  border-color: #222;
}


/* Mobile */

@media (max-width: 700px) {

  .page {
    padding: 20px 14px;
  }

  .plan-card {
    padding: 18px;
  }

  .lesson-row {
    flex-wrap: wrap;
  }

  .study-button {
    width: 100%;
  }

}

</style>