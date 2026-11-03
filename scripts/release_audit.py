"""Read-only publication-candidate and reachable Git-history checks.

Reports paths and rule names, never matched credential values. This is a scoped
pattern/inventory review, not proof that no personal data or secrets exist.
"""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {
    "dataset",
    ".venv",
    "node_modules",
    ".localdata",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "private",
    "uploads",
}
NAMES = {
    "log.txt",
    "chat_transcript",
    "agent-trace.zip",
    "code.zip",
    "output.csv",
    ".env",
}
PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "api_token": re.compile(r"\bsk-[A-Za-z0-9_-]{32,}|\bgh[pousr]_[A-Za-z0-9]{30,}"),
    "machine_home_path": re.compile(
        r"/(?:Users|home)/[^/\s]+/|[A-Z]:\\Users\\[^\\\s]+\\"
    ),
}


def inspect(path, raw):
    p = Path(path)
    findings = []
    if (
        any(part in FORBIDDEN for part in p.parts)
        or p.name in NAMES
        or p.suffix in (".sqlite", ".db", ".pyc", ".zip")
        or (p.name.startswith(".env.") and p.name != ".env.example")
    ):
        findings.append({"path": path, "rule": "excluded_publication_path"})
    if b"\0" not in raw[:4096]:
        text = raw.decode("utf-8", errors="replace")
        for name, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append({"path": path, "rule": name})
    return findings


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def audit(root=ROOT):
    candidates = sorted(
        set(
            git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
            .decode()
            .split("\0")
        )
        - {""}
    )
    findings, manifest = [], []
    for name in candidates:
        p = root / name
        if not p.is_file():
            findings.append({"path": name, "rule": "missing_candidate"})
            continue
        if p.is_symlink():
            findings.append({"path": name, "rule": "symlink_candidate"})
            continue
        raw = p.read_bytes()
        findings += inspect(name, raw)
        manifest.append({"path": name, "sha256": hashlib.sha256(raw).hexdigest()})
    history_findings, seen = [], set()
    for line in git(root, "rev-list", "--objects", "--all").decode().splitlines():
        oid, _, name = line.partition(" ")
        if (
            not name
            or oid in seen
            or git(root, "cat-file", "-t", oid).strip() != b"blob"
        ):
            continue
        seen.add(oid)
        for finding in inspect(name, git(root, "cat-file", "blob", oid)):
            history_findings.append({**finding, "object": oid})
    return {
        "candidate_files": len(manifest),
        "history_blobs": len(seen),
        "working_tree_findings": findings,
        "history_findings": history_findings,
        "passed": not findings and not history_findings,
        "scope": "Git-selected publication candidates and all reachable history; ignores untracked private data, cannot establish legal rights or exhaustive PII absence",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit()
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
