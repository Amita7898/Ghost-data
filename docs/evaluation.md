# Evaluation and reproducibility

Results below distinguish the current local review from historical release runs.
They are synthetic engineering probes, not compliance certification or production
accuracy. Full current measurements are summarized in `evaluation-results.json`;
private development traces and original competition materials are not included.

## Current structured regression

Unchanged seeds 42 / 2026 / 91827, with 32 / 128 / 512 cases respectively, were
regenerated and run three times against both v0.4.0 and the review implementation.
Both versions achieved 100% conclusion accuracy, zero unsupported verified, zero
incorrect noncompliant, 100% authorization accuracy and verification coverage, and
identical repeated outputs. Verification coverage is 57/57, 228/228 and 882/882
provable obligations; it does not measure undiscovered inventory.

The suites share scenario templates. Regeneration changes identifiers and dates,
not the evidence contract. No external or held-out production data was evaluated.
Timing includes local CPU contention from the serial model benchmark; sub-millisecond
differences are not an optimization claim.

## Authorization and retrieval probes

The independent 96-phrase intent corpus in `tests/fixtures/authorization.json` includes
supported deletion language, multilingual refusals, conditional intent, reported
commands, mixed scope and ambiguous requests. Runtime logic never reads this file.

| Metric | v0.4.0 | Review |
|---|---:|---:|
| Correct intent classifications | 50/96 (52.1%) | 96/96 (100%) |
| Incorrectly authorized non-authorizing phrases | 13 | 0 |

These examples were authored to expose regressions, not sampled as an unbiased
language dataset. Passing them does not establish unrestricted multilingual safety.
Audit authorization also does not authorize destructive execution.

A fixed twelve-query retrieval probe uses one eligible observation: five legitimate
identifier/system/resource/state queries, six metadata-key queries and one absent
term. Baseline precision is 5/11 (45.5%), review precision 5/5 (100%); recall remains
5/5. This isolates schema-key pollution, not general search relevance. Legitimate
business text containing “state” or “kind” is still searchable.

## Model evaluation

The historical published four-case run measured 25% deterministic, 75% extraction,
and 75% dynamic-agent conclusion accuracy, with median latencies 0.0003 / 25.93 /
148.75 seconds. Both model modes had zero unsupported verified conclusions. These
are historical measurements, not the current rerun.

The current comparison runs the same four visible receipt-note cases serially with
installed Qwen3.5, fixed generation settings, the original six-turn/240-second
comparison limits and no cloud service. Source labels are read only after inference.
It compares the unchanged v0.4.0 code with the review branch, including v5 advisory
questions. See `evaluation-results.json` for measured per-mode results, failures,
latency and reported token usage. One pass on four related
templates cannot establish agent superiority or statistical repeatability.



| Current rerun | Baseline correct | Review correct | Baseline / review median seconds |
|---|---:|---:|---:|
| Deterministic | 1/4 | 1/4 | 0.00078 / 0.00115 |
| Extraction | 3/4 | 3/4 | 27.84 / 28.04 |
| Dynamic agent | 3/4 | 4/4 | 190.72 / 178.58 |

Baseline agent: 3/4 executions completed, one inference timeout. Review agent: 4/4
completed. All modes/versions had zero unsupported verified conclusions; no oracle
NON_COMPLIANT mismatch occurred. The review recovered the supported injection-case
violation where baseline abstained. This one-run difference on four templates does
not establish a reproducible accuracy or latency gain. The extraction prompt is
unchanged. Agent token usage increased: 31,387 input + 1,876 output before versus
36,035 + 2,009 after; each comparison made 20 agent calls and four extraction calls.
Failed calls may have additional unreported usage. No advisory questions were emitted
under the default goal in these four runs; their practical benefit is not established.

The agent's influence is deliberately bounded: it can propose exact source-contract
interpretations and advisory follow-up questions. The initial deterministic audit
already handles structured facts. A conventional parser can handle this narrow
receipt grammar; broad document understanding is not claimed. Questions can be
useful without improving conclusion accuracy, and citation checks do not validate
a question's assumptions or answer it.

## Tests and integration

Baseline checks newly executed before editing: 207 Python tests passed, one optional
model test skipped; eight frontend tests passed and production build passed. The
five baseline browser workflows and Python 3.12 CI results were historical, not
rerun against the baseline in this local review.

Current checks: **377 passed, one opt-in skipped** on each installed Python 3.13 and
3.14; **10 frontend tests passed**. TypeScript/Prettier, Ruff and the production
build passed. Five offline browser workflows passed with scoped accessibility
checks; OpenAPI generation is byte-identical across those Python versions. An installed wheel was checked outside the source tree
for packaged v4/v5 prompts and deterministic audit execution. The pinned Python
3.13 environment was created fresh. Python 3.12 is not installed locally; its existing
CI matrix remains configured and has not run on these unpublished changes.

The default suite skips the opt-in real-model pytest smoke test. It was enabled
separately and passed (one actual Qwen tool-call test, 11.74 seconds). Five offline
browser workflows passed, including scoped accessibility checks. A separate actual
local-model browser workflow also passed: live events, browser reload, completed
investigation and subsequent cancellation. The successful investigation took 222.26 s,
five model calls/four tools and 8,140 input+426 output tokens. Cancellation took 3.99 s
with one model call, zero tools and 1,258 input+14 output tokens. Its available kernel
assessment remains labeled separately from the cancelled agent execution.

The final wheel was installed in the fresh pinned Python 3.13 environment, and the
full suite ran outside the source checkout with source import paths disabled:
377 passed, one skipped. Exact results and separate usage scopes are in the
measurement summary. FastAPI's test client emits a Starlette deprecation warning; it is not a
failed assertion and was not silenced by changing dependencies.

## Reproduce

See [benchmark methodology](benchmark.md) for architecture, metrics and runtime/oracle
isolation. Use a new directory for each command:

```sh
python -m ghost_data_bench.generate .localdata/suite-small --seed 42 --size small
python -m ghost_data_bench.run .localdata/suite-small --output .localdata/results-small --repeats 3
# Other suites: --seed 2026 --size medium; --seed 91827 --size large
python -m ghost_data_bench.local_agent benchmarks/agent-challenge --output .localdata/local-model-results
```

Generators and scoring are independent of runtime policy code. Only visible bytes
are passed to prediction; the oracle is loaded afterward. This is application-level
isolation, not an OS sandbox. Tests cover attempts to use missing, conflicting,
partial, late, misattributed and invalid evidence, and forged success reports.


## Final pre-release verification

The subsequent candidate check used **Python 3.12.16, 3.13.7 and 3.14.0**. Each
source suite passed **423 tests with one opt-in skip**. The final Python 3.12 wheel
also passed 423 tests/one skip outside the checkout with source imports disabled.
Ruff check/format, Python 3.12 syntax compilation, frontend lint, ten frontend tests,
production build and five offline browser/accessibility workflows passed. Python
3.12 regeneration exactly matched the reviewed OpenAPI and TypeScript DTO bytes;
HTTP 422 status and validation semantics were preserved.

The real local-model smoke passed separately. The Python 3.12 live-browser workflow
passed streaming, reload, completed investigation and cancellation. The completed
run took 205.94 seconds (five calls/four tools, 8,140 input +426 output tokens);
cancellation took 4.57 seconds (one call/zero tools, 1,258 input +14 output tokens).
These runs are separate from the earlier full-stack measurements above.

Additional consent-context probes found **23 false authorizations out of 24 new
non-authorizing phrases** in the prior candidate. Anchored supported English
requests, explicit negative-consent guards, reported/quoted wording, punctuation and
marketing-list handling reduce that count to **zero**, without changing the original
96 intent fixtures or previous expected results. Nine supported-request controls
also pass. Identity tools now reject non-authorizing requests and keep shared-alias
ambiguity from disclosing another subject's identity rows. Broader natural-language
understanding remains outside the grammar's assurance claims.

The unchanged 32/128/512 structured suites (three repetitions, same seeds and
manifest hashes) retain 100% conclusion/authorization accuracy and supported
verification coverage, with zero unsupported verified or false noncompliant outputs.
The earlier four-case model comparison was retained, not rerun or relabeled as this
pre-release evaluation.

### Advisory questions: explicitly experimental

Six targeted synthetic scenarios use one shared investigation goal and separate,
after-inference reference labels: missing readback, partial snapshot, missing field
inventory, conflicting readbacks, compliant control and refusal control. **Zero
questions were emitted**, including four missing-proof opportunities. Five runs
completed; the conflict run exhausted its 240-second budget. All six independently
computed conclusions matched supported expectations; this is not six completed agent
investigations or evidence that question generation works reliably.

The same 26 model-selected tool calls were replayed against the final safety code;
all tool results and reports were identical. Privacy and authority regressions also
cover foreign subject/resource citations, refusal, complete controls, untrusted
question premises and attempts to promote advisory text into proof. A grounded link
is not semantic validation: an invented premise can still be unverified model prose.
Generation remains **experimental and not meaningfully demonstrated**. No prompt was
retuned or question fabricated to turn this result into a success.

Reproduce the probe with the installed local model and a new destination:

```sh
python -m ghost_data_bench.advisory benchmarks/advisory --output .localdata/advisory-probe
```

Its six-turn/240-second limits allow 768 output tokens; normal agent output is 512.
Raw failures and counters are retained privately; public summarized measurements are
under `prerelease_verification` in evaluation-results.json. The probe made 30 model
requests; failed calls may consume unreported tokens. Local API charges were zero;
hardware, electricity and coding-assistant costs were not measured.

Fresh audits show zero known pinned-Python and frontend-production advisories, plus
the same three accepted moderate development-only entries. The TestClient warning
is unchanged. GitHub Actions has not run on this unpublished candidate; no remote-CI
success or release approval is inferred from local checks.

## Artifact retention

Keep `benchmarks/representative` (32-case reference suite), `benchmarks/agent-challenge`
(four reproducible prose cases), and `benchmarks/local-agent-final-results` (published
historical comparison). Keep the three curated demo recordings, original example
bytes and checksum manifest; offline playback depends on them.

Historical structured reports, unsuccessful prototype comparisons, publication
checklists, milestone snapshots and unused root prompt/schema exports were removed
from the current tree after reference checks. A private local archive with hashes
preserves them. The unchanged v0.4.0 Git history also permits exact recovery:

```sh
git show v0.4.0:docs/milestone-21-comparison.json > recovered-comparison.json
git show v0.4.0:benchmarks/hardening-large/results.json > recovered-large-results.json
```

This removes 65 redundant current-tree files (8,836,664 bytes before new summaries),
not their public history. No Git history rewrite, GitHub upload or release-asset
publication was performed. A future release may attach historical reports after
review; until then Git retains them.

## Limits and next experiments

The source authenticity and declared scope assumptions remain. No PDF/OCR, live
connector, authenticated confirmation flow or general semantic relationship resolver
has been added. Model latency/timeouts and conservative abstention remain practical
limits. Local API charges are zero; electricity, hardware and coding-assistant costs
are unmeasured. Failed calls may consume compute without reported token counters.

Use held-out prose templates, more languages, repeated model runs and explicit human
review of advisory-question usefulness before expanding claims. No model-led
authorization, unsupported success assumption or weakened verifier is acceptable.
