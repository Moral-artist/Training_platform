<script setup>
  import { computed, onMounted, reactive, ref } from 'vue'
  import request from '../api/request'
  import { t } from '../i18n'

  // 如果你的 APIRouter 有额外 prefix，只需修改这里的地址。
  const API = {
    systems: '/api/lessons/systems',
    lessons: (systemId) => `/api/lessons/majors/${systemId}/lessonlist`,
    create: '/api/plan/create_preset_plan',
    list: '/api/plan/preset_planlist',
    delete: (planId) =>
      `/api/plan/presetPlan_delete/${planId}`,
  }
  const PAGE_SIZE = 4

  const form = reactive({ plan_name: '', description: '' })
  const systems = ref([])
  const lessonsBySystem = reactive({})
  const expandedSystemId = ref(null)
  const selectedLessons = ref([])
  const existingTemplates = ref([])
  const loadingSystems = ref(false)
  const loadingTemplates = ref(false)
  const submitting = ref(false)
  const systemsError = ref('')
  const templatesError = ref('')
  const formError = ref('')
  const successMessage = ref('')

  const selectedIds = computed(() => new Set(selectedLessons.value.map((item) => item.lesson_id)))
  const selectedCount = computed(() => selectedLessons.value.length)

  function interpolate(key, variables = {}) {
    let result = t(key)
    for (const [name, value] of Object.entries(variables)) {
      result = result.replace(`{${name}}`, String(value))
    }
    return result
  }

  function errorText(error) {
    const status = error?.response?.status
    const detail = error?.response?.data?.detail
    if (typeof detail === 'string' && detail) return detail
    if (status) return t(`HTTP_${status}`)
    return t('networkError')
  }

  function readArray(payload, keys) {
    if (Array.isArray(payload)) return payload
    for (const key of keys) {
      if (Array.isArray(payload?.[key])) return payload[key]
    }
    return []
  }

  async function loadSystems() {
    loadingSystems.value = true;
    systemsError.value = "";

    try {
      const { data } = await request.get(API.systems);

      systems.value = readArray(data, ["systems", "items", "data"])
        .map((item) => ({
          system_id: Number(item.system_id ?? item.id),
          system_name: item.system_name ?? item.name ?? "",
        }))
        .filter(
          (item) =>
            Number.isInteger(item.system_id) &&
            item.system_id > 0
        );

      for (const system of systems.value) {
        if (!lessonsBySystem[system.system_id]) {
          lessonsBySystem[system.system_id] = {
            items: [],
            loading: false,
            loaded: false,
            error: "",
            currentPage: 1,
          };
        }
      }
    } catch (error) {
      systemsError.value = errorText(error);
    } finally {
      loadingSystems.value = false;
    }
  }
  function getPagedLessons(systemId) {
    const state = lessonsBySystem[systemId];
    if (!state) return [];

    const page = state.currentPage || 1;
    const start = (page - 1) * PAGE_SIZE;

    return state.items.slice(start, start + PAGE_SIZE);
  }

  function getSystemTotalPages(systemId) {
    const count = lessonsBySystem[systemId]?.items.length || 0;
    return Math.max(1, Math.ceil(count / PAGE_SIZE));
  }

  function changeSystemPage(systemId, page) {
    const state = lessonsBySystem[systemId];
    if (!state) return;

    const total = getSystemTotalPages(systemId);

    if (page < 1 || page > total) return;

    state.currentPage = page;
  }
  async function loadTemplates() {
    loadingTemplates.value = true
    templatesError.value = ''
    try {
      const { data } = await request.get(API.list)
      existingTemplates.value = readArray(data, ['plans', 'items', 'data'])
    } catch (error) {
      templatesError.value = errorText(error)
    } finally {
      loadingTemplates.value = false
    }
  }

  async function toggleSystem(system) {
    const id = system.system_id
    if (expandedSystemId.value === id) {
      expandedSystemId.value = null
      return
    }
    expandedSystemId.value = id
    await loadSystemLessons(id)
  }

  async function loadSystemLessons(systemId, force = false) {
    const state = lessonsBySystem[systemId]
    if (!state || state.loading || (state.loaded && !force)) return
    state.loading = true
    state.error = ''
    try {
      const items = []
      let page = 1
      let totalPages = 1
      do {
        const { data } = await request.get(API.lessons(systemId), {
          params: { current_page: page, page_size: PAGE_SIZE },
        })
        console.log("课程接口返回:", data);
        const batch = readArray(data, ['lessonlist', 'lessons', 'lesson_list', 'items', 'data'])
        for (const lesson of batch) {
          const id = Number(lesson.lesson_id ?? lesson.id)
          if (!Number.isInteger(id) || id <= 0) continue
          items.push({
            lesson_id: id,
            lesson_name: lesson.lesson_name ?? lesson.name ?? `#${id}`,
            archived: Boolean(lesson.archived || lesson.deleted_at),
          })
        }
        totalPages = Math.max(1, Number(data?.total_pages ?? 1))
        page += 1
      } while (page <= totalPages && page <= 1000)

      state.items = Array.from(
        new Map(
          items.map((item) => [item.lesson_id, item])
        ).values()
      );

      state.currentPage = Math.min(
        state.currentPage || 1,
        Math.max(1, Math.ceil(state.items.length / PAGE_SIZE))
      );

      state.loaded = true;

    } catch (error) {
      state.error = errorText(error)
    } finally {
      state.loading = false
    }
  }

  function isSelected(id) {
    return selectedIds.value.has(id)
  }

  function toggleLesson(lesson, system) {
    if (lesson.archived) return
    const index = selectedLessons.value.findIndex((item) => item.lesson_id === lesson.lesson_id)
    if (index !== -1) {
      selectedLessons.value.splice(index, 1)
    } else {
      selectedLessons.value.push({
        lesson_id: lesson.lesson_id,
        lesson_name: lesson.lesson_name,
        system_name: system.system_name,
      })
    }
    formError.value = ''
    successMessage.value = ''
  }

  function selectedInSystem(systemId) {
    const items = lessonsBySystem[systemId]?.items ?? []
    return items.filter((item) => isSelected(item.lesson_id)).length
  }

  function moveLesson(index, direction) {
    const other = index + direction
    if (other < 0 || other >= selectedLessons.value.length) return
    const result = [...selectedLessons.value]
    ;[result[index], result[other]] = [result[other], result[index]]
    selectedLessons.value = result
  }

  function removeLesson(index) {
    selectedLessons.value.splice(index, 1)
  }

  function clearSelected() {
    selectedLessons.value = []
  }

  async function submit() {
    if (submitting.value) return
    formError.value = ''
    successMessage.value = ''
    if (!form.plan_name.trim()) {
      formError.value = t('presetEnterName')
      return
    }
    if (!form.description.trim()) {
      formError.value = t('presetEnterDescription')
      return
    }
    if (!selectedLessons.value.length) {
      formError.value = t('presetChooseLesson')
      return
    }

    const body = {
      plan_name: form.plan_name.trim(),
      description: form.description.trim(),
      lesson_list: selectedLessons.value.map((item, index) => ({
        lesson_id: item.lesson_id,
        order: index + 1,
      })),
    }

    submitting.value = true
    try {
      await request.post(API.create, body)
      successMessage.value = t('presetCreated')
      form.plan_name = ''
      form.description = ''
      selectedLessons.value = []
      // 新建成功后刷新列表；列表刷新失败不视为创建失败。
      await loadTemplates()
    } catch (error) {
      formError.value = errorText(error)
    } finally {
      submitting.value = false
    }
  }

  const deletingPlanId = ref(null);

  async function deletePresetPlan(plan) {
    if (deletingPlanId.value !== null) return;

    const confirmed = window.confirm(
      `${t("presetDeleteConfirm")}「${plan.plan_name}」?`
    );

    if (!confirmed) return;

    deletingPlanId.value = plan.plan_id;

    try {
      await request.delete(API.delete(plan.plan_id));

      existingTemplates.value = existingTemplates.value.filter(
        (item) => item.plan_id !== plan.plan_id
      );
    } catch (error) {
      templatesError.value = errorText(error);
    } finally {
      deletingPlanId.value = null;
    }
  }

  onMounted(() => {
    void Promise.all([loadSystems(), loadTemplates()])
  })
</script>

<template>
  <main class="preset-page">
    <header class="page-heading">
      <div>
        <h1>{{ t('presetAdminTitle') }}</h1>
        <p>{{ t('presetAdminHint') }}</p>
      </div>
    </header>

    <div class="content-grid">
      <section class="panel create-panel">
        <div class="panel-title">
          <span class="step-tag">01</span>
          <h2>{{ t('presetDetails') }}</h2>
        </div>

        <form id="create-preset-form" @submit.prevent="submit">
          <label class="field">
            <span>{{ t('planName') }} <b aria-hidden="true">*</b></span>
            <input
              v-model.trim="form.plan_name"
              type="text"
              maxlength="100"
              required
              :placeholder="t('presetNamePlaceholder')"
              :disabled="submitting"
            />
          </label>

          <label class="field">
            <span>{{ t('description') }} <b aria-hidden="true">*</b></span>
            <textarea
              v-model.trim="form.description"
              rows="3"
              required
              :placeholder="t('presetDescPlaceholder')"
              :disabled="submitting"
            ></textarea>
          </label>

          <div class="section-head">
            <div class="panel-title">
              <span class="step-tag">02</span>
              <h2>{{ t('presetSelectBySystem') }}</h2>
            </div>
            <p>{{ t('presetSelectHint') }}</p>
          </div>

          <div v-if="loadingSystems" class="inline-state">{{ t('loading') }}</div>
          <div v-else-if="systemsError" class="inline-state error-state">
            <span>{{ systemsError }}</span>
            <button type="button" class="text-action" @click="loadSystems">{{ t('retry') }}</button>
          </div>
          <div v-else-if="!systems.length" class="inline-state">{{ t('presetNoSystems') }}</div>

          <div v-else class="system-list">
            <div v-for="system in systems" :key="system.system_id" class="system-block">
              <button
                type="button"
                class="system-toggle"
                :aria-expanded="expandedSystemId === system.system_id"
                @click="toggleSystem(system)"
              >
                <span class="system-left">
                  <span class="chevron" :class="{ expanded: expandedSystemId === system.system_id }">›</span>
                  <span>{{ system.system_name }}</span>
                </span>
                <span class="count-pill">
                  {{ interpolate('presetSelectedCount', { count: selectedInSystem(system.system_id) }) }}
                </span>
              </button>

              <div v-if="expandedSystemId === system.system_id" class="system-body">
                <div v-if="lessonsBySystem[system.system_id]?.loading" class="inline-state">{{ t('loadingCourses') }}</div>
                <div v-else-if="lessonsBySystem[system.system_id]?.error" class="inline-state error-state">
                  <span>{{ lessonsBySystem[system.system_id].error }}</span>
                  <button type="button" class="text-action" @click="loadSystemLessons(system.system_id, true)">{{ t('retry') }}</button>
                </div>
                <div v-else-if="!lessonsBySystem[system.system_id]?.items.length" class="inline-state">
                  {{ t('presetNoLessons') }}
                </div>
                <label
                  v-for="lesson in getPagedLessons(system.system_id)"
                  :key="lesson.lesson_id"
                  class="lesson-choice"
                  :class="{ active: isSelected(lesson.lesson_id), disabled: lesson.archived }"
                >
                  <input
                    type="checkbox"
                    :checked="isSelected(lesson.lesson_id)"
                    :disabled="lesson.archived || submitting"
                    @change="toggleLesson(lesson, system)"
                  />
                  <span class="lesson-choice-name">{{ lesson.lesson_name }}</span>
                  <span v-if="lesson.archived" class="archived-text">{{ t('archived') }}</span>

                </label>
                <div
                  v-if="getSystemTotalPages(system.system_id) > 1"
                  class="pagination"
                >
                  <button
                    type="button"
                    :disabled="lessonsBySystem[system.system_id].currentPage === 1"
                    @click="changeSystemPage(
                      system.system_id,
                      lessonsBySystem[system.system_id].currentPage - 1
                    )"
                  >
                    {{ t("previousPage") }}
                  </button>

                  <span>
                    {{ lessonsBySystem[system.system_id].currentPage }}
                    /
                    {{ getSystemTotalPages(system.system_id) }}
                  </span>

                  <button
                    type="button"
                    :disabled="
                      lessonsBySystem[system.system_id].currentPage >=
                      getSystemTotalPages(system.system_id)
                    "
                    @click="changeSystemPage(
                      system.system_id,
                      lessonsBySystem[system.system_id].currentPage + 1
                    )"
                  >
                    {{ t("nextPage") }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </form>
      </section>

      <aside class="panel selection-panel">
        <div class="selection-head">
          <div class="panel-title">
            <span class="step-tag">03</span>
            <h2>{{ t('learningOrder') }}</h2>
          </div>
          <span class="count-pill strong">
            {{ interpolate('presetSelectedCount', { count: selectedCount }) }}
          </span>
        </div>
        <p class="muted">{{ t('presetOrderHint') }}</p>

        <div v-if="!selectedLessons.length" class="empty-selection">
          <span class="empty-icon">☷</span>
          <p>{{ t('presetEmptySelection') }}</p>
        </div>
        <ol v-else class="selected-list">
          <li v-for="(item, index) in selectedLessons" :key="item.lesson_id" class="selected-row">
            <span class="order-number">{{ index + 1 }}</span>
            <div class="selected-info">
              <strong>{{ item.lesson_name }}</strong>
              <small>{{ item.system_name }}</small>
            </div>
            <div class="item-actions">
              <button type="button" :aria-label="t('presetMoveUp')" :title="t('presetMoveUp')" :disabled="index === 0 || submitting" @click="moveLesson(index, -1)">↑</button>
              <button type="button" :aria-label="t('presetMoveDown')" :title="t('presetMoveDown')" :disabled="index === selectedLessons.length - 1 || submitting" @click="moveLesson(index, 1)">↓</button>
              <button type="button" class="remove-action" :aria-label="t('delete')" :title="t('delete')" :disabled="submitting" @click="removeLesson(index)">×</button>
            </div>
          </li>
        </ol>

        <button
          v-if="selectedLessons.length"
          type="button"
          class="clear-button"
          :disabled="submitting"
          @click="clearSelected"
        >{{ t('presetClearSelection') }}</button>

        <p v-if="formError" class="feedback error-feedback" role="alert">{{ formError }}</p>
        <p v-if="successMessage" class="feedback success-feedback" role="status">{{ successMessage }}</p>
        <button
          form="create-preset-form"
          type="submit"
          class="submit-button"
          :disabled="submitting || !selectedLessons.length"
        >
          {{ submitting ? t('presetSubmitting') : t('presetSubmit') }}
        </button>
      </aside>
    </div>

    <section class="panel existing-panel">
      <div class="existing-header">
        <div>
          <h2>{{ t('presetExisting') }}</h2>
          <p>{{ t('presetExistingHint') }}</p>
        </div>
        <button type="button" class="secondary-button" :disabled="loadingTemplates" @click="loadTemplates">
          {{ t('retry') }}
        </button>
      </div>
      <div v-if="loadingTemplates" class="inline-state">{{ t('loading') }}</div>
      <div v-else-if="templatesError" class="inline-state error-state">{{ templatesError }}</div>
      <div v-else-if="!existingTemplates.length" class="inline-state">{{ t('presetExistingEmpty') }}</div>

      <div v-else class="template-grid">
        <article v-for="plan in existingTemplates" :key="plan.plan_id" class="template-card">
          <div class="template-card-header">
            <h3>{{ plan.plan_name }}</h3>
            <button
              type="button"
              class="template-delete-button"
              :disabled="deletingPlanId === plan.plan_id"
              @click="deletePresetPlan(plan)"
            >
              {{
                deletingPlanId === plan.plan_id
                  ? t("deleteInProgress")
                  : t("delete")
              }}
            </button>
          </div>
          <p v-if="plan.description" class="template-description">{{ plan.description }}</p>
          <p class="course-count">{{ interpolate('presetCourseCount', { count: plan.lessons?.length || 0 }) }}</p>
          <ol>
            <li v-for="lesson in plan.lessons ?? []" :key="lesson.lesson_id">
              <span>{{ lesson.lesson_name }}</span>
              <span v-if="lesson.archived" class="archived-text">{{ t('archived') }}</span>
            </li>
          </ol>
        </article>
      </div>


    </section>
  </main>
</template>

<style scoped>
  .preset-page { width: 100%; max-width: 1300px; margin: 0 auto; padding: 28px 30px 56px; box-sizing: border-box; color: #18243c; }
  .page-heading { margin-bottom: 22px; }
  .page-heading h1 { margin: 0; font-size: clamp(26px, 2.5vw, 34px); font-weight: 800; line-height: 1.25; }
  .page-heading p { margin: 9px 0 0; font-size: 14px; color: #77839b; }
  .content-grid { display: grid; grid-template-columns: minmax(0, 1.45fr) minmax(320px, 1fr); gap: 20px; align-items: start; }
  .panel { min-width: 0; background: #fff; border: 1px solid #e1e9f6; border-radius: 18px; box-shadow: 0 10px 35px rgba(31, 57, 105, .035); padding: 24px; }
  .panel-title { display: flex; gap: 10px; align-items: center; }
  .panel-title h2 { margin: 0; font-size: 18px; font-weight: 750; }
  .step-tag { display: inline-flex; align-items: center; justify-content: center; height: 27px; min-width: 27px; padding: 0 5px; border-radius: 8px; background: #eaf0ff; color: #3766ef; font-size: 12px; font-weight: 800; }
  .field { display: flex; flex-direction: column; gap: 9px; margin-top: 20px; }
  .field > span { font-weight: 650; font-size: 14px; }
  .field b { color: #e55858; }
  .field input, .field textarea { width: 100%; box-sizing: border-box; border: 1px solid #d9e2f1; border-radius: 10px; padding: 12px 13px; font: inherit; font-size: 14px; color: #18243c; background: #fff; outline: none; resize: vertical; transition: border-color .2s, box-shadow .2s; }
  .field input:focus, .field textarea:focus { border-color: #729aff; box-shadow: 0 0 0 3px rgba(55, 102, 239, .13); }
  .section-head { margin: 27px 0 14px; }
  .section-head p, .muted { color: #77839b; font-size: 13px; line-height: 1.6; }
  .section-head p { margin: 7px 0 0; }
  .system-list { display: grid; gap: 10px; }
  .system-block { overflow: hidden; border: 1px solid #e3eaf6; border-radius: 12px; background: #fff; }
  .system-toggle { display: flex; justify-content: space-between; align-items: center; width: 100%; gap: 14px; padding: 16px; background: #fff; border: 0; cursor: pointer; font: inherit; color: inherit; text-align: left; }
  .system-toggle:hover { background: #f7faff; }
  .system-left { display: flex; align-items: center; gap: 12px; font-size: 14px; font-weight: 700; }
  .chevron { display: inline-block; color: #6d7c93; font-size: 22px; line-height: 1; transition: transform .18s; }
  .chevron.expanded { transform: rotate(90deg); }
  .count-pill { display: inline-flex; flex-shrink: 0; padding: 6px 11px; border-radius: 99px; background: #f0f4fb; font-size: 12px; color: #677993; white-space: nowrap; }
  .count-pill.strong { background: #e9f0ff; color: #3567f4; font-weight: 700; }
  .system-body { background: #fbfcff; padding: 12px; border-top: 1px solid #e8edf7; }
  .lesson-choice { display: flex; align-items: center; gap: 10px; border-radius: 9px; padding: 11px; cursor: pointer; font-size: 14px; }
  .lesson-choice:hover { background: #f0f5ff; }
  .lesson-choice.active { background: #edf3ff; }
  .lesson-choice.disabled { opacity: .55; cursor: not-allowed; }
  .lesson-choice input { accent-color: #386bef; width: 17px; height: 17px; }
  .lesson-choice-name { min-width: 0; overflow-wrap: anywhere; }
  .archived-text { color: #a46630; font-size: 12px; margin-left: auto; }
  .selection-head { display: flex; justify-content: space-between; gap: 10px; align-items: center; }
  .selection-panel .muted { margin: 9px 0 16px; }
  .empty-selection { display: flex; align-items: center; flex-direction: column; padding: 40px 12px; border: 1px dashed #d8e2f2; border-radius: 12px; color: #8997ad; text-align: center; }
  .empty-selection p { font-size: 13px; margin: 7px 0 0; }
  .empty-icon { font-size: 26px; color: #9babce; }
  .selected-list { padding: 0; margin: 0; list-style: none; display: grid; gap: 9px; }
  .selected-row { display: flex; gap: 10px; align-items: center; padding: 11px 10px; border-radius: 11px; border: 1px solid #e4eaf6; }
  .order-number { flex-shrink: 0; width: 29px; height: 29px; border-radius: 8px; background: #eaf1ff; color: #3567ef; display: grid; place-items: center; font-weight: 800; font-size: 13px; }
  .selected-info { min-width: 0; flex: 1; display: grid; gap: 4px; }
  .selected-info strong { font-size: 13px; overflow-wrap: anywhere; }
  .selected-info small { color: #8995a8; }
  .item-actions { display: flex; gap: 3px; }
  .item-actions button { width: 27px; height: 27px; padding: 0; border-radius: 7px; border: 1px solid #e4eaf5; background: #fff; color: #465b7a; cursor: pointer; }
  .item-actions button:hover:not(:disabled) { background: #edf3ff; color: #3766ee; }
  .item-actions button:disabled { opacity: .3; cursor: not-allowed; }
  .item-actions .remove-action { color: #d45858; }
  .clear-button { margin-top: 12px; background: transparent; border: 0; color: #607fac; font-size: 13px; cursor: pointer; padding: 6px 0; }
  .submit-button { display: block; width: 100%; border: 0; border-radius: 10px; margin-top: 18px; padding: 14px; background: #3e6cf2; color: #fff; font-weight: 700; cursor: pointer; box-shadow: 0 7px 18px rgba(62, 108, 242, .2); }
  .submit-button:hover:not(:disabled) { background: #2f5fe5; }
  .submit-button:disabled { opacity: .52; cursor: not-allowed; box-shadow: none; }
  .feedback { padding: 11px; border-radius: 9px; margin: 16px 0 0; font-size: 13px; }
  .error-feedback { background: #fff3f1; border: 1px solid #ffcfc9; color: #b44741; }
  .success-feedback { background: #eef9f1; border: 1px solid #cbe9d5; color: #287347; }
  .inline-state { padding: 16px; color: #8190a8; background: #f8faff; border-radius: 10px; font-size: 13px; }
  .error-state { display: flex; align-items: center; justify-content: space-between; gap: 10px; color: #b44741; }
  .text-action { border: 0; background: transparent; color: #3567ee; cursor: pointer; font-weight: 700; }
  .existing-panel { margin-top: 20px; }
  .existing-header { display: flex; align-items: start; justify-content: space-between; gap: 15px; margin-bottom: 18px; }
  .existing-header h2 { margin: 0; font-size: 18px; }
  .existing-header p { margin: 7px 0 0; color: #8190a8; font-size: 13px; }
  .secondary-button { border: 1px solid #dce6f4; border-radius: 9px; padding: 8px 13px; background: #fff; color: #3567e8; cursor: pointer; }
  .secondary-button:disabled { opacity: .5; cursor: not-allowed; }
  .template-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px; }
  .template-card { padding: 16px; border: 1px solid #e2eaf6; border-radius: 12px; }
  .template-card h3 { margin: 0; font-size: 15px; overflow-wrap: anywhere; }
  .template-description { font-size: 13px; color: #8290a5; line-height: 1.5; }
  .course-count { color: #3766ef; font-size: 12px; font-weight: 700; }
  .template-card ol { margin: 10px 0 0; padding-left: 20px; font-size: 13px; color: #526078; }
  .template-card li { margin: 6px 0; }
  @media (max-width: 960px) { .content-grid { grid-template-columns: 1fr; } }
  @media (max-width: 600px) { .preset-page { padding: 16px 12px 36px; } .panel { padding: 16px; border-radius: 14px; } .selection-head { flex-wrap: wrap; } }

  /* ===== 专业内课程子分页 ===== */

  .pagination {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    margin-top: 18px;
    padding: 16px 12px 4px;
    border-top: 1px solid #e6edf7;
  }

  /* 上一页 / 下一页按钮 */
  .pagination button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 92px;
    height: 36px;
    padding: 0 14px;

    background: #ffffff;
    color: #3b6df6;
    border: 1px solid #d7e3f8;
    border-radius: 9px;

    font-size: 13px;
    font-weight: 600;
    cursor: pointer;

    transition:
      background 0.2s ease,
      border-color 0.2s ease,
      color 0.2s ease,
      box-shadow 0.2s ease;
  }

  /* 鼠标悬停 */
  .pagination button:hover:not(:disabled) {
    background: #edf3ff;
    border-color: #9dbaff;
    color: #2458e8;
    box-shadow: 0 3px 10px rgba(59, 109, 246, 0.08);
  }

  /* 点击效果 */
  .pagination button:active:not(:disabled) {
    background: #dfeaff;
    transform: translateY(1px);
  }

  /* 禁用状态 */
  .pagination button:disabled {
    background: #f5f7fb;
    color: #a3afc2;
    border-color: #e5eaf2;
    cursor: not-allowed;
    box-shadow: none;
  }

  /* 当前页数 */
  .pagination > span {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 70px;
    height: 36px;
    padding: 0 12px;

    background: #eef4ff;
    color: #3768e8;
    border: 1px solid #dce7ff;
    border-radius: 9px;

    font-size: 13px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }

  /* 键盘导航 */
  .pagination button:focus-visible {
    outline: 2px solid #3b6df6;
    outline-offset: 3px;
  }

  /* 手机端 */
  @media (max-width: 600px) {
    .pagination {
      gap: 8px;
      padding: 14px 4px 4px;
    }

    .pagination button {
      min-width: 72px;
      padding: 0 10px;
      font-size: 12px;
    }

    .pagination > span {
      min-width: 58px;
      padding: 0 8px;
    }
  }

  .template-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 14px;
  }

  .template-card-header h3 {
    flex: 1;
    min-width: 0;
    margin: 0;
    overflow-wrap: anywhere;
    font-size: 18px;
    font-weight: 700;
    color: #142b50;
  }

  .template-delete-button {
    flex-shrink: 0;
    padding: 7px 14px;
    border: 1px solid #fecaca;
    border-radius: 8px;
    background: #fff5f5;
    color: #dc2626;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .template-delete-button:hover:not(:disabled) {
    background: #fee2e2;
    border-color: #f87171;
  }

  .template-delete-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

</style>
