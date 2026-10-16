import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const [plugin, repo] = process.argv.slice(2);
const factory = (await import(pathToFileURL(plugin).href)).default;
const warnings = [];
const hooks = await factory({ directory: repo,
  client: { tui: { showToast: async item => warnings.push(item.body.message) } } });
assert.deepEqual(Object.keys(hooks), ["experimental.chat.system.transform"]);
const transform = hooks["experimental.chat.system.transform"];
const output = { system: ["native local rules"] };
await transform({ sessionID: "implementer" }, output);
assert.equal(output.system.length, 2);
assert.ok(output.system[1].startsWith("<!-- flutter-guidelines:installed -->"));
const first = output.system[1];
await transform({ sessionID: "reviewer" }, output);
assert.equal(output.system.length, 2);
assert.equal(output.system[1], first);
assert.equal(warnings.length, 0);
const pin = join(repo, ".flutter-guidelines-installed.json");
const original = readFileSync(pin);
try {
  const changed = JSON.parse(original);
  changed.controller = "0".repeat(64);
  writeFileSync(pin, JSON.stringify(changed));
  await transform({}, output);
  assert.deepEqual(output.system, ["native local rules"]);
  assert.equal(warnings.length, 1);
  assert.match(warnings[0], /differs from project pin/);
} finally {
  writeFileSync(pin, original);
}
console.log("PASS: installed adapter delivery, deduplication, review identity and mismatch warning");
