import { Window } from "happy-dom";
import { fileURLToPath } from "node:url";
import fs from "node:fs/promises";
const window = new Window({ url: "http://localhost:15173/home" });
for (const key of [
  "document",
  "navigator",
  "location",
  "history",
  "localStorage",
  "sessionStorage",
  "HTMLElement",
  "SVGElement",
  "Element",
  "Node",
  "Event",
  "CustomEvent",
  "MutationObserver",
])
  Object.defineProperty(globalThis, key, {
    value: window[key],
    configurable: true,
    writable: true,
  });
globalThis.window = window;
document.body.innerHTML = '<div id="app"></div>';
const { createServer } = await import("vite");
const { parse, compileScript } = await import("@vue/compiler-sfc");
const server = await createServer({
  configFile: false,
  plugins: [
    {
      name: "client-test-sfc",
      transform(code, id) {
        if (id.endsWith(".vue")) {
          const { descriptor } = parse(code, { filename: id });
          return {
            code: compileScript(descriptor, {
              id: "qa-component",
              inlineTemplate: true,
            }).content,
            map: null,
          };
        }
      },
    },
  ],
  root: fileURLToPath(new URL("..", import.meta.url)),
  server: { middlewareMode: true },
  appType: "custom",
});
const catalog = [
  {
    system_id: 1,
    system_name: "QA Electrical",
    lessons: [
      {
        lesson_id: 1,
        lesson_name: "QA Power training",
        video_status: "ready",
        can_access: false,
      },
    ],
  },
  { system_id: 5, system_name: "QA New specialty", lessons: [] },
];
let logged = false;
let examReads = 0;
const user = {
  account_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  user_name: "QA Admin",
  email: "qa@example.com",
  role: "administer",
  character: "engineer",
  csrf_token: "mock-csrf",
};
const { default: request } = await server.ssrLoadModule("/src/api/request.js");
request.defaults.adapter = async (config) => {
  let data = [];
  const reject = (status) => {
    throw Object.assign(new Error("mock"), { response: { status }, config });
  };
  if (config.url === "/api/user/user_info") {
    if (!logged) reject(401);
    data = { ...user };
  } else if (config.url === "/api/auth/login") {
    logged = true;
    data = { csrf_token: "mock-csrf" };
  } else if (config.url === "/api/auth/logout") {
    logged = false;
    data = {};
  } else if (config.url === "/api/lessons/catalog")
    data = catalog.map((s) => ({
      ...s,
      lessons: s.lessons.map((l) => ({ ...l, can_access: logged })),
    }));
  else if (config.url.endsWith("/detail"))
    data = {
      lesson_id: 1,
      lesson_name: "QA Power training",
      description: "Description",
      system_id: 1,
      video_status: "ready",
      can_manage: true,
      video_asset_id: "11111111-1111-4111-8111-111111111111",
      revision: 1,
    };
  else if (config.url === "/api/admin/accounts")
    data = { accounts: [user], total: 1, page: 1 };
  else if (config.url === "/api/exams/getExams") {
    examReads++;
    reject(404);
  }
  return { data, status: 200, statusText: "OK", headers: {}, config };
};
// SSR loader compiles SFCs. Import the same Vue instance as compiled components.
const { createApp, nextTick } = await import("vue");
const { default: App } = await server.ssrLoadModule("/src/App.vue");
const { default: router } = await server.ssrLoadModule("/src/router/index.js");
const app = createApp(App);
const errors = [];
app.config.errorHandler = (e) => errors.push(String(e));
app.use(router);
app.mount("#app");
await router.isReady();
const settle = async () => {
  for (let i = 0; i < 20; i++) {
    await new Promise((r) => setTimeout(r, 10));
    await nextTick();
  }
};
await settle();
const assert = (condition, message) => {
  if (!condition) throw new Error(message);
};
assert(
  document.body.textContent.includes("QA New specialty"),
  "all systems visible",
);
assert(
  !document.querySelector('a[href="/lessons/1/detail"]'),
  "anonymous detail link disabled",
);
await router.push("/profile");
await settle();
assert(router.currentRoute.value.path === "/login", "anonymous route guard");
logged = true;
await router.push("/home");
await settle();
const { setLocale } = await server.ssrLoadModule("/src/i18n/index.js");
const pages = [
  "/home",
  "/dashboard",
  "/profile",
  "/lessons/create",
  "/lessons/manage",
  "/lessons/1/edit",
  "/lessons/accessmanage",
  "/systems",
  "/lessons/1/detail",
  "/video_play/1",
  "/video_detail/1",
  "/plans",
  "/exams",
  "/accounts",
  "/error",
  "/missing-page",
  "/pre_register",
  "/verify_email",
  "/forgot_password",
  "/reset_password",
  "/login",
];
for (const path of pages) {
  await router.push(path);
  await settle();
  assert(document.querySelector('button[title="登出"]'), "logout on " + path);
  assert(
    document.querySelector(".language-control select"),
    "language on " + path,
  );
  assert(!errors.length, "render error " + path + ": " + errors.join(","));
  if (!["/error", "/missing-page"].includes(path))
    assert(
      !document.querySelector(".state.warning"),
      "page unexpectedly failed: " + path,
    );
  const excluded =
    /^\/(video_play|video_detail|pre_register|verify_email|login)/.test(path);
  assert(
    Boolean(document.querySelector(".sidebar")) !== excluded,
    "sidebar rule " + path,
  );
}
// 普通学员没有等级字段，也应请求已授权课程的考试。
const readsBefore = examReads;
user.role = "user";
await router.push("/exams?lesson=1");
await settle();
assert(
  examReads > readsBefore,
  "authorized student can fetch exams without membership",
);
assert(!errors.length, "student exam render error");
for (const lang of ["en", "th", "zh"]) {
  setLocale(lang);
  await router.push("/home");
  await settle();
  assert(
    document.documentElement.lang === { zh: "zh-CN", en: "en", th: "th" }[lang],
    "document language",
  );
  assert(
    document.querySelector("h1").textContent ===
      { en: "Course catalog", th: "หน้าหลักสูตร", zh: "课程首页" }[lang],
    "translated heading",
  );
}
console.log(
  JSON.stringify(
    {
      pages: pages.length,
      languages: 3,
      checks: [
        "anonymous route guard",
        "all systems",
        "disabled course links",
        "shared sidebar",
        "logout",
        "language control",
        "render without exceptions",
      ],
      errors,
    },
    null,
    2,
  ),
);
app.unmount();
await server.close();
window.happyDOM.abort();
