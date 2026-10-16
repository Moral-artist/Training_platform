<script setup>
  import { onMounted, ref } from "vue";
  import { getCatalog, deleteSystem } from "../api/lessons";
  import { t } from "../i18n";
  import request from "../api/request";
  import { useTask } from "../composables/useTask";
  import PageState from "../components/PageState.vue";
  import { notify } from "../stores/notices";

  const systems = ref([]);
  const name = ref("");
  const deletingId = ref(null);

  const { busy, error, run } = useTask();

  // 加载专业列表
  async function load() {
    await run(async () => {
      systems.value = await getCatalog();
    });
  }

  // 新增专业
  async function save() {
    const systemName = name.value.trim();

    if (!systemName) return;

    await run(async () => {
      await request.post(
        "/api/lessons/systemsubmit",
        null,
        {
          params: {
            system_name: systemName
          }
        }
      );

      name.value = "";
      systems.value = await getCatalog();

      notify("saved", "success");
    });
  }

  // 删除专业
  async function removeSystem(system) {
    const confirmed = window.confirm(
      `确定删除专业「${system.system_name}」吗？`
    );

    if (!confirmed) return;

    deletingId.value = system.system_id;

    try {
      await run(async () => {
        await deleteSystem(system.system_id);

        // 删除成功后刷新列表
        systems.value = await getCatalog();

        notify("deleted", "success");
      });
    } finally {
      deletingId.value = null;
    }
  }

  onMounted(load);
</script>

<template>
  <section class="card">

    <!-- 专业列表 -->
    <div class="tabs">
      <div
        v-for="s in systems"
        :key="s.system_id"
        class="system-tag"
      >
        <span class="system-name">
          {{ s.system_name }}
        </span>

        <button
          type="button"
          class="delete-btn"
          :disabled="busy"
          :title="`删除 ${s.system_name}`"
          @click="removeSystem(s)"
        >
          <span v-if="deletingId === s.system_id">
            ...
          </span>
          <span v-else>
            ×
          </span>
        </button>
      </div>

      <p v-if="!systems.length && !busy" class="empty">
        暂无专业
      </p>
    </div>

    <!-- 新增专业 -->
    <form class="form" @submit.prevent="save">
      <label class="field">
        <span>{{ t("systemName") }}</span>

        <input
          v-model="name"
          required
          maxlength="200"
          :placeholder="t('systemNamePlaceholder')"
        />
      </label>

      <button :disabled="busy || !name.trim()">
        {{ t("save") }}
      </button>
    </form>

    <!-- 状态展示 -->
    <PageState
      :error="error"
      @retry="load"
    />

  </section>
</template>

<style scoped>
  .tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 24px;
  }

  .system-tag {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    padding: 8px 10px 8px 16px;
    border: 1px solid #dbe3ee;
    border-radius: 10px;
    background: #f8fafc;
    transition: all 0.2s ease;
  }

  .system-tag:hover {
    border-color: #94a3b8;
    background: #f1f5f9;
  }

  .system-name {
    font-size: 14px;
    font-weight: 500;
    color: #334155;
  }

  .delete-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    padding: 0;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: #94a3b8;
    font-size: 20px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .delete-btn:hover:not(:disabled) {
    background: #fee2e2;
    color: #dc2626;
  }

  .delete-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .empty {
    color: #94a3b8;
    font-size: 14px;
  }
</style>