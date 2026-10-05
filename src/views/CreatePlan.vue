<template>
  <div class="page">

    <!-- 页面标题 -->
    <div class="page-header">
      <div>
        <h1>创建培训计划</h1>
        <p>选择预设培训模板，或创建自己的培训计划。</p>
      </div>
    </div>


    <!-- 模式切换 -->
    <div class="mode-tabs">

      <button
        class="tab-button"
        :class="{ active: mode === 'template' }"
        @click="switchMode('template')"
      >
        预设模板
      </button>

      <button
        class="tab-button"
        :class="{ active: mode === 'custom' }"
        @click="switchMode('custom')"
      >
        自定义计划
      </button>

    </div>


    <!-- ================================================= -->
    <!-- 预设模板 -->
    <!-- ================================================= -->

    <div
      v-if="mode === 'template'"
      class="card"
    >

      <div class="section-header">
        <div>
          <h2>预设培训模板</h2>
          <p>选择管理员创建的培训计划模板。</p>
        </div>
      </div>


      <!-- 加载状态 -->

      <div
        v-if="presetLoading"
        class="loading"
      >
        正在加载培训模板...
      </div>


      <!-- 没有模板 -->

      <div
        v-else-if="presetPlans.length === 0"
        class="empty"
      >
        当前没有可用的培训模板。
      </div>


      <!-- 模板列表 -->

      <div
        v-else
        class="template-grid"
      >

        <div
          v-for="plan in presetPlans"
          :key="plan.plan_id"
          class="template-card"
          :class="{
            selected:
              Number(templateForm.plan_id) ===
              Number(plan.plan_id)
          }"
          @click="selectTemplate(plan)"
        >

          <div class="template-top">

            <div>
              <h3>
                {{ plan.plan_name }}
              </h3>

              <span class="lesson-count">
                {{ plan.lessons.length }} 门课程
              </span>
            </div>


            <div
              class="select-circle"
              :class="{
                checked:
                  Number(templateForm.plan_id) ===
                  Number(plan.plan_id)
              }"
            >
              <span
                v-if="
                  Number(templateForm.plan_id) ===
                  Number(plan.plan_id)
                "
              >
                ✓
              </span>
            </div>

          </div>


          <!-- 模板课程 -->

          <div class="template-lessons">

            <div
              v-for="lesson in plan.lessons"
              :key="lesson.lesson_id"
              class="template-lesson"
            >

              <span class="lesson-order">
                {{ lesson.order }}
              </span>

              <span class="lesson-name">
                {{ lesson.lesson_name }}
              </span>

            </div>

          </div>

        </div>

      </div>


      <!-- 已选择模板以后 -->

      <div
        v-if="selectedTemplate"
        class="selected-section"
      >

        <h3>
          创建个人学习计划
        </h3>

        <div class="form-group">

          <label>
            计划名称
          </label>

          <input
            v-model.trim="templateForm.plan_name"
            type="text"
            placeholder="例如：我的数据中心基础培训"
            maxlength="100"
          />

        </div>


        <div class="selected-summary">

          <div>
            <span class="summary-label">
              已选择模板
            </span>

            <strong>
              {{ selectedTemplate.plan_name }}
            </strong>
          </div>

          <div>
            <span class="summary-label">
              课程数量
            </span>

            <strong>
              {{ selectedTemplate.lessons.length }}
            </strong>
          </div>

        </div>


        <button
          class="primary-button"
          :disabled="templateSubmitting"
          @click="submitTemplatePlan"
        >

          {{
            templateSubmitting
              ? '正在创建...'
              : '创建培训计划'
          }}

        </button>

      </div>

    </div>


<!-- ========================================= -->
<!-- 自定义培训计划 -->
<!-- ========================================= -->

    <div
    v-else
    class="card"
    >

    <div class="section-header">
        <div>
        <h2>自定义培训计划</h2>

        <p>
            按专业选择课程，然后调整学习顺序。
        </p>
        </div>
    </div>


    <!-- 计划名称 -->

    <div class="form-group">

        <label>
        计划名称
        </label>

        <input
        v-model.trim="customForm.plan_name"
        type="text"
        placeholder="例如：我的数据中心培训计划"
        maxlength="100"
        />

    </div>


    <!-- =============================== -->
    <!-- 专业课程选择 -->
    <!-- =============================== -->

    <div class="lesson-select-header">

        <div>
        <h3>选择课程</h3>

        <span>
            已选择 {{ customForm.lesson_list.length }} 门课程
        </span>
        </div>

    </div>


    <!-- Loading -->

    <div
        v-if="lessonLoading"
        class="loading"
    >
        正在加载课程...
    </div>


    <!-- 没有课程 -->

    <div
        v-else-if="lessonSystems.length === 0"
        class="empty"
    >
        当前暂无课程
    </div>


    <!-- 专业分类 -->

    <div
        v-else
        class="systems-container"
    >

        <div
        v-for="system in lessonSystems"
        :key="system.system_name"
        class="system-card"
        >

        <!-- 专业标题 -->

        <div
            class="system-header"
            @click="
            toggleSystem(
                system.system_name
            )
            "
        >

            <div class="system-header-left">

            <span
                class="system-arrow"
                :class="{
                expanded:
                    isSystemExpanded(
                    system.system_name
                    )
                }"
            >
                ›
            </span>


            <div>

                <h4>
                {{ system.system_name }}
                </h4>

                <span>
                {{ system.lessons.length }}
                门课程
                </span>

            </div>

            </div>


            <div class="system-selected-count">

            已选
            {{
                getSystemSelectedCount(
                system
                )
            }}

            </div>

        </div>


        <!-- 专业下的课程 -->

        <div
            v-if="
            isSystemExpanded(
                system.system_name
            )
            "
            class="system-lessons"
        >

            <label
            v-for="lesson in system.lessons"
            :key="lesson.lesson_id"
            class="lesson-checkbox-row"
            :class="{
                selected:
                isLessonSelected(
                    lesson.lesson_id
                )
            }"
            >

            <input
                type="checkbox"
                :checked="
                isLessonSelected(
                    lesson.lesson_id
                )
                "
                @change="
                toggleLesson(
                    lesson,
                    system.system_name
                )
                "
            />


            <div class="checkbox-content">

                <span class="checkbox-lesson-name">
                {{ lesson.lesson_name }}
                </span>

                <span class="checkbox-system-name">
                {{ system.system_name }}
                </span>

            </div>

            </label>

        </div>

        </div>

    </div>


    <!-- =============================== -->
    <!-- 已选择课程 -->
    <!-- =============================== -->

    <div class="selected-lessons-section">

        <div class="selected-lessons-header">

        <div>

            <h3>
            学习顺序
            </h3>

            <span>
            拖动或使用按钮调整课程顺序
            </span>

        </div>


        <button
            v-if="customForm.lesson_list.length > 0"
            class="clear-button"
            @click="clearSelectedLessons"
        >
            清空
        </button>

        </div>


        <!-- 为空 -->

        <div
        v-if="customForm.lesson_list.length === 0"
        class="empty custom-empty"
        >

        请从上方专业列表中选择课程。

        </div>


        <!-- 已选择 -->

        <div
        v-else
        class="selected-lesson-list"
        >

        <div
            v-for="(lesson, index) in customForm.lesson_list"
            :key="lesson.lesson_id"
            class="selected-lesson-row"
        >

            <!-- 顺序 -->

            <div class="selected-order">

            {{ index + 1 }}

            </div>


            <!-- 课程信息 -->

            <div class="selected-lesson-info">

            <strong>
                {{ lesson.lesson_name }}
            </strong>

            <span>
                {{ lesson.system_name }}
            </span>

            </div>


            <!-- 调整顺序 -->

            <div class="selected-actions">

            <button
                class="icon-button"
                :disabled="index === 0"
                @click="
                moveSelectedLesson(
                    index,
                    -1
                )
                "
            >
                ↑
            </button>


            <button
                class="icon-button"
                :disabled="
                index ===
                customForm.lesson_list.length - 1
                "
                @click="
                moveSelectedLesson(
                    index,
                    1
                )
                "
            >
                ↓
            </button>


            <button
                class="delete-button"
                @click="
                removeSelectedLesson(
                    index
                )
                "
            >
                删除
            </button>

            </div>

        </div>

        </div>

    </div>


    <!-- 提交 -->

    <button
        class="primary-button"
        :disabled="
        customSubmitting ||
        customForm.lesson_list.length === 0
        "
        @click="submitCustomPlan"
    >

        {{
        customSubmitting
            ? '正在创建...'
            : '创建自定义计划'
        }}

    </button>

    </div>


    <!-- ================================================= -->
    <!-- Message -->
    <!-- ================================================= -->

    <div
      v-if="message"
      class="message"
      :class="messageType"
    >

      {{ message }}

    </div>

  </div>
</template>


<script setup>

import {
  computed,
  onMounted,
  reactive,
  ref
} from 'vue'

import {
  getPresetPlanList,
  addTemplatePlan,
  addCustomPlan
} from '../api/plan'

import request from '../api/request'


// =====================================================
// 页面模式
// =====================================================

const mode = ref('template')


// =====================================================
// Loading
// =====================================================

const presetLoading = ref(false)

const templateSubmitting = ref(false)

const customSubmitting = ref(false)

const lessonSystems = ref([])

const lessonLoading = ref(false)

const expandedSystems = ref([])

// =====================================================
// Message
// =====================================================

const message = ref('')

const messageType = ref('success')


// =====================================================
// 后端数据
// =====================================================

// 整理后的预设培训计划
const presetPlans = ref([])

// 所有课程
const availableLessons = ref([])


// =====================================================
// Template Form
// =====================================================

const templateForm = reactive({

  plan_name: '',

  plan_id: ''

})


// =====================================================
// Custom Form
// =====================================================

const customForm = reactive({

  plan_name: '',

  lesson_list: []

})


// =====================================================
// 当前选择的模板
// =====================================================

const selectedTemplate = computed(() => {

  if (!templateForm.plan_id) {
    return null
  }


  return presetPlans.value.find(

    plan =>
      Number(plan.plan_id) ===
      Number(templateForm.plan_id)

  )

})


// =====================================================
// 切换模式
// =====================================================

function switchMode(newMode) {

  mode.value = newMode

  clearMessage()

}


// =====================================================
// 加载预设模板
// =====================================================

async function loadPresetPlans() {

  presetLoading.value = true


  try {

    const response =
      await getPresetPlanList()


    /*
      后端返回：

      [
        {
          plan_id: 1,
          plan_name: "基础培训",
          order: 1,
          lesson_id: 3,
          lesson_name: "UPS基础"
        },
        ...
      ]
    */

    const rawData =
      response.data


    const planMap =
      new Map()


    rawData.forEach(item => {

      const planId =
        item.plan_id


      if (!planMap.has(planId)) {

        planMap.set(planId, {

          plan_id:
            item.plan_id,

          plan_name:
            item.plan_name,

          lessons: []

        })

      }


      planMap
        .get(planId)
        .lessons
        .push({

          lesson_id:
            item.lesson_id,

          lesson_name:
            item.lesson_name,

          order:
            item.order

        })

    })


    // 确保课程顺序正确

    planMap.forEach(plan => {

      plan.lessons.sort(
        (a, b) =>
          a.order - b.order
      )

    })


    presetPlans.value =
      Array.from(
        planMap.values()
      )


  } catch (error) {

    console.error(
      '加载预设培训计划失败:',
      error
    )


    showMessage(
      error.response?.data?.detail ||
      '加载培训模板失败',
      'error'
    )

  } finally {

    presetLoading.value = false

  }

}


// =====================================================
// 获取课程
// =====================================================

async function loadLessons() {

  lessonLoading.value = true

  try {

    const response =
      await request.get(
        '/api/lessons/alllessons'
      )

    /*
      后端：

      [
        {
          system_name: "Electrical",
          lessons: [
            {
              lesson_id: 1,
              lesson_name: "UPS基础"
            }
          ]
        }
      ]
    */

    lessonSystems.value =
      response.data


    // 默认展开第一个专业

    if (
      response.data.length > 0
    ) {

      expandedSystems.value = [
        response.data[0]
          .system_name
      ]

    }

  } catch (error) {

    console.error(
      '加载课程失败:',
      error
    )

    showMessage(
      error.response?.data?.detail ||
      '加载课程失败',
      'error'
    )

  } finally {

    lessonLoading.value = false

  }

}

function toggleSystem(systemName) {

  const index =
    expandedSystems.value.indexOf(
      systemName
    )

  if (index >= 0) {

    expandedSystems.value.splice(
      index,
      1
    )

  } else {

    expandedSystems.value.push(
      systemName
    )

  }

}


function isSystemExpanded(
  systemName
) {

  return expandedSystems.value.includes(
    systemName
  )

}

function isLessonSelected(
  lessonId
) {

  return customForm
    .lesson_list
    .some(
      item =>
        Number(item.lesson_id) ===
        Number(lessonId)
    )

}

function toggleLesson(
  lesson,
  systemName
) {

  const index =
    customForm
      .lesson_list
      .findIndex(
        item =>
          Number(item.lesson_id) ===
          Number(lesson.lesson_id)
      )


  // 已经选择 → 取消
  if (index >= 0) {

    customForm
      .lesson_list
      .splice(
        index,
        1
      )

    updateCustomOrder()

    return
  }


  // 没有选择 → 添加
  customForm
    .lesson_list
    .push({

      lesson_id:
        lesson.lesson_id,

      lesson_name:
        lesson.lesson_name,

      system_name:
        systemName,

      order:
        customForm
          .lesson_list
          .length + 1

    })

}

function getSystemSelectedCount(
  system
) {

  return system.lessons.filter(
    lesson =>
      isLessonSelected(
        lesson.lesson_id
      )
  ).length

}

function removeSelectedLesson(
  index
) {

  customForm
    .lesson_list
    .splice(
      index,
      1
    )

  updateCustomOrder()

}

function clearSelectedLessons() {

  customForm.lesson_list = []

}

function updateCustomOrder() {

  customForm
    .lesson_list
    .forEach(
      (item, index) => {

        item.order =
          index + 1

      }
    )

}

function moveSelectedLesson(index, direction) {
  const targetIndex = index + direction

  if (
    targetIndex < 0 ||
    targetIndex >= customForm.lesson_list.length
  ) {
    return
  }

  const list = customForm.lesson_list

  const temp = list[index]
  list[index] = list[targetIndex]
  list[targetIndex] = temp

  updateCustomOrder()
}

async function submitCustomPlan() {

  clearMessage()


  if (!customForm.plan_name) {

    showMessage(
      '请输入计划名称',
      'error'
    )

    return

  }


  if (
    customForm.lesson_list.length === 0
  ) {

    showMessage(
      '请至少选择一门课程',
      'error'
    )

    return

  }


  customSubmitting.value = true


  try {

    const payload = {

      plan_name:
        customForm.plan_name,

      lesson_list:
        customForm
          .lesson_list
          .map(
            (lesson, index) => ({

              lesson_id:
                Number(
                  lesson.lesson_id
                ),

              order:
                index + 1

            })
          )

    }


    console.log(
      'Add custom plan:',
      payload
    )


    const response =
      await addCustomPlan(
        payload
      )


    showMessage(
      response.data?.message ||
      '自定义计划创建成功',
      'success'
    )


    customForm.plan_name = ''

    customForm.lesson_list = []


  } catch (error) {

    handleError(error)

  } finally {

    customSubmitting.value = false

  }

}

// =====================================================
// 选择模板
// =====================================================

function selectTemplate(plan) {

  templateForm.plan_id =
    plan.plan_id


  // 默认名字

  if (!templateForm.plan_name) {

    templateForm.plan_name =
      plan.plan_name

  }

}


// =====================================================
// 提交模板计划
// =====================================================

async function submitTemplatePlan() {

  clearMessage()


  if (!templateForm.plan_id) {

    showMessage(
      '请选择培训模板',
      'error'
    )

    return

  }


  if (!templateForm.plan_name) {

    showMessage(
      '请输入计划名称',
      'error'
    )

    return

  }


  templateSubmitting.value = true


  try {

    const payload = {

      plan_name:
        templateForm.plan_name,

      plan_id:
        Number(
          templateForm.plan_id
        )

    }


    console.log(
      'Add template plan:',
      payload
    )


    const response =
      await addTemplatePlan(
        payload
      )


    showMessage(
      response.data?.message ||
      '培训计划创建成功',
      'success'
    )


    templateForm.plan_name = ''

    templateForm.plan_id = ''


  } catch (error) {

    handleError(error)

  } finally {

    templateSubmitting.value = false

  }

}


// =====================================================
// 错误统一处理
// =====================================================

function handleError(error) {

  console.error(
    'Request error:',
    error
  )


  const status =
    error.response?.status


  const detail =
    error.response?.data?.detail


  // Membership

  if (
    status === 409 &&
    detail === 'No access'
  ) {

    showMessage(
      '当前会员等级没有权限使用该功能',
      'error'
    )

    return

  }


  // Session

  if (status === 401) {

    showMessage(
      '登录状态已失效，请重新登录',
      'error'
    )

    return

  }


  // CSRF

  if (status === 403) {

    showMessage(
      'CSRF 验证失败，请刷新页面后重试',
      'error'
    )

    return

  }


  if (status === 422) {

    showMessage(
      '提交的数据格式不正确',
      'error'
    )

    return

  }


  showMessage(
    detail ||
    '操作失败，请稍后重试',
    'error'
  )

}


// =====================================================
// Message
// =====================================================

function showMessage(
  text,
  type = 'success'
) {

  message.value =
    text

  messageType.value =
    type


  window.scrollTo({

    top: 0,

    behavior: 'smooth'

  })

}


function clearMessage() {

  message.value = ''

}


// =====================================================
// 页面加载
// =====================================================

onMounted(() => {

  loadPresetPlans()

  loadLessons()

})

</script>


<style scoped>

* {
  box-sizing: border-box;
}

.page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px 24px 60px;
  color: #222;
}


/* ===========================
   Header
=========================== */

.page-header {
  margin-bottom: 26px;
}

.page-header h1 {
  margin: 0;
  font-size: 30px;
  font-weight: 700;
}

.page-header p {
  margin: 8px 0 0;
  color: #777;
  font-size: 14px;
}


/* ===========================
   Tabs
=========================== */

.mode-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 22px;
}

.tab-button {
  border: 1px solid #ddd;
  background: white;
  color: #555;

  padding: 10px 22px;

  border-radius: 8px;

  font-size: 14px;

  cursor: pointer;

  transition: 0.2s;
}

.tab-button:hover {
  background: #f5f5f5;
}

.tab-button.active {
  background: #222;
  color: white;
  border-color: #222;
}


/* ===========================
   Card
=========================== */

.card {
  background: white;

  border: 1px solid #e5e5e5;

  border-radius: 14px;

  padding: 28px;

  box-shadow:
    0 2px 8px rgba(
      0,
      0,
      0,
      0.04
    );
}


.section-header {
  margin-bottom: 24px;
}

.section-header h2 {
  margin: 0;

  font-size: 22px;
}

.section-header p {
  margin: 7px 0 0;

  color: #888;

  font-size: 14px;
}


/* ===========================
   Templates
=========================== */

.template-grid {
  display: grid;

  grid-template-columns:
    repeat(
      auto-fill,
      minmax(280px, 1fr)
    );

  gap: 16px;
}


.template-card {
  border: 1px solid #ddd;

  border-radius: 12px;

  padding: 18px;

  cursor: pointer;

  transition:
    border-color 0.2s,
    box-shadow 0.2s,
    transform 0.2s;
}


.template-card:hover {
  border-color: #888;

  transform:
    translateY(-1px);
}


.template-card.selected {
  border-color: #222;

  box-shadow:
    0 0 0 1px #222;
}


.template-top {
  display: flex;

  align-items: flex-start;

  justify-content:
    space-between;

  gap: 10px;
}


.template-top h3 {
  margin: 0;

  font-size: 17px;
}


.lesson-count {
  display: inline-block;

  margin-top: 7px;

  color: #888;

  font-size: 12px;
}


.select-circle {
  width: 23px;

  height: 23px;

  border-radius: 50%;

  border:
    1px solid #bbb;

  display: flex;

  align-items: center;

  justify-content:
    center;

  flex-shrink: 0;
}


.select-circle.checked {
  color: white;

  background: #222;

  border-color: #222;
}


/* ===========================
   Template lessons
=========================== */

.template-lessons {
  margin-top: 18px;

  border-top:
    1px solid #eee;

  padding-top: 12px;
}


.template-lesson {
  display: flex;

  align-items: center;

  gap: 10px;

  padding: 7px 0;

  font-size: 13px;
}


.lesson-order {
  width: 24px;

  height: 24px;

  display: flex;

  align-items: center;

  justify-content:
    center;

  border-radius: 50%;

  background: #f2f2f2;

  font-size: 12px;

  flex-shrink: 0;
}


.lesson-name {
  overflow: hidden;

  text-overflow:
    ellipsis;

  white-space: nowrap;
}


/* ===========================
   Selected
=========================== */

.selected-section {
  margin-top: 28px;

  padding-top: 25px;

  border-top:
    1px solid #eee;
}

.selected-section h3 {
  margin:
    0 0 18px;
}


.selected-summary {
  display: flex;

  gap: 40px;

  padding: 16px;

  margin:
    14px 0 5px;

  border-radius: 8px;

  background: #f8f8f8;
}


.selected-summary > div {
  display: flex;

  flex-direction:
    column;

  gap: 4px;
}


.summary-label {
  color: #888;

  font-size: 12px;
}


/* ===========================
   Form
=========================== */

.form-group {
  display: flex;

  flex-direction:
    column;

  gap: 8px;

  margin-bottom: 20px;
}


.form-group label {
  font-size: 14px;

  font-weight: 600;
}


input,
select {
  width: 100%;

  height: 44px;

  padding:
    0 12px;

  border:
    1px solid #d5d5d5;

  border-radius: 8px;

  background: white;

  color: #222;

  outline: none;

  font-size: 14px;

  transition:
    border-color 0.2s;
}


input:focus,
select:focus {
  border-color: #222;
}


/* ===========================
   Custom lesson
=========================== */

.lesson-section-header {
  display: flex;

  justify-content:
    space-between;

  align-items: center;

  gap: 20px;

  margin:
    30px 0 16px;
}


.lesson-section-header h3 {
  margin: 0;
}


.lesson-section-header span {
  display: block;

  color: #888;

  font-size: 12px;

  margin-top: 5px;
}

.lesson-select-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 30px 0 16px;
}

.lesson-select-header h3 {
  margin: 0;
}

.lesson-select-header span {
  display: block;
  margin-top: 5px;
  color: #888;
  font-size: 12px;
}


/* =============================
   专业列表
============================= */

.systems-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.system-card {
  border: 1px solid #e3e3e3;
  border-radius: 10px;
  overflow: hidden;
}

.system-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  padding: 15px 18px;

  background: #fafafa;

  cursor: pointer;

  user-select: none;
}

.system-header:hover {
  background: #f5f5f5;
}

.system-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.system-header h4 {
  margin: 0;
  font-size: 15px;
}

.system-header-left span:not(.system-arrow) {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #888;
}

.system-arrow {
  display: inline-block;

  font-size: 24px;

  transform: rotate(0deg);

  transition: transform 0.2s;
}

.system-arrow.expanded {
  transform: rotate(90deg);
}

.system-selected-count {
  font-size: 12px;
  color: #666;

  background: #eee;

  padding: 5px 10px;

  border-radius: 20px;
}


/* =============================
   专业下课程
============================= */

.system-lessons {
  padding: 8px 14px 14px;

  background: white;
}

.lesson-checkbox-row {
  display: flex;
  align-items: center;
  gap: 12px;

  padding: 12px;

  margin-top: 6px;

  border: 1px solid transparent;

  border-radius: 8px;

  cursor: pointer;

  transition: 0.15s;
}

.lesson-checkbox-row:hover {
  background: #f8f8f8;
}

.lesson-checkbox-row.selected {
  border-color: #ccc;
  background: #f7f7f7;
}

.lesson-checkbox-row input {
  width: 17px;
  height: 17px;

  flex-shrink: 0;
}

.checkbox-content {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.checkbox-lesson-name {
  font-size: 14px;
  color: #222;
}

.checkbox-system-name {
  font-size: 11px;
  color: #999;
}


/* =============================
   已选择课程
============================= */

.selected-lessons-section {
  margin-top: 30px;

  padding-top: 24px;

  border-top: 1px solid #eee;
}

.selected-lessons-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  margin-bottom: 15px;
}

.selected-lessons-header h3 {
  margin: 0;
}

.selected-lessons-header span {
  display: block;

  margin-top: 4px;

  color: #888;

  font-size: 12px;
}

.selected-lesson-list {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.selected-lesson-row {
  display: flex;
  align-items: center;
  gap: 14px;

  padding: 13px 14px;

  border: 1px solid #e4e4e4;

  border-radius: 9px;

  background: #fafafa;
}

.selected-order {
  width: 32px;
  height: 32px;

  display: flex;
  align-items: center;
  justify-content: center;

  border-radius: 50%;

  background: #222;
  color: white;

  font-size: 13px;

  flex-shrink: 0;
}

.selected-lesson-info {
  flex: 1;

  min-width: 0;
}

.selected-lesson-info strong {
  display: block;

  overflow: hidden;

  white-space: nowrap;

  text-overflow: ellipsis;

  font-size: 14px;
}

.selected-lesson-info span {
  display: block;

  margin-top: 4px;

  color: #999;

  font-size: 11px;
}

.selected-actions {
  display: flex;
  gap: 6px;

  flex-shrink: 0;
}

.clear-button {
  border: none;

  background: transparent;

  color: #999;

  cursor: pointer;
}

.clear-button:hover {
  color: #c33;
}

.custom-lessons {
  display: flex;

  flex-direction:
    column;

  gap: 10px;
}


.custom-lesson-row {
  display: flex;

  align-items:
    flex-end;

  gap: 12px;

  padding: 14px;

  border:
    1px solid #e5e5e5;

  border-radius: 10px;

  background: #fafafa;
}


.drag-order {
  width: 32px;

  height: 32px;

  display: flex;

  align-items: center;

  justify-content:
    center;

  background: #222;

  color: white;

  border-radius: 50%;

  flex-shrink: 0;

  margin-bottom: 6px;
}


.lesson-selector {
  flex: 1;
}


.lesson-selector label {
  display: block;

  margin-bottom: 7px;

  color: #777;

  font-size: 12px;
}


.lesson-actions {
  display: flex;

  gap: 6px;

  padding-bottom: 3px;
}


/* ===========================
   Buttons
=========================== */

.primary-button {
  width: 100%;

  height: 46px;

  margin-top: 24px;

  border: none;

  border-radius: 8px;

  background: #222;

  color: white;

  font-size: 14px;

  font-weight: 600;

  cursor: pointer;

  transition:
    opacity 0.2s,
    transform 0.1s;
}


.primary-button:hover:not(:disabled) {
  opacity: 0.9;
}


.primary-button:active:not(:disabled) {
  transform:
    scale(0.995);
}


.primary-button:disabled {
  opacity: 0.5;

  cursor:
    not-allowed;
}


.secondary-button {
  border:
    1px solid #ddd;

  background: white;

  color: #333;

  padding:
    9px 14px;

  border-radius: 7px;

  cursor: pointer;
}


.secondary-button:hover {
  background: #f5f5f5;
}


.icon-button {
  width: 34px;

  height: 34px;

  border:
    1px solid #ddd;

  background: white;

  border-radius: 6px;

  cursor: pointer;
}


.icon-button:disabled {
  opacity: 0.35;

  cursor:
    not-allowed;
}


.delete-button {
  height: 34px;

  padding:
    0 12px;

  border: none;

  border-radius: 6px;

  background: #feecec;

  color: #c33;

  cursor: pointer;
}


/* ===========================
   Empty
=========================== */

.empty {
  padding: 40px;

  text-align: center;

  color: #999;

  border:
    1px dashed #ccc;

  border-radius: 10px;

  background: #fafafa;
}


.custom-empty {
  display: flex;

  flex-direction:
    column;

  align-items: center;

  gap: 12px;
}


.empty-icon {
  width: 42px;

  height: 42px;

  border-radius: 50%;

  display: flex;

  align-items: center;

  justify-content:
    center;

  background: #eee;

  color: #777;

  font-size: 25px;
}


/* ===========================
   Loading
=========================== */

.loading {
  padding: 50px;

  text-align: center;

  color: #777;
}


/* ===========================
   Message
=========================== */

.message {
  position: fixed;

  top: 25px;

  left: 50%;

  transform:
    translateX(-50%);

  padding:
    12px 20px;

  border-radius: 8px;

  z-index: 1000;

  box-shadow:
    0 4px 16px
    rgba(
      0,
      0,
      0,
      0.15
    );
}


.message.success {
  background: #eaf8ee;

  color: #208640;

  border:
    1px solid #bee5c8;
}


.message.error {
  background: #ffeded;

  color: #c33;

  border:
    1px solid #f0bcbc;
}


/* ===========================
   Mobile
=========================== */

@media (
  max-width: 700px
) {

  .page {
    padding:
      20px 14px 40px;
  }


  .card {
    padding: 18px;
  }


  .template-grid {
    grid-template-columns:
      1fr;
  }


  .custom-lesson-row {
    flex-wrap: wrap;
  }


  .lesson-selector {
    width:
      calc(100% - 50px);
  }


  .lesson-actions {
    width: 100%;

    justify-content:
      flex-end;
  }


  .selected-summary {
    flex-direction:
      column;

    gap: 12px;
  }

}

</style>