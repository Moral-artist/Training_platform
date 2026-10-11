import axios from "axios";
import { BASE_URL } from "../config";

let csrfToken = null;
let csrfPromise = null;
let membershipLevel = null;
const request = axios.create({ baseURL: BASE_URL, withCredentials: true });
export function setCsrfToken(token) {
  csrfToken = token;
}
export function getCsrfToken() {
  return csrfToken;
}

// 新增：会员等级管理
export function setMembershipLevel(level) {
  membershipLevel = level == null ? null : Number(level);
}

export function getMembershipLevel() {
  return membershipLevel;
}

export async function ensureCsrfToken() {
  if (csrfToken) return csrfToken;
  if (!csrfPromise) {
    csrfPromise = request
      .get("/api/user/user_info")
      .then((response) => {
        csrfToken = response.data.csrf_token;
        setMembershipLevel(response.data.membership_level);
        if (!csrfToken) throw new Error("UI:HTTP_401");
        return csrfToken;
      })
      .finally(() => {
        csrfPromise = null;
      });
  }
  return csrfPromise;
}

const publicAuth = new Set([
  "/api/auth/login",
  "/api/auth/pre_register",
  "/api/auth/verify_register",
  "/api/auth/pre_reset",
  "/api/auth/verify_reset",
]);
request.interceptors.request.use(async (config) => {
  if (
    ["POST", "PUT", "PATCH", "DELETE"].includes(config.method?.toUpperCase()) &&
    !publicAuth.has(config.url)
  ) {
    config.headers["X-CSRF-Token"] = await ensureCsrfToken();
  }
  return config;
});
request.interceptors.response.use(
  (response) => {
    if (response.data?.csrf_token) setCsrfToken(response.data.csrf_token);
      // 获取用户资料时同步更新会员等级
    if (response.config.url === "/api/user/user_info") {
      setMembershipLevel(response.data.membership_level);
    }
    if (response.config.url === "/api/auth/logout") setCsrfToken(null);
    return response;
  },
  (error) => {
    if (
      error.response?.status === 401 ||
      error.response?.data?.detail === "Invalid CSRF token"
    )
      setCsrfToken(null);
      setMembershipLevel(null);
    if (error.response?.status === 401 && !publicAuth.has(error.config?.url))
      window.dispatchEvent(new Event("training-session-expired"));
    // 不重放修改请求，避免重复创建课程；下次操作重新取 CSRF。
    return Promise.reject(error);
  },
);
export default request;
