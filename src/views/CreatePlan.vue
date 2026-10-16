<template>
  <div class="page">

    <!-- 页面标题 -->
    <div class="page-header">
      <div>
        <h1>{{ t("createTrainingPlan") }}</h1>
        <p>{{ t("createPlanDescription") }}</p>
      </div>
    </div>


    <!-- 模式切换 -->
    <div class="mode-tabs">

      <button
        class="tab-button"
        :class="{ active: mode === 'template' }"
        @click="switchMode('template')"
      >
        {{ t("presetTemplate") }}
      </button>

      <button
        class="tab-button"
        :class="{ active: mode === 'custom' }"
        @click="switchMode('custom')"
      >
        {{ t("customPlan") }}
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
          {{t("presetTrainingTemplate")}}
          <p>{{ t("presetTemplateHint") }}</p>
        </div>
      </div>


      <!-- 加载状态 -->

      <div
        v-if="presetLoading"
        class="loading"
      >
        {{ t("loadingTemplates") }}
      </div>


      <!-- 没有模板 -->

      <div
        v-else-if="presetPlans.length === 0"
        class="empty"
      >
        {{ t("noTemplates") }}
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
                {{ t("courseCount").replace("{count}", String(plan.lessons.length)) }}
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
          {{t("createPersonalPlan")}}
        </h3>

        <div class="form-group">

          <label>
            {{t("planName")}}
          </label>

          <input
            v-model.trim="templateForm.plan_name"
            type="text"
            :placeholder="t('planNamePlaceholder')"
            maxlength="100"
          />

        </div>


        <div class="selected-summary">

          <div>
            <span class="summary-label">
              {{t("selectedTemplate")}}
            </span>

            <strong>
              {{ selectedTemplate.plan_name }}
            </strong>
          </div>

          <div>
            <span class="summary-label">
              {{t("courseQuantity")}}
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

          {{ templateSubmitting ? t("creating") : t("createTrainingPlan") }}

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
        <h2>{{ t("customTrainingPlan") }}</h2>

        <p>
            {{t("customPlanHint")}}
        </p>
        </div>
    </div>


    <!-- 计划名称 -->

    <div class="form-group">

        <label>
        {{t("planName")}}
        </label>

        <input
        v-model.trim="customForm.plan_name"
        type="text"
        :placeholder="t('customPlanPlaceholder')"
        maxlength="100"
        />

    </div>


    <!-- =============================== -->
    <!-- 专业课程选择 -->
    <!-- =============================== -->

    <div class="lesson-select-header">

        <div>
        <h3>{{t("selectCourse")}}</h3>

        <span>
          {{
            t("selectedCoursesCount").replace(
              "{count}",
              String(customForm.lesson_list.length)
            )
          }}
        </span>
        </div>

    </div>


    <!-- Loading -->

    <div
        v-if="lessonLoading"
        class="loading"
    >
        {{t("loadingCourses")}}
    </div>


    <!-- 没有课程 -->

    <div
        v-else-if="lessonSystems.length === 0"
        class="empty"
    >
        {{t("noCoursesAvailable")}}
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
                  {{ t("courseCount").replace("{count}", String(system.lessons.length)) }}
                </span>
            </div>

            </div>


            <div class="system-selected-count">

              {{
                t("selectedCount").replace(
                  "{count}",
                  String(getSystemSelectedCount(system))
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
            {{t("learningOrder")}}
            </h3>

            <span>
            {{t("reorderHint")}}
            </span>

        </div>


        <button
            v-if="customForm.lesson_list.length > 0"
            class="clear-button"
            @click="clearSelectedLessons"
        >
          {{t("clearAll")}}
        </button>

        </div>


        <!-- 为空 -->

        <div
        v-if="customForm.lesson_list.length === 0"
        class="empty custom-empty"
        >

        {{t("selectCoursesHint")}}

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
                {{ t("delete") }}
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

      {{ customSubmitting ? t("creating") : t("createCustomPlan") }}

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
  import { getMembershipLevel } from '../api/request'
  import { t } from '../i18n'

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
    clearMessage()

    const membershipLevel = getMembershipLevel()

    // 示例：自定义计划要求等级 >= 1
    if (
      newMode === 'custom' &&
      (membershipLevel === null || membershipLevel < 1)
    ) {
      showMessage(
        '当前会员等级不足，无法使用自定义培训计划',
        'error'
      )
      return
    }

    mode.value = newMode
  }


  // =====================================================
  // 加载预设模板
  // =====================================================

  async function loadPresetPlans() {
    presetLoading.value = true

    try {
      const response = await getPresetPlanList()

      const rawData = response.data

      presetPlans.value = rawData.map(plan => ({
        plan_id: plan.plan_id,
        plan_name: plan.plan_name,
        description: plan.description,
        lessons: [...(plan.lessons || [])].sort(
          (a, b) => a.order - b.order
        )
      }))


    } catch (error) {
      console.error('加载预设培训计划失败:', error)

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

      console.log("alllesson:",lessonSystems.value)

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
  .page {
    padding: 32px 40px 56px;
    background: #f4f7fc;
    min-height: 100%;
  }

  .page-header {
    margin-bottom: 24px;
  }

  .page-header h1 {
    margin: 0;
    font-size: 44px;
    font-weight: 800;
    color: #162033;
    line-height: 1.15;
  }

  .page-header p {
    margin: 10px 0 0;
    font-size: 16px;
    color: #6b7280;
  }

  .mode-tabs {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
  }

  .tab-button {
    min-width: 116px;
    height: 44px;
    padding: 0 18px;
    border-radius: 12px;
    border: 1px solid #d8e2f0;
    background: #ffffff;
    color: #3b4a67;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .tab-button:hover {
    border-color: #8bb7ff;
    color: #2f6bff;
    background: #f8fbff;
  }

  .tab-button.active {
    background: #eaf2ff;
    color: #2f6bff;
    border-color: #8bb7ff;
    box-shadow: inset 0 0 0 1px rgba(47, 107, 255, 0.08);
  }

  .card {
    background: #ffffff;
    border: 1px solid #e6edf7;
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(31, 41, 55, 0.05);
    padding: 28px 32px;
  }

  .section-header {
    margin-bottom: 24px;
  }

  .section-header h2 {
    margin: 0;
    font-size: 24px;
    font-weight: 800;
    color: #172033;
  }

  .section-header p {
    margin: 8px 0 0;
    font-size: 15px;
    color: #6b7280;
  }

  .form-group {
    margin-bottom: 28px;
  }

  .form-group label {
    display: inline-block;
    margin-bottom: 10px;
    font-size: 15px;
    font-weight: 700;
    color: #172033;
  }

  .form-group input {
    width: 100%;
    height: 48px;
    padding: 0 16px;
    border: 1px solid #d9e2ef;
    border-radius: 12px;
    background: #ffffff;
    color: #172033;
    font-size: 15px;
    outline: none;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
    box-sizing: border-box;
  }

  .form-group input:focus {
    border-color: #7aa8ff;
    box-shadow: 0 0 0 4px rgba(47, 107, 255, 0.12);
  }

  .lesson-select-header,
  .selected-lessons-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 16px;
    margin-bottom: 16px;
  }

  .lesson-select-header h3,
  .selected-lessons-header h3 {
    margin: 0;
    font-size: 24px;
    font-weight: 800;
    color: #172033;
  }

  .lesson-select-header span,
  .selected-lessons-header span {
    display: inline-block;
    margin-top: 8px;
    color: #6b7280;
    font-size: 14px;
  }

  .loading,
  .empty,
  .custom-empty {
    border: 1px dashed #d7e3f4;
    border-radius: 14px;
    background: #f8fbff;
    color: #6b7280;
    padding: 20px 18px;
    font-size: 14px;
  }

  .systems-container {
    display: grid;
    gap: 16px;
    margin-bottom: 28px;
  }

  .system-card {
    border: 1px solid #e6edf7;
    border-radius: 16px;
    background: #fcfdff;
    overflow: hidden;
  }

  .system-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    padding: 18px 20px;
    cursor: pointer;
    background: #ffffff;
  }

  .system-header:hover {
    background: #f8fbff;
  }

  .system-header-left {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .system-arrow {
    display: inline-block;
    font-size: 18px;
    color: #6b7280;
    transition: transform 0.2s ease;
  }

  .system-arrow.expanded {
    transform: rotate(90deg);
  }

  .system-header h4 {
    margin: 0;
    font-size: 18px;
    font-weight: 700;
    color: #172033;
  }

  .system-header span {
    font-size: 13px;
    color: #7b8798;
  }

  .system-selected-count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 68px;
    height: 32px;
    padding: 0 12px;
    border-radius: 999px;
    background: #eef4ff;
    color: #2f6bff;
    font-size: 13px;
    font-weight: 700;
  }

  .system-lessons {
    padding: 8px 16px 18px;
    background: #fbfcff;
  }

  .lesson-checkbox-row {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 12px;
    border-radius: 12px;
    cursor: pointer;
    transition: background 0.2s ease, border-color 0.2s ease;
  }

  .lesson-checkbox-row:hover {
    background: #f4f8ff;
  }

  .lesson-checkbox-row.selected {
    background: #eef4ff;
  }

  .lesson-checkbox-row input[type="checkbox"] {
    width: 18px;
    height: 18px;
    accent-color: #2f6bff;
    flex-shrink: 0;
  }

  .checkbox-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .checkbox-lesson-name {
    font-size: 15px;
    font-weight: 600;
    color: #172033;
  }

  .checkbox-system-name {
    font-size: 13px;
    color: #7b8798;
  }

  .selected-lessons-section {
    margin-top: 8px;
  }

  .selected-lesson-list {
    display: grid;
    gap: 12px;
    margin-bottom: 24px;
  }

  .selected-lesson-row {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px 18px;
    background: #ffffff;
    border: 1px solid #e6edf7;
    border-radius: 14px;
  }

  .selected-order {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: #eaf2ff;
    color: #2f6bff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    flex-shrink: 0;
  }

  .selected-lesson-info {
    flex: 1;
    min-width: 0;
  }

  .selected-lesson-info strong {
    display: block;
    color: #172033;
    font-size: 15px;
    font-weight: 700;
  }

  .selected-lesson-info span {
    display: inline-block;
    margin-top: 4px;
    color: #7b8798;
    font-size: 13px;
  }

  .selected-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .icon-button,
  .clear-button,
  .delete-button,
  .primary-button {
    border: none;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .icon-button {
    width: 36px;
    height: 36px;
    background: #f3f6fb;
    color: #31415f;
  }

  .icon-button:hover:not(:disabled) {
    background: #e8eef9;
  }

  .icon-button:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .clear-button {
    height: 40px;
    padding: 0 16px;
    background: #fff7f7;
    color: #d14343;
    border: 1px solid #ffd9d9;
  }

  .clear-button:hover {
    background: #ffecec;
  }

  .delete-button {
    height: 36px;
    padding: 0 14px;
    background: #fff7f7;
    color: #d14343;
    border: 1px solid #ffd9d9;
  }

  .delete-button:hover {
    background: #ffecec;
  }

  .primary-button {
    height: 46px;
    min-width: 180px;
    padding: 0 20px;
    background: #2f6bff;
    color: #ffffff;
    box-shadow: 0 10px 20px rgba(47, 107, 255, 0.18);
  }

  .primary-button:hover:not(:disabled) {
    background: #245bef;
  }

  .primary-button:disabled {
    opacity: 0.55;
    cursor: not-allowed;
    box-shadow: none;
  }

  .message {
    margin-top: 18px;
    padding: 14px 16px;
    border-radius: 12px;
    font-size: 14px;
  }

  .message.success {
    background: #edf9f0;
    color: #23844d;
    border: 1px solid #cdeed8;
  }

  .message.error {
    background: #fff4f4;
    color: #c13c3c;
    border: 1px solid #ffd5d5;
  }

  @media (max-width: 900px) {
    .page {
      padding: 20px 16px 36px;
    }

    .card {
      padding: 20px 18px;
      border-radius: 16px;
    }

    .lesson-select-header,
    .selected-lessons-header,
    .selected-lesson-row,
    .system-header {
      flex-direction: column;
      align-items: flex-start;
    }

    .selected-actions {
      width: 100%;
      justify-content: flex-start;
    }
  }
  
  /* 预设模板区域 */
  .template-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 18px;
    margin-top: 24px;
  }

  /* 每张培训模板卡片 */
  .template-card {
    padding: 22px;
    background: #ffffff;
    border: 1px solid #dfe7f4;
    border-radius: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .template-card:hover {
    border-color: #9bbcff;
    background: #f8fbff;
    box-shadow: 0 6px 20px rgba(47, 107, 255, 0.08);
    transform: translateY(-2px);
  }

  .template-card.selected {
    border-color: #3b6df6;
    background: #f0f5ff;
    box-shadow: 0 0 0 2px rgba(59, 109, 246, 0.1);
  }

  /* 模板标题和选择状态 */
  .template-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 18px;
  }

  .template-top h3 {
    margin: 0 0 8px;
    color: #172033;
    font-size: 18px;
    font-weight: 700;
  }

  .lesson-count {
    display: inline-block;
    color: #718096;
    font-size: 13px;
  }

  /* 模板选中标识 */
  .select-circle {
    width: 24px;
    height: 24px;
    border: 2px solid #cbd5e1;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    color: #ffffff;
  }

  .select-circle.checked {
    background: #3b6df6;
    border-color: #3b6df6;
  }

  /* 模板内的课程列表 */
  .template-lessons {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding-top: 16px;
    border-top: 1px solid #edf1f7;
  }

  .template-lesson {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    background: #f7f9fd;
    border-radius: 10px;
  }

  .lesson-order {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    flex-shrink: 0;
    border-radius: 8px;
    background: #e8efff;
    color: #3768e8;
    font-size: 13px;
    font-weight: 700;
  }

  .lesson-name {
    min-width: 0;
    color: #334155;
    font-size: 14px;
    line-height: 1.5;
    overflow-wrap: anywhere;
  }

  /* 已选择模板后的表单 */
  .selected-section {
    margin-top: 24px;
    padding: 24px;
    background: #f8fbff;
    border: 1px solid #dfe7f4;
    border-radius: 14px;
  }

  .selected-section h3 {
    margin: 0 0 20px;
    font-size: 19px;
    color: #172033;
  }

  .selected-summary {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
    margin: 20px 0;
  }

  .selected-summary > div {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 16px;
    background: #ffffff;
    border: 1px solid #e6edf7;
    border-radius: 10px;
  }

  .summary-label {
    font-size: 13px;
    color: #718096;
  }

  /* 与主 Layout 匹配的标题尺寸 */
  .page-header h1 {
    font-size: clamp(26px, 2.5vw, 36px);
    line-height: 1.25;
    font-weight: 750;
  }

  .page-header p {
    font-size: 14px;
    line-height: 1.6;
  }

  /* 响应式 */
  @media (max-width: 900px) {
    .template-grid {
      grid-template-columns: 1fr;
    }

    .selected-summary {
      grid-template-columns: 1fr;
    }

    .template-card {
      padding: 18px;
    }
  }

</style>
