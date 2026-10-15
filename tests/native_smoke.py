"""Optional non-model native probes; run using the clean installed interpreter."""

import json
import os
from pathlib import Path
import subprocess
import sys

from test_runtime import RuntimeTests


def main():
    fixture = RuntimeTests()
    fixture.setUp()
    fixture.install()
    root = fixture.root
    print(f"Native proof directory: {root}", flush=True)
    home = root / "isolated-home"
    home.mkdir()
    environment = dict(os.environ, HOME=str(home), CLAUDE_CONFIG_DIR=str(home / ".claude"),
                       XDG_CONFIG_HOME=str(home / "config"), XDG_CACHE_HOME=str(home / "cache"),
                       XDG_DATA_HOME=str(home / "data"), XDG_STATE_HOME=str(home / "state"),
                       OPENCODE_DISABLE_DEFAULT_PLUGINS="1", OPENCODE_DISABLE_EXTERNAL_SKILLS="1")
    for key in ("OPENCODE_CONFIG", "OPENCODE_CONFIG_CONTENT", "OPENCODE_PURE",
                "OPENCODE_DISABLE_PROJECT_CONFIG", "CLAUDE_CODE_SIMPLE",
                "CLAUDE_CODE_SAFE_MODE"):
        environment.pop(key, None)
    results = {}
    for label, command in (
        ("claude-doctor", ["claude", "doctor"]),
        ("opencode-config", ["opencode", "debug", "config", "--print-logs", "--log-level", "DEBUG"]),
        ("opencode-agent", ["opencode", "debug", "agent", "build", "--print-logs", "--log-level", "DEBUG"]),
    ):
        try:
            result = subprocess.run(command, cwd=fixture.repo, env=environment,
                                    capture_output=True, text=True, timeout=60)
            (root / (label + ".stdout")).write_text(result.stdout)
            (root / (label + ".stderr")).write_text(result.stderr)
            results[label] = {"command": command, "returncode": result.returncode}
            if label == "opencode-config" and result.returncode == 0:
                config = json.loads(result.stdout)
                plugins = config.get("plugin", config.get("plugins", []))
                results[label]["discovered"] = any(
                    "flutter-guidelines.js" in str(entry) for entry in plugins)
        except (OSError, subprocess.TimeoutExpired) as error:
            results[label] = {"command": command, "error": str(error)}
    (root / "results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    print("No model call requested. Inspect logs: config probes are not an interactive hook smoke.")
    return int(any(value.get("returncode") != 0 or value.get("discovered") is False
                   for value in results.values()))


if __name__ == "__main__":
    sys.exit(main())
