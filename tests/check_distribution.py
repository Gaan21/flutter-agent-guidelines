"""Build outside checkout; inspect archives; install and test from isolated cwd.

Run with a Python >=3.11 build environment containing build, setuptools and wheel:
    python tests/check_distribution.py
Artifacts and environments remain in the printed temporary directory for review.
"""

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile

PAYLOAD = ("AGENTS.md", "decisions/boundaries.md", "decisions/reliability.md",
           "procedures/verification.md", "references/upstream.md", "profiles/architecture.md")
NOTICES = ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "provenance/README.md")
ADAPTERS = ("adapters/opencode.js", "adapters/opencode-bootstrap.js",
            "adapters/opencode-installed.js", "bootstrap-contract.json")


def run(*arguments, cwd):
    print("+", *map(str, arguments), flush=True)
    subprocess.run(list(map(str, arguments)), cwd=cwd, check=True)


def main():
    repository = Path(__file__).resolve().parents[1]
    temporary = Path(tempfile.mkdtemp(prefix="flutter-guidelines-proof-")).resolve()
    print(f"Proof directory: {temporary}", flush=True)
    source = temporary / "source"
    source.mkdir()
    for name in ("pyproject.toml", "MANIFEST.in", "README.md", "AGENTS.md", "CHANGELOG.md", *NOTICES):
        destination = source / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repository / name, destination)
    for name in ("src", "tests", "docs"):
        shutil.copytree(repository / name, source / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
    artifacts = temporary / "dist"
    # Default build produces the wheel FROM the sdist, exercising both formats.
    run(sys.executable, "-m", "build", "--no-isolation", "--outdir", artifacts, source, cwd=temporary)
    wheel, = artifacts.glob("*.whl")
    sdist, = artifacts.glob("*.tar.gz")
    with zipfile.ZipFile(wheel) as archive, tarfile.open(sdist) as source_archive:
        wheel_names = set(archive.namelist())
        source_members = {member.name: member for member in source_archive.getmembers()}
        prefix = sdist.name.removesuffix(".tar.gz") + "/"
        for name in PAYLOAD:
            packaged = "flutter_agent_guidelines/payload/" + name
            expected = (repository / "src" / packaged).read_bytes()
            assert archive.read(packaged) == expected
            assert source_archive.extractfile(prefix + "src/" + packaged).read() == expected
        actual_payload = {name.removeprefix("flutter_agent_guidelines/payload/")
                          for name in wheel_names if name.startswith("flutter_agent_guidelines/payload/")}
        assert actual_payload == set(PAYLOAD), actual_payload
        for name in ADAPTERS:
            packaged = "flutter_agent_guidelines/" + name
            expected = (repository / "src" / packaged).read_bytes()
            assert archive.read(packaged) == expected
            assert source_archive.extractfile(prefix + "src/" + packaged).read() == expected
        for name in NOTICES:
            destination, = [entry for entry in wheel_names if entry.endswith(".dist-info/licenses/" + name)]
            expected = (repository / name).read_bytes()
            assert archive.read(destination) == expected
            assert source_archive.extractfile(prefix + name).read() == expected
        assert all(not member.issym() and not member.islnk() for member in source_members.values())
        assert prefix + "docs/task-api.md" in source_members
        assert prefix + "docs/runtime.md" in source_members
        assert prefix + "docs/installed-mode.md" in source_members
        assert prefix + "tests/adapter_harness.mjs" in source_members
        assert prefix + "tests/installed_adapter_harness.mjs" in source_members
        assert not any("__pycache__" in name or name.startswith("tests/") for name in wheel_names)
    environment = temporary / "installed"
    venv.EnvBuilder(with_pip=True).create(environment)
    executable = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    cli = environment / ("Scripts/flutter-guidelines.exe" if os.name == "nt" else "bin/flutter-guidelines")
    run(executable, "-m", "pip", "install", "--no-deps", wheel, cwd=temporary)
    run(cli, "--help", cwd=temporary)
    run(executable, "-I", "-m", "unittest", "discover", "-s", source / "tests", "-v", cwd=temporary)
    for artifact in (wheel, sdist):
        print(f"SHA256 {artifact.name}: {hashlib.sha256(artifact.read_bytes()).hexdigest()}")
    print("PASS: wheel/sdist payload and notices exact; isolated installation and tests")


if __name__ == "__main__":
    main()
