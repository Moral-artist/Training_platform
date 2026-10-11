<script setup>
import { onMounted, ref } from "vue";
import request from "../api/request";
import { t } from "../i18n";
import { useTask } from "../composables/useTask";
import { notify } from "../stores/notices";
import PageState from "../components/PageState.vue";
const accounts = ref([]),
  search = ref(""),
  page = ref(1),
  total = ref(0),
  { busy, error, run } = useTask();
async function load() {
  await run(async () => {
    const { data } = await request.get("/api/admin/accounts", {
      params: { search: search.value, page: page.value },
    });
    accounts.value = data.accounts;
    total.value = data.total;
  });
}
async function save(a) {
  await run(async () => {
    await request.put(`/api/admin/accounts/${a.account_id}`, {
      role: a.role,
      is_active: a.is_active,
    });
    notify("saved", "success");
  });
}
onMounted(load);
</script>
<template>
  <section class="card">
    <p>{{ t("accountHint") }}</p>
    <form
      class="actions"
      @submit.prevent="
        page = 1;
        load();
      "
    >
      <input
        v-model="search"
        class="compact"
        :aria-label="t('search')"
      /><button :disabled="busy">{{ t("search") }}</button>
    </form>
    <PageState :busy="busy" :error="error" @retry="load" />
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>{{ t("userName") }}</th>
            <th>{{ t("role") }}</th>
            <th>{{ t("active") }}</th>
            <th>{{ t("save") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in accounts" :key="a.account_id">
            <td>
              {{ a.user_name }}<br /><small>{{ a.email }}</small>
            </td>
            <td>
              <select v-model="a.role" :aria-label="t('role')">
                <option
                  v-for="role in ['user', 'manager', 'administer']"
                  :key="role"
                  :value="role"
                >
                  {{ t(role) }}
                </option>
              </select>
            </td>
            <td>
              <input
                v-model="a.is_active"
                type="checkbox"
                :aria-label="t('active')"
              />
            </td>
            <td>
              <button :disabled="busy" @click="save(a)">{{ t("save") }}</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="actions">
      <button
        class="secondary"
        :disabled="page <= 1 || busy"
        @click="
          page--;
          load();
        "
      >
        ←</button
      ><span>{{ page }} / {{ Math.max(1, Math.ceil(total / 50)) }}</span
      ><button
        class="secondary"
        :disabled="page * 50 >= total || busy"
        @click="
          page++;
          load();
        "
      >
        →
      </button>
    </div>
  </section>
</template>
