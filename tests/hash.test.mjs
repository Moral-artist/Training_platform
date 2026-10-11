import test from "node:test";
import assert from "node:assert/strict";
import { createHash, randomBytes } from "node:crypto";
import { Sha256, hashBlob } from "../src/utils/sha256.js";
for (const size of [0, 1, 55, 56, 63, 64, 65, 1024, 4 * 1024 * 1024 + 200]) {
  test(`incremental hash matches SHA256 for ${size} bytes`, async () => {
    const data = randomBytes(size),
      hash = new Sha256();
    for (let offset = 0; offset < size; offset += 113)
      hash.update(data.subarray(offset, offset + 113));
    const expected = createHash("sha256").update(data).digest("hex");
    assert.equal(hash.digest(), expected);
    assert.equal(await hashBlob(new Blob([data])), expected);
  });
}
