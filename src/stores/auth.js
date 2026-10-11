// 登录凭证只在 HttpOnly Cookie 中；不将会话/CSRF 写入 localStorage。
import { reactive } from "vue";
import request, { setCsrfToken } from "../api/request";
export const auth = reactive({ user: null, checked: false });
let pending;
export async function loadUser(force = false) {
  if (pending) return pending;
  if (auth.checked && !force) return auth.user;
  pending = request
    .get("/api/user/user_info")
    .then(({ data }) => {
      auth.user = data;
      auth.checked = true;
      return data;
    })
    .catch((error) => {
      if (error.response?.status !== 401) throw error;
      auth.user = null;
      auth.checked = true;
      setCsrfToken(null);
      return null;
    })
    .finally(() => {
      pending = null;
    });
  return pending;
}
export function clearUser() {
  auth.user = null;
  auth.checked = false;
  setCsrfToken(null);
}
export const canUpload = () =>
  ["administer", "manager"].includes(auth.user?.role);
export const isAdmin = () => auth.user?.role === "administer";

window.addEventListener("training-session-expired", () => {
  auth.user = null;
  auth.checked = true;
  setCsrfToken(null);
});
