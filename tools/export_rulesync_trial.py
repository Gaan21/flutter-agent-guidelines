"""Export committed guidance into a disposable rulesync generation workspace."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = "src/flutter_agent_guidelines/payload/"
NOTICES = ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "provenance/README.md")
RULESYNC_VERSION = "36.0.2"


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def export(destination, ref="HEAD", architecture=False):
    """Export once, without writing into a checkout or running rulesync."""
    revision = git("rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()
    destination = Path(destination).absolute()
    destination = destination.parent.resolve() / destination.name
    if destination == ROOT or ROOT in destination.parents:
        raise ValueError("Use a disposable destination outside the guidance repository")
    if destination.exists() or destination.is_symlink():
        raise ValueError("Destination must not already exist")

    files = {}
    source_files = {}
    tree = git("ls-tree", "-rz", revision, "--", PAYLOAD, *NOTICES)
    for item in tree.split(b"\0"):
        if not item:
            continue
        metadata, raw_path = item.split(b"\t", 1)
        mode, kind, object_id = metadata.decode().split()
        path = raw_path.decode()
        if mode not in ("100644", "100755") or kind != "blob":
            raise ValueError("Only regular source files are accepted: " + path)
        content = git("cat-file", "blob", object_id)
        target = ".guidelines-trial/" + (
            "payload/" + path[len(PAYLOAD):] if path.startswith(PAYLOAD) else path
        )
        files[target] = content
        source_files[path] = {"sha256": digest(content), "export": target}

    entry_key = ".guidelines-trial/payload/AGENTS.md"
    if entry_key not in files or any(path not in source_files for path in NOTICES):
        raise ValueError("Source revision lacks the canonical entry or required notices")
    entry = files[entry_key].decode()
    # Generated root files live at the workspace root; preserve the raw entry too.
    rendered = re.sub(
        r"\]\(((?:decisions|procedures|profiles|references)/[^)]+)\)",
        r"](.guidelines-trial/payload/\1)",
        entry,
    )
    selection = "architecture" if architecture else "generic"
    preamble = (
        "# Delivery trial\n\n"
        "This is rulesync-generated delivery, not the installed Python adapter. "
        "No runtime integrity verification is provided by this entry. "
        "References below to installed adapters, connections or task joins describe "
        "those separate delivery modes, not capabilities of this trial.\n\n"
        f"Guidance source: `{revision}`. Selected Flutter profile: `{selection}`. "
        "Explicit local product decisions take precedence. "
        "Availability of another profile does not activate it.\n\n"
    )
    if architecture:
        preamble += (
            "The project explicitly selects the architecture profile: consult "
            "`.guidelines-trial/payload/profiles/architecture.md` when applicable.\n\n"
        )
    files[".rulesync/rules/flutter.md"] = (
        '---\nroot: true\ntargets: ["claudecode", "opencode"]\n'
        'description: "Selected Flutter guidance delivery trial"\n---\n\n'
        + preamble + rendered
    ).encode()
    files["rulesync.jsonc"] = json_bytes({
        "targets": ["claudecode", "opencode"],
        "features": ["rules"],
        "global": False,
        "delete": False,
    })
    manifest = json_bytes({
        "format": 1,
        "source_revision": revision,
        "rulesync_version": RULESYNC_VERSION,
        "modules": ["flutter"],
        "profile": selection,
        "source_files": source_files,
        "files": {path: digest(data) for path, data in sorted(files.items())},
        "transformation": "Trial preamble and workspace-relative entry links; source copies unchanged",
        "limits": "Preparation inventory only; not task approval or runtime delivery evidence",
    })
    destination.mkdir()
    try:
        for path, content in files.items():
            output = destination / path
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(content)
        (destination / "trial-manifest.json").write_bytes(manifest)
    except Exception:
        shutil.rmtree(destination)
        raise
    return {"source_revision": revision, "manifest_sha256": digest(manifest),
            "rulesync_version": RULESYNC_VERSION, "profile": selection}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="New directory outside the guidance checkout")
    parser.add_argument("--ref", default="HEAD", help="Source revision resolved once (default: local HEAD)")
    parser.add_argument("--architecture", action="store_true", help="Explicitly select the architecture profile")
    args = parser.parse_args()
    print(json.dumps(export(args.output, args.ref, args.architecture), indent=2))


if __name__ == "__main__":
    main()
