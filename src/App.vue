<script setup>
import { onErrorCaptured, ref, watch } from "vue";
import { useRoute } from "vue-router";
import AppLayout from "./components/AppLayout.vue";
import PageState from "./components/PageState.vue";
const route = useRoute(),
  crashed = ref(false);
onErrorCaptured(() => {
  crashed.value = true;
  return false;
});
watch(
  () => route.fullPath,
  () => {
    crashed.value = false;
  },
);
function reload() {
  window.location.reload();
}
</script>
<template>
  <AppLayout
    ><PageState
      v-if="crashed"
      error="unexpectedError"
      @retry="reload" /><RouterView v-else :key="route.fullPath"
  /></AppLayout>
</template>
