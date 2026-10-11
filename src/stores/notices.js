import { reactive } from "vue";
export const notice = reactive({ key: "", type: "warning" });
export function notify(key, type = "warning") {
  notice.key = key;
  notice.type = type;
}
