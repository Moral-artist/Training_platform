<script setup>
  import { onMounted, ref, watch } from "vue";
  import request from "../api/request";
  import { t } from "../i18n";
  import { useTask } from "../composables/useTask";
  import PageState from "../components/PageState.vue";
  import { notify } from "../stores/notices";

  const rows = ref([]);
  const deleting = ref(null);

  const { busy, error, run } = useTask();

  const PAGE_SIZE = 10;

  const searchKeyword = ref("");
  const currentPage = ref(1);
  const totalPages = ref(0);
  const totalLessons = ref(0);

  let searchTimer = null;
  let requestVersion = 0;

  async function load() {
    const version = ++requestVersion;

    await run(async () => {
      const { data } = await request.get(
        "/api/lessons/manage_lessons",
        {
          params: {
            current_page: currentPage.value,
            page_size: PAGE_SIZE,
            keyword: searchKeyword.value.trim(),
          },
        }
      );

      // 忽略旧请求，避免搜索过程中旧结果覆盖新结果
      if (version !== requestVersion) return;

      rows.value = data.lessonlist ?? [];
      totalPages.value = data.total_pages ?? 0;
      totalLessons.value = data.total_lessons ?? 0;
    });
  }

  function changePage(page) {
    if (page < 1 || page > totalPages.value) return;

    currentPage.value = page;
    load();
  }

  // 搜索输入停止 350ms 后才发出请求
  watch(searchKeyword, () => {
    currentPage.value = 1;
    requestVersion++;

    if (searchTimer) clearTimeout(searchTimer);

    searchTimer = setTimeout(() => {
      load();
    }, 350);
  });

  async function remove() {
    if (!deleting.value || busy.value) return;

    const lesson = deleting.value;

    try {
      await run(async () => {
        await request.delete(
          `/api/lessons/${lesson.lesson_id}`,
          {
            params: {
              revision: lesson.revision,
            },
          }
        );
      });

      // 删除成功后关闭确认弹窗
      deleting.value = null;

      notify("saved", "success");

      // 如果当前页只有一条课程，并且不是第一页
      // 删除后自动返回上一页
      if (rows.value.length === 1 && currentPage.value > 1) {
        currentPage.value -= 1;
      }

      // 重新请求后端，刷新列表和分页
      await load();

    } catch (err) {
      console.error("删除课程失败:", err);
    }
  }

  onMounted(load);
</script>


<template>
  <Teleport to="body">
    <div
      v-if="busy || error"
      class="page-state-overlay"
    >
      <PageState
        :busy="busy"
        :error="error"
        @retry="load"
      />
    </div>
  </Teleport>

  <section class="lesson-manage card">

    <!-- 页面顶部 -->
    <header class="manage-header">
      <div>
        <h2>{{ t("manageLessons") }}</h2>
        <p class="manage-subtitle">
          {{ t("searchLessonsPlaceholder") }}
        </p>
      </div>

      <span class="total-badge">
        {{ totalLessons }} {{ t("courseUnit") }}
      </span>
    </header>

    <!-- 搜索栏 -->
    <div class="manage-toolbar">
      <div class="search-field">
        <span class="search-symbol">⌕</span>

        <input
          v-model="searchKeyword"
          type="search"
          :placeholder="t('searchLessonsPlaceholder')"
        />

        <button
          v-if="searchKeyword"
          type="button"
          class="search-clear"
          :aria-label="t('clearSearch')"
          @click="searchKeyword = ''"
        >
          ×
        </button>
      </div>
    </div>

    <!-- 表格 -->
    <div class="manage-table-scroll">
      <table class="manage-table">
        <thead>
          <tr>
            <th>{{ t("lessonName") }}</th>
            <th class="operations-heading">
              {{ t("editLesson") }}
            </th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="l in rows" :key="l.lesson_id">
            <td>
              <div class="lesson-cell">
                <span class="lesson-icon">▤</span>

                <div class="lesson-information">
                  <strong>{{ l.lesson_name }}</strong>
                  <small>ID: {{ l.lesson_id }}</small>
                </div>
              </div>
            </td>

            <td>
              <div class="row-actions">
                <RouterLink
                  class="action-button edit-button"
                  :to="`/lessons/${l.lesson_id}/edit`"
                >
                  <span>✎</span>
                  {{ t("editLesson") }}
                </RouterLink>

                <button
                  type="button"
                  class="action-button delete-button"
                  :disabled="busy"
                  @click="deleting = l"
                >
                  <span>×</span>
                  {{ t("delete") }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 空状态 -->
    <div
      v-if="!busy && !error && !rows.length"
      class="manage-empty"
    >
      <span class="empty-symbol">⌕</span>
      <p>
        {{
          searchKeyword.trim()
            ? t("noSearchResults")
            : t("empty")
        }}
      </p>
    </div>

    <!-- 分页 -->
    <footer class="manage-footer">
      <span class="footer-count">
        {{ totalLessons }} {{ t("courseUnit") }}
      </span>

      <div v-if="totalPages > 1" class="manage-pagination">
        <button
          type="button"
          :disabled="currentPage <= 1 || busy"
          @click="changePage(currentPage - 1)"
        >
          ‹
        </button>

        <span class="current-page">
          {{ currentPage }} / {{ totalPages }}
        </span>

        <button
          type="button"
          :disabled="currentPage >= totalPages || busy"
          @click="changePage(currentPage + 1)"
        >
          ›
        </button>
      </div>
    </footer>

    <!-- 删除确认 -->
    <div
      v-if="deleting"
      class="delete-overlay"
      role="presentation"
      @click.self="deleting = null"
    >
      <div
        class="delete-dialog"
        role="alertdialog"
        aria-modal="true"
        :aria-label="t('deleteConfirm')"
      >
        <div class="dialog-icon">!</div>
        <h3>{{ t("deleteConfirm") }}</h3>
        <p class="dialog-lesson-name">
          {{ deleting.lesson_name }}
        </p>

        <div class="dialog-actions">
          <button
            type="button"
            class="dialog-cancel"
            :disabled="busy"
            @click="deleting = null"
          >
            {{ t("cancel") }}
          </button>

          <button
            type="button"
            class="dialog-delete"
            :disabled="busy"
            @click="remove"
          >
            {{ t("confirm") }}
          </button>
        </div>
      </div>
    </div>

  </section>
</template>

<style scoped>

  /* 全屏加载和错误遮罩 */
  .page-state-overlay {
    position: fixed;
    inset: 0;
    z-index: 9999;

    display: flex;
    align-items: center;
    justify-content: center;

    width: 100%;
    min-height: 100dvh;
    padding: 20px;
    box-sizing: border-box;

    background: rgba(245, 248, 255, 0.78);
    backdrop-filter: blur(5px);
  }

  /* 遮罩内部的 PageState 容器 */
  .page-state-overlay :deep(> *) {
    width: 100%;
    max-width: 420px;
  }

  /* ===== 页面主容器 ===== */
  .lesson-manage {
    padding: 0;
    overflow: hidden;
    border: 1px solid #e3eaf5;
    border-radius: 16px;
    background: #ffffff;
    box-shadow: 0 4px 20px rgba(30, 64, 120, 0.035);
  }

  /* ===== 标题区域 ===== */
  .manage-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    padding: 24px 26px 16px;
  }

  .manage-header h2 {
    margin: 0;
    color: #172c4d;
    font-size: 21px;
    font-weight: 700;
    letter-spacing: -0.3px;
  }

  .manage-subtitle {
    margin: 7px 0 0;
    font-size: 13px;
    color: #91a0b5;
  }

  .total-badge {
    display: inline-flex;
    align-items: center;
    flex-shrink: 0;
    padding: 7px 13px;
    border-radius: 20px;
    background: #edf3ff;
    color: #3766ef;
    font-size: 12px;
    font-weight: 700;
  }

  /* ===== 搜索栏 ===== */
  .manage-toolbar {
    padding: 5px 26px 22px;
  }

  .search-field {
    position: relative;
    width: 100%;
    max-width: 440px;
  }

  .search-field input {
    width: 100%;
    height: 44px;
    box-sizing: border-box;
    padding: 0 44px;
    border: 1px solid #dce5f2;
    border-radius: 10px;
    background: #f9fbff;
    color: #253857;
    font-size: 14px;
    outline: none;
    transition: 0.2s ease;
  }

  .search-field input:focus {
    background: #ffffff;
    border-color: #5485f7;
    box-shadow: 0 0 0 3px rgba(59, 109, 246, 0.09);
  }

  .search-field input::placeholder {
    color: #a1aec0;
  }

  .search-symbol {
    position: absolute;
    left: 15px;
    top: 50%;
    transform: translateY(-50%);
    color: #8fa2bc;
    font-size: 26px;
    line-height: 1;
    pointer-events: none;
  }

  .search-clear {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    padding: 4px;
    border: none;
    background: transparent;
    color: #99a6b9;
    font-size: 21px;
    cursor: pointer;
  }

  /* ===== 表格 ===== */
  .manage-table-scroll {
    width: 100%;
    overflow-x: auto;
  }

  .manage-table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
  }

  .manage-table thead {
    background: #f7f9fd;
  }

  .manage-table th {
    padding: 15px 26px;
    text-align: left;
    color: #8391a7;
    font-size: 12px;
    font-weight: 600;
    border-top: 1px solid #eef2f8;
    border-bottom: 1px solid #eef2f8;
  }

  .manage-table th:first-child {
    width: 65%;
  }

  .manage-table th:last-child {
    width: 35%;
  }

  .manage-table td {
    padding: 17px 26px;
    border-bottom: 1px solid #f0f3f9;
    vertical-align: middle;
  }

  .manage-table tbody tr {
    transition: background 0.2s ease;
  }

  .manage-table tbody tr:hover {
    background: #f8faff;
  }

  /* ===== 课程名称 ===== */
  .lesson-cell {
    display: flex;
    align-items: center;
    gap: 13px;
    min-width: 0;
  }

  .lesson-icon {
    width: 38px;
    height: 38px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    background: #edf3ff;
    color: #4676ed;
    font-size: 20px;
  }

  .lesson-information {
    display: flex;
    flex-direction: column;
    gap: 5px;
    min-width: 0;
  }

  .lesson-information strong {
    color: #253858;
    font-size: 14px;
    font-weight: 600;
    overflow-wrap: anywhere;
  }

  .lesson-information small {
    color: #a0aec0;
    font-size: 11px;
  }

  /* ===== 操作按钮 ===== */
  .row-actions {
    display: flex;
    justify-content: flex-start;
    align-items: center;
    flex-wrap: wrap;
    gap: 9px;
  }

  .action-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    min-height: 35px;
    padding: 0 13px;
    border: 1px solid transparent;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
    text-decoration: none;
    white-space: nowrap;
    cursor: pointer;
    transition: 0.2s ease;
  }

  .edit-button {
    color: #3766ef;
    background: #edf3ff;
    border-color: #dce7ff;
  }

  .edit-button:hover {
    background: #e0eaff;
    border-color: #b9cfff;
  }

  .delete-button {
    color: #e05252;
    background: #fff5f5;
    border-color: #ffe0e0;
  }

  .delete-button:hover:not(:disabled) {
    color: #cf3030;
    background: #ffe8e8;
    border-color: #ffc5c5;
  }

  .action-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* ===== 空状态 ===== */
  .manage-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    padding: 52px 20px;
    color: #91a0b4;
  }

  .empty-symbol {
    font-size: 44px;
    color: #c3cfdf;
  }

  .manage-empty p {
    margin: 0;
    font-size: 14px;
  }

  /* ===== 底部分页 ===== */
  .manage-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    min-height: 72px;
    padding: 14px 26px;
  }

  .footer-count {
    font-size: 12px;
    color: #91a0b4;
  }

  .manage-pagination {
    display: flex;
    align-items: center;
    gap: 9px;
  }

  .manage-pagination button {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background: #ffffff;
    color: #4668b0;
    border: 1px solid #dce5f2;
    border-radius: 9px;
    font-size: 22px;
    cursor: pointer;
    transition: 0.2s ease;
  }

  .manage-pagination button:hover:not(:disabled) {
    background: #edf3ff;
    border-color: #9dbaff;
  }

  .manage-pagination button:disabled {
    color: #c3ccda;
    background: #f7f9fc;
    cursor: not-allowed;
  }

  .current-page {
    min-width: 58px;
    text-align: center;
    color: #526580;
    font-size: 13px;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }

  /* ===== 删除确认遮罩 ===== */
  .delete-overlay {
    position: fixed;
    inset: 0;
    z-index: 3000;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
    background: rgba(19, 33, 57, 0.42);
    backdrop-filter: blur(3px);
  }

  .delete-dialog {
    width: 100%;
    max-width: 420px;
    padding: 30px;
    border: 1px solid #e9eef6;
    border-radius: 16px;
    background: #ffffff;
    box-shadow: 0 25px 70px rgba(16, 32, 62, 0.18);
    text-align: center;
  }

  .dialog-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    margin: 0 auto 16px;
    border-radius: 50%;
    background: #fff0f0;
    color: #e05252;
    font-size: 24px;
    font-weight: 700;
  }

  .delete-dialog h3 {
    margin: 0 0 12px;
    font-size: 19px;
    color: #213553;
  }

  .dialog-lesson-name {
    margin: 0;
    color: #71839d;
    font-size: 14px;
    overflow-wrap: anywhere;
  }

  .dialog-actions {
    display: flex;
    gap: 12px;
    margin-top: 28px;
  }

  .dialog-actions button {
    flex: 1;
    height: 41px;
    border-radius: 9px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
  }

  .dialog-cancel {
    background: #ffffff;
    color: #5e708c;
    border: 1px solid #dce5f2;
  }

  .dialog-delete {
    background: #e05252;
    color: #ffffff;
    border: 1px solid #e05252;
  }

  .dialog-delete:hover:not(:disabled) {
    background: #c83e3e;
  }

  .dialog-actions button:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }

  /* ===== 响应式 ===== */
  @media (max-width: 640px) {
    .manage-header {
      padding: 20px 16px 14px;
    }

    .manage-header h2 {
      font-size: 18px;
    }

    .manage-toolbar {
      padding: 4px 16px 16px;
    }

    .search-field {
      max-width: 100%;
    }

    .manage-table {
      min-width: 500px;
    }

    .manage-table th,
    .manage-table td {
      padding: 14px 16px;
    }

    .manage-footer {
      padding: 14px 16px;
    }

    .delete-dialog {
      padding: 24px 18px;
    }
  }

</style>

