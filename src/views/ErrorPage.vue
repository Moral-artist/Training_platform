<script setup>
import { useRoute } from "vue-router";
import { t } from "../i18n";
import PageState from "../components/PageState.vue";
const route = useRoute();
const code = /^HTTP_(400|401|403|404|409|422|429|500|502|503)$/.test(
  String(route.query.code),
)
  ? route.query.code
  : route.meta.error || "unexpectedError";
function retry() {
  window.location.href = "/home";
}
</script>
<template>
  <PageState :error="code" @retry="retry" /><RouterLink
    class="button secondary"
    to="/home"
    >{{ t("home") }}</RouterLink
  >
</template>
