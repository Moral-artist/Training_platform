<script setup>
import { computed, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import request from "../api/request";
import { clearUser, loadUser } from "../stores/auth";
import { t } from "../i18n";
import { useTask } from "../composables/useTask";
import { notify } from "../stores/notices";
import PageState from "../components/PageState.vue";
const route = useRoute(),
  router = useRouter(),
  kind = computed(() => route.meta.authKind);
const form = reactive({
  user_name: "",
  email: "",
  password: "",
  new_password: "",
  character: "operator",
  code: "",
});
let cachedChallenge = null;
try {
  cachedChallenge = JSON.parse(
    sessionStorage.getItem("training-challenge") || "null",
  );
} catch {
  sessionStorage.removeItem("training-challenge");
}
const challenge = ref(cachedChallenge);
const { busy, error, reference, run } = useTask();
const verifying = computed(() => kind.value === "verifyEmail");
const statusKeys = {
  verifyEmail: { 401: "verifyInvalid" },
  login: { 400: "loginInvalid", 401: "loginInvalid" },
  register: { 409: "emailTaken" },
  forgotPassword: { 409: "emailNotFound" },
  resetPassword: { 409: "emailNotFound" },
};
async function submit() {
  await run(async () => {
    if (verifying.value) {
      if (!challenge.value) throw new Error("UI:challengeMissing");
      const path =
        challenge.value.purpose === "reset"
          ? "verify_reset"
          : "verify_register";
      await request.post(`/api/auth/${path}`, null, {
        params: { challenge_id: challenge.value.id, code: form.code },
      });
      sessionStorage.removeItem("training-challenge");
      clearUser();
      notify("saved", "success");
      await router.replace("/login");
      return;
    }
    if (kind.value === "login") {
      await request.post("/api/auth/login", {
        email: form.email,
        password: form.password,
      });
      await loadUser(true);
      // 仅站内路径可用作登录后跳转，防止开放重定向。
      const next = String(route.query.redirect || "/home");
      await router.replace(
        next.startsWith("/") && !next.startsWith("//") ? next : "/home",
      );
      return;
    }
    const reset = ["forgotPassword", "resetPassword"].includes(kind.value);
    const body = reset
      ? { email: form.email, new_password: form.new_password }
      : {
          user_name: form.user_name.trim(),
          email: form.email,
          password: form.password,
          character: form.character,
        };
    const { data } = await request.post(
      `/api/auth/${reset ? "pre_reset" : "pre_register"}`,
      body,
    );
    // 持久化只含 challenge ID/用途；密码从不写入存储。
    sessionStorage.setItem(
      "training-challenge",
      JSON.stringify({
        id: data.challenge_id,
        purpose: reset ? "reset" : "register",
      }),
    );
    await router.push("/verify_email");
  }, statusKeys[kind.value] || {});
}
</script>
<template>
  <form class="card form narrow" @submit.prevent="submit">
    <p v-if="verifying">{{ t("verifyHint") }}</p>
    <template v-if="!verifying">
      <label v-if="kind === 'register'" class="field"
        ><span>{{ t("userName") }}</span
        ><input
          v-model="form.user_name"
          required
          maxlength="100"
          autocomplete="name"
      /></label>
      <label class="field"
        ><span>{{ t("email") }}</span
        ><input v-model="form.email" type="email" required autocomplete="email"
      /></label>
      <label v-if="['login', 'register'].includes(kind)" class="field"
        ><span>{{ t("password") }}</span
        ><input
          v-model="form.password"
          type="password"
          required
          :minlength="kind === 'register' ? 8 : 1"
          maxlength="128"
          :autocomplete="
            kind === 'login' ? 'current-password' : 'new-password'
          "
      /></label>
      <label v-else class="field"
        ><span>{{ t("newPassword") }}</span
        ><input
          v-model="form.new_password"
          type="password"
          required
          minlength="8"
          maxlength="128"
          autocomplete="new-password"
      /></label>
      <label v-if="kind === 'register'" class="field"
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
      <p v-if="kind !== 'login'" class="hint">{{ t("passwordHint") }}</p>
    </template>
    <label v-else class="field"
      ><span>{{ t("code") }}</span
      ><input
        v-model="form.code"
        inputmode="numeric"
        pattern="[0-9]{6}"
        minlength="6"
        maxlength="6"
        required
        autocomplete="one-time-code"
    /></label>
    <PageState :error="error" :reference="reference" @retry="submit" />
    <button :disabled="busy || (verifying && !challenge)">
      {{ busy ? t("loading") : t(verifying ? "verifyEmail" : kind) }}
    </button>
    <div class="auth-links">
      <RouterLink to="/login">{{ t("login") }}</RouterLink
      ><RouterLink to="/pre_register">{{ t("register") }}</RouterLink
      ><RouterLink to="/forgot_password">{{ t("forgotPassword") }}</RouterLink>
    </div>
  </form>
</template>
