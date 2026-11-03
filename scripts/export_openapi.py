"""Generate the API contract without starting a server or loading a model."""

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))
from ghost_data.web.app import create_app

with TemporaryDirectory() as directory:
    app = create_app(root, Path(directory), offline=True)
    (root / "docs/openapi.json").write_text(json.dumps(app.openapi(), indent=2) + "\n")
    app.state.service.shutdown()
print("Wrote docs/openapi.json")
