import { hashBlob } from "../utils/sha256";
self.onmessage = async ({ data }) => {
  try {
    const hash = await hashBlob(data.file, (progress) =>
      self.postMessage({ progress }),
    );
    self.postMessage({ hash });
  } catch {
    self.postMessage({ error: true });
  }
};
