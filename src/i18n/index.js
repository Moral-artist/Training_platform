import { ref } from "vue";
import messages from "./messages.json";
const saved = localStorage.getItem("training-language");
export const locale = ref(["zh", "en", "th"].includes(saved) ? saved : "zh");
export function t(key) {
  return messages[locale.value][key] || messages.zh[key] || key;
}
export function setLocale(value) {
  if (!messages[value]) return;
  locale.value = value;
  localStorage.setItem("training-language", value);
  document.documentElement.lang = { zh: "zh-CN", en: "en", th: "th" }[value];
}
setLocale(locale.value);
