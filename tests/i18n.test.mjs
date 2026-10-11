import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
const messages = JSON.parse(
  await fs.readFile(
    new URL("../src/i18n/messages.json", import.meta.url),
    "utf8",
  ),
);
test("all interface keys have Chinese, English and Thai translations", () => {
  assert.deepEqual(
    Object.keys(messages.en).sort(),
    Object.keys(messages.zh).sort(),
  );
  assert.deepEqual(
    Object.keys(messages.th).sort(),
    Object.keys(messages.zh).sort(),
  );
  for (const locale of ["zh", "en", "th"])
    for (const value of Object.values(messages[locale]))
      assert.ok(value.length);
});
