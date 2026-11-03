"""Read-only setup diagnostics. Offline checks never contact Ollama."""

import argparse
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def checks(root=ROOT):
    results = [("Python 3.11+", sys.version_info >= (3, 11), sys.version.split()[0])]
    for name in ("pydantic", "fastapi", "uvicorn"):
        try:
            version = importlib.metadata.version(name)
            results.append((name, True, version))
        except importlib.metadata.PackageNotFoundError:
            results.append(
                (
                    name,
                    False,
                    "Install: python -m pip install -r requirements-web-tested.txt",
                )
            )
    built = (root / "frontend/dist/index.html").is_file()
    results.append(
        (
            "Production UI",
            built,
            "ready"
            if built
            else "Run npm ci --prefix frontend && npm run build --prefix frontend",
        )
    )
    for name in ("node", "npm"):
        binary = shutil.which(name)
        if binary:
            result = subprocess.run(
                [binary, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            detail = result.stdout.strip() or "Version check failed"
            ok = result.returncode == 0
            if name == "node" and ok:
                ok = int(detail.lstrip("v").split(".")[0]) >= 22
                if not ok:
                    detail += " — use Node 22+ to build"
        else:
            ok, detail = False, "Needed to build the UI; install Node 22+"
        results.append((name + " (build tool)", ok or built, detail))
    try:
        hashes = json.loads((root / "demo/RECORDING_SHA256.json").read_text())
        for name in (
            "receipt-absent-v4-live.json",
            "remaining-replica-v3-live.json",
            "conflicting-readbacks-live.json",
        ):
            expected = hashes["demo/" + name]
            actual = hashlib.sha256((root / "demo" / name).read_bytes()).hexdigest()
            results.append(
                (
                    "Recording " + name,
                    actual == expected,
                    "integrity verified"
                    if actual == expected
                    else "Restore recording from the repository",
                )
            )
    except (OSError, ValueError, KeyError, TypeError):
        results.append(
            ("Demo recordings", False, "Restore demo files and RECORDING_SHA256.json")
        )
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Explicit offline check (default; never contacts Ollama)",
    )
    parser.parse_args()
    results = checks()
    for name, ok, detail in results:
        print(f"{'OK' if ok else 'MISSING'} · {name}: {detail}")
    print("No model queries or downloads performed. Live readiness: ghost-data doctor")
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
