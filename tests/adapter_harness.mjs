import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { readFileSync, writeFileSync, mkdirSync, symlinkSync } from "node:fs";
import { join } from "node:path";

const repo = process.argv[2];
const pluginPath = join(repo, ".opencode/plugins/flutter-guidelines.js");
const { default: plugin } = await import(pathToFileURL(pluginPath));
mkdirSync(join(repo, "lib/nested"), { recursive: true });
const warnings = [];
const hooks = await plugin({ directory: join(repo, "lib/nested"), worktree: repo,
  client: { tui: { showToast: async ({ body }) => { warnings.push(body.message); } } } });
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
await hooks["experimental.chat.system.transform"]({}, { system: [] });
assert.match(warnings.at(-1), /sessionID/);
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
await hooks["chat.message"]({ sessionID: "implementer" }, {});
assert.match(warnings.at(-1), /modified|differs/);
await hooks["tool.execute.before"]({ sessionID: "implementer", tool: "edit" },
  { args: { filePath: join(repo, "AGENTS.md") } });
await assert.rejects(hooks["tool.execute.before"]({ sessionID: "implementer", tool: "edit" },
  { args: { filePath: join(repo, ".flutter-guidelines/work.json") } }), /protected/);
writeFileSync(pluginPath, original);
await hooks.dispose(); // Direct callable cleanup test, not native disposal-delivery evidence.
state = JSON.parse(readFileSync(join(repo, ".flutter-guidelines/work.json")));
assert.equal(Object.keys(state.sessions).length, 0);
await hooks["chat.message"]({ sessionID: "implementer" }, {});
writeFileSync(join(repo, "overlay.md"), "changed overlay");
await hooks["experimental.chat.system.transform"]({ sessionID: "implementer" }, output);
assert.deepEqual(output.system, ["Existing system authority"], "remove stale injection on failure");
assert.match(warnings.at(-1), /drift/);
// Exercise failures before Python can return a protocol response.
for (const [index, launcher] of [
  [join(repo, "missing-python")],
  [process.execPath, "-e", "process.exit(1)"],
  [process.execPath, "-e", "process.stdin.resume(); process.stdout.write('invalid json')"],
].entries()) {
  writeFileSync(pluginPath, original.toString().replace(/^const launcher = .*;$/m,
    `const launcher = ${JSON.stringify(launcher)};`));
  const { default: failingPlugin } = await import(`${pathToFileURL(pluginPath)}?failure=${index}`);
  const failing = await failingPlugin({ directory: repo, client: {
    tui: { showToast: async ({ body }) => { warnings.push(body.message); throw new Error("UI unavailable"); } },
  } });
  await failing.config({});
  await failing["chat.message"]({ sessionID: "failure" }, {});
  const stale = { system: ["Other authority", "<!-- flutter-guidelines:context -->stale"] };
  await failing["experimental.chat.system.transform"]({ sessionID: "failure" }, stale);
  assert.deepEqual(stale.system, ["Other authority"]);
  assert.match(warnings.at(-1), /unavailable/);
  await failing["tool.execute.before"]({ sessionID: "failure", tool: "read" },
    { args: { filePath: join(repo, ".flutter-guidelines/work.json") } });
  await failing["tool.execute.before"]({ sessionID: "failure", tool: "edit" },
    { args: { filePath: join(repo, "AGENTS.md") } });
  const alias = join(repo, `state-alias-${index}`);
  symlinkSync(join(repo, ".flutter-guidelines"), alias);
  for (const target of [join(repo, ".flutter-guidelines/work.json"), join(alias, "new.json")]) {
    await assert.rejects(failing["tool.execute.before"]({ sessionID: "failure", tool: "edit" },
      { args: { filePath: target } }), /protected/);
  }
}
writeFileSync(pluginPath, original);
console.log("PASS: controller hooks, visible degradation and protected writes");
