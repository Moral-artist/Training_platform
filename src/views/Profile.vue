<script setup>
import { reactive } from "vue";
import { auth, loadUser } from "../stores/auth";
import { t } from "../i18n";
import request from "../api/request";
import { useTask } from "../composables/useTask";
import { notify } from "../stores/notices";
import PageState from "../components/PageState.vue";
const form = reactive({
  username: auth.user?.user_name || "",
  character: auth.user?.character || "operator",
});
const { busy, error, run } = useTask();
async function save() {
  await run(async () => {
    await request.post("/api/user/edit_profile", form);
    await loadUser(true);
    notify("saved", "success");
  });
}
</script>
<template>
  <form class="card form" @submit.prevent="save">
    <p>{{ t("profileHint") }}</p>
    <p>{{ t("email") }}: {{ auth.user?.email }}</p>
    <p>{{ t("role") }}: {{ t(auth.user?.role) }}</p>
    <label class="field"
      ><span>{{ t("userName") }}</span
      ><input v-model="form.username" required maxlength="100"
    /></label>
    <label class="field"
      ><span>{{ t("character") }}</span
      ><select v-model="form.character">
        <option
          v-for="c in ['engineer', 'operator', 'shiftleader']"
          :key="c"
          :value="c"
        >
          {{ t(c) }}
        </option>
      </select></label
    >
    <PageState :error="error" @retry="save" /><button :disabled="busy">
      {{ busy ? t("loading") : t("save") }}
    </button>
  </form>
</template>
