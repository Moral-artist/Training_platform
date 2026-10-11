<script setup>
import { computed, ref, watchEffect } from "vue";
import { useRoute, useRouter } from "vue-router";
import { auth, clearUser, isAdmin, canUpload } from "../stores/auth";
import { locale, setLocale, t } from "../i18n";
import { notice, notify } from "../stores/notices";
import request from "../api/request";
const route = useRoute(),
  router = useRouter(),
  leaving = ref(false);
const links = [
  ["home", "/home", "all"],
  ["dashboard", "/dashboard", "user"],
  ["profile", "/profile", "user"],
  ["plans", "/createplan", "user"],
  ["exams", "/exams", "user"],
  ["createLesson", "/lessons/create", "manager"],
  ["manageLessons", "/lessons/manage", "user"],
  ["systems", "/systems", "admin"],
  ["access", "/lessons/accessmanage", "admin"],
  ["accounts", "/accounts", "admin"],
];
function enabled(level) {
  return (
    level === "all" ||
    (level === "admin"
      ? isAdmin()
      : level === "manager"
        ? canUpload()
        : !!auth.user)
  );
}
const title = computed(() => t(route.meta.title || "brand"));
watchEffect(() => {
  document.title = `${title.value} · ${t("brand")}`;
});
async function logout() {
  leaving.value = true;
  try {
    await request.post("/api/auth/logout");
    clearUser();
    notice.key = "";
    await router.replace("/home");
    window.dispatchEvent(new Event("training-logout"));
  } catch (error) {
    if (error.response?.status === 401) {
      clearUser();
      await router.replace("/home");
    } else notify(`HTTP_${error.response?.status || 500}`);
  } finally {
    leaving.value = false;
  }
}
</script>
<template>
  <div class="app-shell">
    <header class="site-header">
      <RouterLink class="brand" to="/home"
        ><span class="brand-mark">T</span
        ><span
          ><strong>{{ t("brand") }}</strong
          ><small>Training System</small></span
        ></RouterLink
      >
      <div class="header-actions">
        <span v-if="auth.user" class="user-badge">{{
          auth.user.user_name
        }}</span>
        <label class="language-control"
          ><span>{{ t("language") }}</span
          ><select :value="locale" @change="setLocale($event.target.value)">
            <option value="zh">中文</option>
            <option value="en">English</option>
            <option value="th">ไทย</option>
          </select></label
        >
        <RouterLink v-if="!auth.user" class="button secondary" to="/login">{{
          t("login")
        }}</RouterLink>
        <RouterLink v-if="!auth.user" class="button" to="/pre_register">{{
          t("register")
        }}</RouterLink>
        <button
          class="secondary"
          :disabled="!auth.user || leaving"
          :title="auth.user ? t('logout') : t('loggedOut')"
          @click="logout"
        >
          {{ t("logout") }}
        </button>
      </div>
    </header>
    <div class="shell-body" :class="{ standalone: route.meta.noSidebar }">
      <!-- 所有带侧栏的路由使用同一个组件、同一组菜单。角色无权时禁用入口。 -->
      <aside v-if="!route.meta.noSidebar" class="sidebar">
        <nav :aria-label="t('brand')">
          <template v-for="[key, path, level] in links" :key="key"
            ><RouterLink v-if="enabled(level)" :to="path">{{
              t(key)
            }}</RouterLink
            >
          </template
          >
        </nav>
      </aside>
      <main class="content">
        <div class="page-heading">
          <span class="eyebrow">TRAINING SYSTEM</span>
          <h1>{{ title }}</h1>
        </div>
        <div v-if="notice.key" class="notice" :class="notice.type" role="alert">
          <span>{{ t(notice.key) }}</span
          ><button
            class="text-button"
            :aria-label="t('cancel')"
            @click="notice.key = ''"
          >
            ×
          </button>
        </div>
        <slot />
      </main>
    </div>
  </div>
</template>
