# Setup and diagnostics

Run the README quickstart from a fresh checkout. Dependency installation requires
network access; subsequent offline replay does not require an AI service. Source repository: https://github.com/amita7898/ghost-data.

The pinned Python environment is in requirements-web-tested.txt; the exact npm
resolution is frontend/package-lock.json (`npm ci`, not a floating fresh install).
Python 3.14/macOS arm64 and Node 25 were tested locally; the CI matrix additionally
targets Python 3.12/Node 22. Native Windows execution remains untested. Use a current
Node 22 release (22.12+) or newer supported LTS release.

After installation/build, `python scripts/check_setup.py --offline` checks package
availability, build tools, frontend assets and all three curated recording hashes. It never
queries Ollama, installs dependencies or downloads a model. It reports missing
items with the corresponding setup command.

| Symptom | Action |
|---|---|
| Missing fastapi/uvicorn/build backend | Activate .venv, install pinned requirements, then editable project as in README |
| “Build the frontend first” | `npm ci --prefix frontend` then `npm run build --prefix frontend` |
| Port 8000 in use | Stop your earlier server or use `python scripts/start.py --offline --port 8001`; open that exact port |
| Replay recording/input integrity failure | Restore original demo/examples/checksum files from the reviewed checkout; do not edit traces to force success |
| Backend unavailable | Check the Python server terminal and URL; a model service cannot replace the backend |
| Model unavailable in offline mode | Expected. Choose a recorded demo; live starts are intentionally disabled |
| Database already owned by another backend | Use one backend per data directory, or choose another private `--data-dir` |
| Failed/interrupted/cancelled run | Review actual saved events and retry explicitly; execution does not silently resume |

Default application storage is `.localdata/`, ignored by Git. To keep sensitive
investigations elsewhere use `--data-dir` with a directory you control. There is no
data-deletion UI yet. Do not publish databases or browser traces of private cases.

## Live local inference

Install the official runtime from [Ollama](https://ollama.com/download). Read the
current model card, license, download size and hardware requirements before
explicitly downloading weights. No model pull is run by the application.

The measured model tag is `qwen3.5:latest`; the recorded digest is
`6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`.
A mutable tag is not a reproducibility guarantee. `ghost-data doctor` displays
actual runtime/model details and rejects remote models or models without tools.
The recorded model is 9.7B Q4_K_M (~6.6 GB assets). Tests used Apple M3, 16 GiB
unified RAM and 16,384 context; measured runner RSS was ~6.45 GiB, a snapshot rather
than a guaranteed peak. Allow memory for the OS, context, browser and other apps.

On macOS/Linux, `sh scripts/serve-local.sh` binds Ollama to 127.0.0.1:11434 with
cloud disabled and one inference slot. If Ollama is already serving, do not start a
second copy. On Windows set OLLAMA_NO_CLOUD=1, OLLAMA_HOST=127.0.0.1:11434,
OLLAMA_NUM_PARALLEL=1 and OLLAMA_MAX_LOADED_MODELS=1 before `ollama serve`.
Windows instructions have not been executed natively.

Run `ghost-data doctor`, then start the web app without --offline. Do not run CLI
inference concurrently with web investigations; the API gate cannot coordinate
independent clients. The in-flight call may take up to 120 seconds to return during
cancellation. No automatic model-call retry occurs after an uncertain timeout.

Legacy CLI remains available:

```sh
ghost-data examples/remaining_replica.json
ghost-data investigate examples/prose_receipt.json --agent local --trace /tmp/audit.json
ghost-data replay demo/receipt-absent-v4-live.json
```

On Windows choose a writable local trace path instead of /tmp. All examples are
fictional. Model weights and runtime binaries are not redistributed here.
