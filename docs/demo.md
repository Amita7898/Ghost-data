# A short, authentic demonstration

The README GIF is a 15-second accelerated navigation through the actual app, using
independently authored synthetic inputs and genuine saved Qwen tool calls. It is
**REPLAY**, not a live-speed claim or newly generated inference. No event text or
model hypotheses are invented. GIF color quantization is lossy; JSON recordings are
the underlying event source.

## Reviewer walkthrough (about one minute)

1. Start with `python scripts/start.py --offline` and open localhost:8000.
2. Choose **Prose receipt audit**. Pause or **Show all**; model-selected tools such
   as get_context, read_evidence and submit_hypothesis are actual recorded actions.
3. Find the accepted STATE hypothesis. Its quote and source locator—not the model's
   confidence—support the independently validated scoped result.
4. Select **Inspect supporting source**. Read the original note and SHA/row pointer;
   Escape closes the dialog and returns focus to the source control.
5. Open **Evidence** to inspect the observation inventory and audit eligibility.
6. Return to Overview and choose **Conflicting readbacks**. Its two genuinely
   rejected hypotheses remain visible; conflicting source states yield INCONCLUSIVE.
   Rejection is useful evidence of the boundary, not an error to erase.

The main receipt/replica recordings are from M3. The conflict recording is a
byte-identical curated copy of the existing final serialized comparison trace,
paired with its original visible input. Its hash and input hash are checked before
import. No evaluator-only file is presented to the runtime or replay as evidence.

## Reproduce media (optional developer task)

With dependencies installed, Chrome available, and the offline server running:

```sh
cd frontend
node scripts/capture-demo.mjs ../.demo-capture
cd ..
# Optional media tool only; not needed to run Ghost Data:
python -m pip install Pillow==11.3.0
python scripts/encode_demo.py .demo-capture docs/demo/ghost-data-replay.gif
```

GHOST_DATA_WEB_URL selects another local server URL for capture. Capture requires
that server to report offline mode, then exercises the real UI and saves six PNGs
plus a description/hash manifest. `docs/demo/capture.json` records the release
capture; intermediate PNGs are ignored. This writes new synthetic local history,
not the stored recordings. Existing recordings are never edited.

Screenshots from real browser tests are under docs/screenshots. Do not replace
synthetic inputs with personal data, private cases, terminal credentials or browser
account chrome when recording public media. Avoid claiming the GIF runs at actual
inference speed. Live timing and failures remain in performance.md.
