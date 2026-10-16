// Direct hook dispatch only; not evidence of native OpenCode callback delivery.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { appendFileSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { execFileSync } from "node:child_process";

const repo = process.argv[2];
const path = join(repo, ".opencode/plugins/flutter-guidelines.js");
const { default: plugin } = await import(pathToFileURL(path));
const warnings = [];
const hooks = await plugin({ directory: repo, client: { tui: {
  showToast: async ({ body }) => warnings.push(body.message),
} } });
await hooks.config({});
const workPath = join(repo, ".flutter-guidelines/work.json");
await Promise.all([hooks["chat.message"]({ sessionID: "one" }, {}),
  hooks["chat.message"]({ sessionID: "two" }, {})]);
const first = JSON.parse(readFileSync(workPath));
assert.equal(Object.keys(first.sessions).length, 2);
const output = { system: ["Existing authority"] };
await hooks["experimental.chat.system.transform"]({ sessionID: "one" }, output);
assert.match(output.system[1], /Verified Guidelines-Root/);
await hooks["experimental.chat.system.transform"]({ sessionID: "one" }, output);
assert.equal(output.system.length, 2);
await assert.rejects(hooks["tool.execute.before"]({ sessionID: "one", tool: "edit" },
  { args: { filePath: workPath } }), /protected/);
const cached = JSON.parse(readFileSync(join(repo, ".flutter-guidelines/engine.json")));
await assert.rejects(hooks["tool.execute.before"]({ sessionID: "one", tool: "edit" },
  { args: { filePath: cached.deployment } }), /protected/);
await hooks.event({ event: { type: "session.idle" } });
assert.equal(Object.keys(JSON.parse(readFileSync(workPath)).sessions).length, 2);
await hooks.event({ event: { type: "session.deleted", properties: { info: { id: "two" } } } });
assert.equal(Object.keys(JSON.parse(readFileSync(workPath)).sessions).length, 1);
await hooks.dispose();
assert.equal(Object.keys(JSON.parse(readFileSync(workPath)).sessions).length, 0);
assert.deepEqual(warnings, []);
// Close accepted work and advance a trusted fixture while retaining this transport instance.
execFileSync(process.argv[4], ["-I", "-m", "flutter_agent_guidelines.cli", "end", "--repo", repo]);
const source = process.argv[3];
appendFileSync(join(source, "src/flutter_agent_guidelines/adapters/opencode.js"),
  '\nglobalThis.flutterAdapterTrialRevision = "two";\n');
execFileSync("git", ["-C", source, "add", "."]);
execFileSync("git", ["-C", source, "-c", "user.name=Fixture", "-c",
  "user.email=fixture@example.invalid", "commit", "-m", "fixture adapter update"]);
await hooks["chat.message"]({ sessionID: "three" }, {});
assert.equal(globalThis.flutterAdapterTrialRevision, "two", "new JS executes without replacing transport");
const second = JSON.parse(readFileSync(workPath));
assert.notEqual(first.controller.digest, second.controller.digest);
assert.notEqual(first.revision, second.revision);
await hooks.dispose();
// Keep the fallback local guard even when Python cannot launch.
const original = readFileSync(path, "utf8");
writeFileSync(path, original.replace(/^const launcher = .*;$/m,
  `const launcher = ${JSON.stringify([join(repo, "missing-python")])};`));
const { default: failingPlugin } = await import(`${pathToFileURL(path)}?failure`);
const failing = await failingPlugin({ directory: repo, client: { tui: {
  showToast: async ({ body }) => warnings.push(body.message),
} } });
const stale = { system: ["Existing authority", "<!-- flutter-guidelines:context -->stale"] };
await failing["experimental.chat.system.transform"]({ sessionID: "failure" }, stale);
assert.deepEqual(stale.system, ["Existing authority"]);
assert.match(warnings.at(-1), /unavailable/);
await assert.rejects(failing["tool.execute.before"]({ sessionID: "failure", tool: "edit" },
  { args: { filePath: cached.deployment } }), /protected/);
writeFileSync(path, original);
console.log("PASS: stable transport, live versioned-adapter selection, leases and fallback guards");
