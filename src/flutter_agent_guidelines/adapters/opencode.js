// Installed local adapter. No fetched source is executed.
import { spawn, spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";

const launcher = __LAUNCHER__;
const filename = fileURLToPath(import.meta.url);
const loadedHash = (() => {
  try { return createHash("sha256").update(readFileSync(filename)).digest("hex"); }
  catch { return "unavailable"; } // Defer failure to blocking hooks, not plugin construction.
})();

export default async ({ directory, worktree }) => {
  const cwd = directory || worktree;
  const lease = randomUUID();
  const sessions = new Map();
  const request = (event, session, extra = {}) => ({
    event, session_id: session, cwd, lease, adapter_hash: loadedHash,
    adapter_path: filename, ...extra,
  });
  const invoke = (payload) => new Promise((resolve, reject) => {
    const child = spawn(launcher[0], launcher.slice(1), { shell: false });
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
    if (!session) throw new Error("Flutter runtime requires native sessionID");
    const result = await invoke(request(event, session, {
      expected: sessions.get(session), ...extra,
    }));
    sessions.set(session, result.work.snapshot);
    return result;
  };
  // No async work on exit; idle is deliberately not a lifecycle boundary.
  process.once("exit", () => {
    for (const session of sessions.keys()) {
      spawnSync(launcher[0], launcher.slice(1), {
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
    config: async () => { await invoke(request("doctor", "")); },
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
      output.system.push(result.context);
    },
    "tool.execute.before": async (input, output) => {
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
