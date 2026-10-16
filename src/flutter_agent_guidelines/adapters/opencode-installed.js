// Installed-version delivery: no fetching, session leases, exit handlers or tool guards.
import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";

const loadedHash = createHash("sha256").update(readFileSync(new URL(import.meta.url))).digest("hex");

const launcher = typeof __LAUNCHER__ === "undefined" ? null : __LAUNCHER__;

export default async ({ directory, worktree, client, flutterInstalled }) => {
  const command = flutterInstalled?.launcher || launcher;
  const cwd = directory || worktree;
  const invoke = () => new Promise((resolve, reject) => {
    const child = spawn(command[0], command.slice(1), { shell: false });
    let stdout = "", stderr = "";
    child.stdout.on("data", data => { stdout += data; });
    child.stderr.on("data", data => { stderr += data; });
    child.on("error", reject);
    child.on("close", code => {
      if (code !== 0) return reject(new Error(stderr || "installed controller failed"));
      try { resolve(JSON.parse(stdout)); } catch (error) { reject(error); }
    });
    child.stdin.on("error", reject);
    child.stdin.end(JSON.stringify({ cwd, adapter_hash: loadedHash }));
  });
  return {
    "experimental.chat.system.transform": async (_input, output) => {
      for (let i = output.system.length - 1; i >= 0; i--) {
        if (output.system[i].startsWith("<!-- flutter-guidelines:installed -->")) {
          output.system.splice(i, 1);
        }
      }
      try {
        const result = await invoke();
        if (result.warning) throw new Error(result.warning);
        if (typeof result.context !== "string" || !result.identity) {
          throw new Error("invalid installed controller response");
        }
        output.system.push(result.context);
      } catch (error) {
        const message = `Installed Flutter guidance unavailable; no context injected: ${error.message}`;
        console.error(message);
        try { await client?.tui.showToast({ body: { message, variant: "warning" } }); }
        catch { /* Notification availability does not control conversation access. */ }
      }
    },
  };
};
