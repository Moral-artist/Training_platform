import { createRouter, createWebHistory } from "vue-router";
import { auth, loadUser, canUpload, isAdmin } from "../stores/auth";
import { notify } from "../stores/notices";
const view = (name) => () => import(`../views/${name}.vue`);
const routes = [
  { path: "/", redirect: "/home" },
  {
    path: "/home",
    component: view("Home"),
    meta: { title: "home", public: true },
  },
  ...[
    ["/login", "login"],
    ["/pre_register", "register"],
    ["/verify_email", "verifyEmail"],
    ["/forgot_password", "forgotPassword"],
    ["/reset_password", "resetPassword"],
  ].map(([path, title]) => ({
    path,
    component: view("Auth"),
    meta: {
      title,
      public: true,
      noSidebar: !["forgotPassword", "resetPassword"].includes(title),
      authKind: title,
    },
  })),
  { path: "/register", redirect: "/pre_register" },
  { path: "/verify_register", redirect: "/verify_email" },
  {
    path: "/dashboard",
    component: view("Dashboard"),
    meta: { title: "dashboard" },
  },
  { path: "/profile", component: view("Profile"), meta: { title: "profile" } },
  {
    path: "/lessons/create",
    component: view("LessonCreate"),
    meta: { title: "createLesson", role: "manager" },
  },
  { path: "/lessons/lessoncreate", redirect: "/lessons/create" },
  {
    path: "/lessons/manage",
    component: view("LessonManage"),
    meta: { title: "manageLessons" },
  },
  {
    path: "/lessons/:lessonId/edit",
    component: view("LessonCreate"),
    meta: { title: "editLesson" },
  },
  {
    path: "/lessons/accessmanage",
    component: view("LessonAccessManage"),
    meta: { title: "access", role: "admin" },
  },
  {
    path: "/systems",
    component: view("SystemCreate"),
    meta: { title: "systems", role: "admin" },
  },
  { path: "/lessons/systemcreate", redirect: "/systems" },
  {
    path: "/lessons/:lessonId/detail",
    component: view("LessonDetail"),
    meta: { title: "videoDetail" },
  },
  {
    path: "/video_detail/:lessonId",
    component: view("LessonDetail"),
    meta: { title: "videoDetail", noSidebar: true },
  },
  {
    path: "/video_play/:lessonId",
    component: view("VideoPlay"),
    meta: { title: "playPage", noSidebar: true },
  },
  {
    path: "/lessons/:major/:lessonId",
    redirect: (to) => `/lessons/${to.params.lessonId}/detail`,
  },
  {
    path: "/lessons/:systemId",
    component: view("Home"),
    meta: { title: "home" },
  },
  { path: "/plans", component: view("Plans"), meta: { title: "plans" } },
  {
    path: "/createplan",
    component: view("CreatePlan"),
    name:"createplan"
  },
  {
    path: "/plans/templates/manage",
    component: view("ManagePresetPlan"),
    name: "createPresetPlan",
    meta: {
      title: "createTemplate",
      role: "manager",
    },
  },
  { path: "/exams", component: view("Exams"), meta: { title: "exams" } },
  {
    path: "/accounts",
    component: view("Accounts"),
    meta: { title: "accounts", role: "admin" },
  },
  {
    path: "/error",
    component: view("ErrorPage"),
    meta: { title: "errorTitle", public: true },
  },
  {
    path: "/:pathMatch(.*)*",
    component: view("ErrorPage"),
    meta: { title: "errorTitle", public: true, error: "HTTP_404" },
  },

];
const router = createRouter({ history: createWebHistory(), routes });
router.beforeEach(async (to) => {
  try {
    await loadUser(true);
  } catch (error) {
    if (to.path === "/error") return true;
    return {
      path: "/error",
      query: { code: `HTTP_${error.response?.status || 503}` },
    };
  }
  if (!to.meta.public && !auth.user)
    return { path: "/login", query: { redirect: to.fullPath } };
  if (
    (to.meta.role === "admin" && !isAdmin()) ||
    (to.meta.role === "manager" && !canUpload())
  ) {
    notify("HTTP_403");
    return "/home";
  }
});
router.onError(() => notify("unexpectedError", "error"));
export default router;
