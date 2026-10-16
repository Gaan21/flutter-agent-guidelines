// Versioned runtime adapter; executable source requires explicit bootstrap approval.
import { spawn, spawnSync } from "node:child_process";
import { readFileSync, realpathSync } from "node:fs";
import { resolve, dirname, basename, sep } from "node:path";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";

const launcher = typeof __LAUNCHER__ === "undefined" ? null : __LAUNCHER__;
const filename = fileURLToPath(import.meta.url);
const loadedHash = (() => {
  try { return createHash("sha256").update(readFileSync(filename)).digest("hex"); }
  catch { return "unavailable"; } // Defer failure to blocking hooks, not plugin construction.
})();

export default async ({ directory, worktree, client, flutterBridge }) => {
  const command = flutterBridge?.launcher || launcher;
  const cwd = directory || worktree;
  const repo = flutterBridge?.repo || resolve(dirname(filename), "../..");
  const physical = path => {
    try { return realpathSync(path); }
    catch {
      const parent = dirname(path);
      return parent === path ? path : resolve(physical(parent), basename(path));
    }
  };
  const protectedPaths = [".flutter-guidelines", ".flutter-guidelines.json",
    ".claude/settings.local.json", ".opencode/plugins/flutter-guidelines.js"]
    .map(path => physical(resolve(repo, path)));
  const guard = (tool, args) => {
    if (["read", "glob", "grep", "list", "webfetch", "websearch"].includes(tool)) return;
    const visit = value => {
      if (typeof value === "string") {
        for (const token of [value, ...(value.match(/[^\s"'`<>|;()]+/g) || [])]) {
          if (token.length > 4096 || /[\n\0]/.test(token)) continue;
          const path = physical(resolve(cwd, token));
          if (protectedPaths.some(root => path === root || path.startsWith(root + sep))) {
            throw new Error("tool write/execute target is protected runtime state; use Read for inspection");
          }
        }
      } else if (value && typeof value === "object") Object.values(value).forEach(visit);
    };
    visit(args);
  };
  const warn = async message => {
    console.error(message);
    try {
      await client?.tui.showToast({ body: { message, variant: "warning" } });
    } catch { /* Notification failure must not block a conversation. */ }
  };
  const lease = flutterBridge?.lease || randomUUID();
  const sessions = new Map();
  const request = (event, session, extra = {}) => ({
    event, session_id: session, cwd, lease, adapter_hash: flutterBridge?.hash || loadedHash,
    adapter_path: flutterBridge?.path || filename, ...extra,
  });
  const invoke = (payload) => new Promise((resolve, reject) => {
    const child = spawn(command[0], command.slice(1), { shell: false });
    let stdout = "", stderr = "";
    child.stdout.on("data", data => { stdout += data; });
    child.stderr.on("data", data => { stderr += data; });
    child.on("error", reject);
    child.on("close", code => {
      if (code !== 0) return reject(new Error(stderr || "Flutter runtime failed"));
      try { resolve(JSON.parse(stdout)); } catch (error) { reject(error); }
    });
    child.stdin.on("error", reject);
    child.stdin.end(JSON.stringify(payload));
  });
  const prepare = async (session, event = "verify", extra = {}) => {
    try {
      if (!session) throw new Error("Flutter runtime requires native sessionID");
      const result = await invoke(request(event, session, {
        expected: sessions.get(session), ...extra,
      }));
      if (result.warning) { await warn(result.warning); return null; }
      if (!result.work?.snapshot || typeof result.context !== "string") {
        throw new Error("invalid runtime response");
      }
      sessions.set(session, result.work.snapshot);
      return result;
    } catch (error) {
      await warn(`Flutter guidelines unavailable; no context injected: ${error.message}`);
      return null;
    }
  };
  // No async work on exit; idle is deliberately not a lifecycle boundary.
  process.once("exit", () => {
    for (const session of sessions.keys()) {
      spawnSync(command[0], command.slice(1), {
        input: JSON.stringify(request("release", session)), timeout: 10000,
        shell: false, stdio: ["pipe", "ignore", "ignore"],
      });
    }
  });
  return {
    // Callable cleanup; native dispose delivery is not established by config probes.
    dispose: async () => {
      for (const session of sessions.keys()) {
        await invoke(request("release", session));
        sessions.delete(session);
      }
    },
    config: async () => {
      try {
        const result = await invoke(request("doctor", ""));
        if (result.warning) await warn(result.warning);
      } catch (error) { await warn(`Flutter guidelines unavailable: ${error.message}`); }
    },
    "chat.message": async (input) => {
      await prepare(input.sessionID, "prompt");
    },
    "experimental.chat.system.transform": async (input, output) => {
      const result = await prepare(input.sessionID);
      for (let index = output.system.length - 1; index >= 0; index--) {
        if (output.system[index].startsWith("<!-- flutter-guidelines:context -->")) {
          output.system.splice(index, 1);
        }
      }
      if (result) output.system.push(result.context);
    },
    "tool.execute.before": async (input, output) => {
      guard(input.tool, output.args);
      await prepare(input.sessionID, "tool", {
        tool_name: input.tool, tool_input: output.args,
      });
    },
    event: async ({ event }) => {
      if (event.type === "session.deleted") {
        const id = event.properties.info.id;
        if (sessions.has(id)) {
          await invoke(request("release", id));
          sessions.delete(id);
        }
      }
    },
  };
};
