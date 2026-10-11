import axios from "axios";
import request from "./request";
// 新签名逐段获取，不将签名 URL 持久化。每次恢复以 R2 实际分段清单为准。
export async function transferFile(file, info, onProgress, signal) {
  const done = new Map(info.parts.map((p) => [p.part_number, p.size]));
  const update = (extra) =>
    onProgress(
      Math.min(
        100,
        Math.round(
          (([...done.values()].reduce((a, b) => a + b, 0) + extra) /
            file.size) *
            100,
        ),
      ),
    );
  update(0);
  for (let number = 1; number <= info.part_count; number++) {
    if (done.has(number)) continue;
    const from = (number - 1) * info.part_size,
      chunk = file.slice(from, Math.min(file.size, from + info.part_size));
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        const { data } = await request.post(
          `/api/uploads/${info.asset_id}/part`,
          null,
          { params: { part_number: number }, signal },
        );
        // R2 不接收登录 Cookie 和 CSRF；不要使用带站点凭证的 request 实例。
        await axios.put(data.upload_url, chunk, {
          signal,
          withCredentials: false,
          headers: { "Content-Type": file.type },
          onUploadProgress: (e) => update(e.loaded),
        });
        done.set(number, chunk.size);
        update(0);
        break;
      } catch (error) {
        if (
          signal.aborted ||
          attempt === 2 ||
          [401, 404, 409, 422].includes(error.response?.status)
        )
          throw error;
        await new Promise((resolve) =>
          setTimeout(resolve, 500 * (attempt + 1)),
        );
      }
    }
  }
  return (
    await request.post(`/api/uploads/${info.asset_id}/complete`, null, {
      signal,
    })
  ).data;
}
export function fingerprintFile(file, progress, signal) {
  return new Promise((resolve, reject) => {
    const worker = new Worker(new URL("../workers/hash.js", import.meta.url), {
      type: "module",
    });
    const finish = () => {
      worker.terminate();
      signal.removeEventListener("abort", abort);
    };
    const abort = () => {
      finish();
      reject(new Error("UI:paused"));
    };
    signal.addEventListener("abort", abort, { once: true });
    if (signal.aborted) return abort();
    worker.onmessage = ({ data }) => {
      if (data.progress !== undefined) progress(data.progress);
      if (data.hash) {
        finish();
        resolve(data.hash);
      } else if (data.error) {
        finish();
        reject(new Error("UI:invalidFile"));
      }
    };
    worker.onerror = () => {
      finish();
      reject(new Error("UI:invalidFile"));
    };
    worker.postMessage({ file });
  });
}
