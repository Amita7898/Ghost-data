"""Serve the built React UI and API on localhost; no model downloads."""

import argparse
import importlib.util
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description="Ghost Data local web application")
parser.add_argument(
    "--offline",
    action="store_true",
    help="Disable all live model access; genuine recorded demos remain available",
)
parser.add_argument("--port", type=int, default=8000)
parser.add_argument("--data-dir", type=Path, default=root / ".localdata")
args = parser.parse_args()
if not (root / "frontend/dist/index.html").exists():
    raise SystemExit(
        "Build the frontend first: npm ci --prefix frontend && npm run build --prefix frontend"
    )
if not 1 <= args.port <= 65535:
    raise SystemExit("Port must be between 1 and 65535.")
os.environ["GHOST_DATA_PROJECT"] = str(root)
os.environ["GHOST_DATA_DATA_DIR"] = str(args.data_dir.resolve())
os.environ["GHOST_DATA_OFFLINE"] = "1" if args.offline else "0"
sys.path.insert(0, str(root / "src"))
try:
    if importlib.util.find_spec("fastapi") is None:
        raise ImportError("fastapi")
    import uvicorn
except ImportError:
    raise SystemExit("Install web dependencies: python -m pip install -e '.[web,dev]'")
print(f"Ghost Data → http://127.0.0.1:{args.port}", flush=True)
print(
    "Recorded replay only; no model access."
    if args.offline
    else "Local inference enabled. Start Ollama separately for live runs.",
    flush=True,
)
uvicorn.run(
    "ghost_data.web.app:create_app",
    factory=True,
    host="127.0.0.1",
    port=args.port,
    workers=1,
)
