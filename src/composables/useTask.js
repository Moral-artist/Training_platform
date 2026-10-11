import { ref } from "vue";
export function errorKey(error) {
  if (error.message?.startsWith("UI:")) return error.message.slice(3);
  if (error.response) return `HTTP_${error.response.status}`;
  return "networkError";
}
// 页面异步操作共享 loading/错误展示；异常永远不显示后端堆栈或敏感字段。
export function useTask() {
  const busy = ref(false),
    error = ref(""),
    reference = ref("");
  async function run(action, statusKeys = {}) {
    if (busy.value) return;
    busy.value = true;
    error.value = "";
    reference.value = "";
    try {
      return await action();
    } catch (err) {
      error.value = statusKeys[err.response?.status] || errorKey(err);
      reference.value = err.response?.data?.request_id || "";
    } finally {
      busy.value = false;
    }
  }
  return { busy, error, reference, run };
}
