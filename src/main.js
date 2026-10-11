import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { notify } from "./stores/notices";
import "./style.css";
const app = createApp(App);
app.config.errorHandler = () => notify("unexpectedError", "error");
window.addEventListener(
  "invalid",
  (event) => {
    event.preventDefault();
    notify("HTTP_422");
  },
  true,
);
window.addEventListener("unhandledrejection", () =>
  notify("unexpectedError", "error"),
);
app.use(router).mount("#app");
