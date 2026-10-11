<script setup>
import { t } from "../i18n";
defineProps({ busy: Boolean, error: String, reference: String });
defineEmits(["retry"]);
</script>
<template>
  <div v-if="busy" class="state" role="status">
    <span class="spinner"></span>{{ t("loading") }}
  </div>
  <section v-else-if="error" class="state warning" role="alert">
    <h2>{{ t("errorTitle") }}</h2>
    <p>{{ t(error) }}</p>
    <small v-if="reference">{{ t("requestReference") }}: {{ reference }}</small>
    <button type="button" @click="$emit('retry')">{{ t("retry") }}</button>
  </section>
</template>
