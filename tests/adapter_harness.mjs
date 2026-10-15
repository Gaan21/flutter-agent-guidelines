import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const repo = process.argv[2];
const pluginPath = join(repo, ".opencode/plugins/flutter-guidelines.js");
const { default: plugin } = await import(pathToFileURL(pluginPath));
mkdirSync(join(repo, "lib/nested"), { recursive: true });
const hooks = await plugin({ directory: join(repo, "lib/nested"), worktree: repo });
await hooks.config({ permission: { edit: "deny" } });
await hooks["chat.message"]({ sessionID: "implementer" }, { parts: [] });
const output = { system: ["Existing system authority"] };
await hooks["experimental.chat.system.transform"]({ sessionID: "implementer" }, output);
assert.equal(output.system[0], "Existing system authority");
assert.match(output.system[1], /Verified Guidelines-Root:/);
assert.match(output.system[1], /local\/policies\/AGENTS.md/);
await hooks["experimental.chat.system.transform"]({ sessionID: "implementer" }, output);
assert.equal(output.system.length, 2, "one entry per model context; preserve existing system text");
await hooks["chat.message"]({ sessionID: "reviewer" }, { parts: [] });
const review = { system: [] };
await hooks["experimental.chat.system.transform"]({ sessionID: "reviewer" }, review);
assert.equal(output.system[1], review.system[0]);
await assert.rejects(hooks["experimental.chat.system.transform"]({}, { system: [] }), /sessionID/);
await hooks["tool.execute.before"]({ sessionID: "implementer", tool: "read" },
  { args: { filePath: join(repo, ".flutter-guidelines/work.json") } });
await assert.rejects(hooks["tool.execute.before"]({ sessionID: "reviewer", tool: "edit" },
  { args: { filePath: join(repo, ".flutter-guidelines/work.json") } }), /protected/);
await hooks.event({ event: { type: "session.idle", properties: { sessionID: "reviewer" } } });
let state = JSON.parse(readFileSync(join(repo, ".flutter-guidelines/work.json")));
assert.equal(Object.keys(state.sessions).length, 2);
await hooks.event({ event: { type: "session.deleted", properties: { info: { id: "reviewer" } } } });
state = JSON.parse(readFileSync(join(repo, ".flutter-guidelines/work.json")));
assert.equal(Object.keys(state.sessions).length, 1);
const original = readFileSync(pluginPath);
writeFileSync(pluginPath, Buffer.concat([original, Buffer.from("\n// live change\n")]));
await assert.rejects(hooks["chat.message"]({ sessionID: "implementer" }, {}), /modified|differs/);
writeFileSync(pluginPath, original);
await hooks.dispose(); // Direct callable cleanup test, not native disposal-delivery evidence.
state = JSON.parse(readFileSync(join(repo, ".flutter-guidelines/work.json")));
assert.equal(Object.keys(state.sessions).length, 0);
await hooks["chat.message"]({ sessionID: "implementer" }, {});
writeFileSync(join(repo, "overlay.md"), "changed overlay");
await assert.rejects(hooks["experimental.chat.system.transform"]({ sessionID: "implementer" },
  { system: [] }), /drift/);
console.log("PASS: real controller message/system/tool/event hooks and fail-closed live changes");
