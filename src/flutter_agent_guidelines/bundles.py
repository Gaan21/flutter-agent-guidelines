"""One payload allowlist, read using installed resource APIs."""

from importlib import metadata, resources

from .snapshots import SnapshotError, canonical, digest, file_hashes, write_snapshot

DISTRIBUTION = "flutter-agent-guidelines"
PAYLOAD = (
    "AGENTS.md", "decisions/boundaries.md", "decisions/reliability.md",
    "procedures/verification.md", "references/upstream.md",
)
NOTICES = ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "provenance/README.md")


def read_resource(name):
    """Return bytes for one allowlisted payload resource (no filesystem writes)."""
    if name not in PAYLOAD:
        raise SnapshotError("unknown payload resource")
    return resources.files("flutter_agent_guidelines").joinpath("payload", name).read_bytes()


def package_files():
    distribution = metadata.distribution(DISTRIBUTION)
    files = {f"payload/{name}": read_resource(name) for name in PAYLOAD}
    # PEP 639 notices live once, in distribution metadata, not a second payload.
    for name in NOTICES:
        matches = [item for item in distribution.files or ()
                   if str(item).endswith(f".dist-info/licenses/{name}")]
        if len(matches) != 1:
            raise SnapshotError("install a wheel with complete license metadata")
        files[name] = distribution.locate_file(matches[0]).read_bytes()
    return files


def inspect_package():
    files = package_files()
    version = metadata.version(DISTRIBUTION)
    return {
        "kind": "guidance-bundle", "package": DISTRIBUTION, "version": version,
        "development": ".dev" in version, "source_approval": "not supplied",
        "payload_digest": digest(canonical(file_hashes({
            name: content for name, content in files.items() if name.startswith("payload/")
        }))),
        "files": file_hashes(files),
    }


def export_bundle(parent):
    """Materialize a content-addressed bundle; export never implies approval."""
    information = inspect_package()
    information.pop("files")
    return write_snapshot(parent, package_files(), information)
