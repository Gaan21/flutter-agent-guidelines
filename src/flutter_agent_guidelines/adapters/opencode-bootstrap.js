// Stable protocol-1 transport. Per-work hooks are imported from verified deployments.
import { spawn } from "node:child_process";
import { readFileSync, realpathSync } from "node:fs";
import { resolve, dirname, basename, sep } from "node:path";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import { homedir } from "node:os";

const launcher = __LAUNCHER__;
const filename = fileURLToPath(import.meta.url);
const loadedHash = createHash("sha256").update(readFileSync(filename)).digest("hex");

export default async input => {
  const cwd = input.directory || input.worktree;
  const repo = resolve(dirname(filename), "../..");
  const lease = randomUUID();
  const sessions = new Map(), instances = new Map();
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
  protectedPaths.push(physical(resolve(dirname(launcher[0]), "..")));
  try {
    const config = JSON.parse(readFileSync(resolve(repo, ".flutter-guidelines.json")));
    protectedPaths.push(physical(resolve(config.cache || process.env.FLUTTER_GUIDELINES_CACHE ||
      resolve(homedir(), ".cache/flutter-agent-guidelines"))));
  } catch { /* Keep the local guard active during configuration failure. */ }
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
    try { await input.client?.tui.showToast({ body: { message, variant: "warning" } }); }
    catch { /* Warning delivery is best effort; conversation continues. */ }
  };
  const invoke = payload => new Promise((accept, reject) => {
    const child = spawn(launcher[0], launcher.slice(1), { shell: false });
    let stdout = "", stderr = "";
    child.stdout.on("data", data => { stdout += data; });
    child.stderr.on("data", data => { stderr += data; });
    child.on("error", reject);
    child.on("close", code => {
      if (code) return reject(new Error(stderr || "bootstrap failed"));
      try { accept(JSON.parse(stdout)); } catch (error) { reject(error); }
    });
    child.stdin.on("error", reject);
    child.stdin.end(JSON.stringify(payload));
  });
  const select = async session => {
    try {
      if (!session) throw new Error("native sessionID required");
      const result = await invoke({ event: "select", session_id: session, lease, cwd,
        adapter_path: filename, adapter_hash: loadedHash, expected: sessions.get(session)?.snapshot });
      if (result.warning) throw new Error(result.warning);
      if (!result.module || !result.work?.snapshot) throw new Error("invalid bootstrap response");
      const key = result.work.id;
      if (!instances.has(key)) {
        // Reserve the promise before import: parallel callbacks share a single hook instance.
        instances.set(key, (async () => {
          const { default: plugin } = await import(pathToFileURL(result.module));
          return plugin({ ...input, flutterBridge: { launcher, repo, lease,
            path: filename, hash: loadedHash } });
        })());
      }
      const hooks = await instances.get(key);
      sessions.set(session, { snapshot: result.work.snapshot, hooks });
      return hooks;
    } catch (error) {
      await warn(`Flutter guidelines unavailable; no context injected: ${error.message}`);
      return null;
    }
  };
  return {
    config: async () => {}, // Discovery must not create work at client configuration time.
    "chat.message": async (a, b) => (await select(a.sessionID))?.["chat.message"]?.(a, b),
    "experimental.chat.system.transform": async (a, b) => {
      const hooks = await select(a.sessionID);
      if (hooks) return hooks["experimental.chat.system.transform"]?.(a, b);
      b.system = b.system.filter(text => !text.startsWith("<!-- flutter-guidelines:context -->"));
    },
    "tool.execute.before": async (a, b) => {
      guard(a.tool, b.args);
      return (await select(a.sessionID))?.["tool.execute.before"]?.(a, b);
    },
    event: async value => {
      if (value.event.type === "session.deleted") {
        const id = value.event.properties.info.id;
        await sessions.get(id)?.hooks.event?.(value);
        sessions.delete(id);
      }
    },
    dispose: async () => {
      for (const hooks of instances.values()) await (await hooks).dispose?.();
      sessions.clear();
    },
  };
};
