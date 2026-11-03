# Milestone 4 validation

## Implemented

A React/TypeScript/Vite/Tailwind application connected to a versioned FastAPI/Pydantic adapter, SQLite WAL storage, persistent SSE, and the existing bounded Ollama investigation controller. The three-panel workspace displays actual observable tool activity and validated hypotheses; model summaries are labeled unverified. Offline replay verifies and displays genuine saved M3 traces without calling the runtime.

New investigation creation supports validated JSON uploads (5 MB), embedded policy selection, explicit scope and exact UTC cutoff. Evidence sources retain SHA-256 identifiers and row pointers, original bytes, source previews and audit eligibility reasons. History preserves run input and report exports. There are no destructive agent tools or externally paid inference calls.

## Preservation

Git checkpoint: `98c2555` (Milestone 3). All 32 existing Python source/test files were byte-compared and are unchanged. The kernel, six agent tools, proof validator, synthetic generator, benchmark and CLI are reused. No competition data or private development transcript is copied into this standalone project. No remote publication was performed.

## Executed checks

- Python offline suite: **199 passed, 1 skipped** (the existing opt-in actual-model test); one upstream Starlette/httpx TestClient deprecation warning.
- Final installed-project suite with actual-model smoke enabled: **200 passed**, one upstream TestClient deprecation warning (12.10 seconds). This includes all 171 existing tests and 29 new API test cases.
- New web API suite: **29 passed**.
- Frontend Vitest/React Testing Library: **7 passed**.
- Clean `npm ci`, TypeScript and Vite production build: passed.
- Offline Chrome integration: **2 passed**, actual-model test intentionally skipped; replay/source navigation/report download/reload/mobile overflow and new-case upload validation exercised against a real API with `--offline`.
- Fresh virtual environment: installed built `ghost_data-0.4.0` wheel with pinned web dependencies successfully; web API import, existing CLI and genuine offline replay all worked.

- Actual live Chrome integration: **1 passed** (2.9 minutes): genuine inference, reload/SSE recovery, independently validated NON_COMPLIANT report, and cancellation of a separate real run.
- Completed run: **162.439 seconds, 5 model calls, 5 tool calls, 8,130 input / 443 output tokens**, 27 persisted events.
- Cancellation: **4.651 seconds**, one actual model call (1,132 input / 14 output tokens), cancelled status, zero completed tool calls; it was never labeled completed.
- Earlier live attempt completed the same investigation but failed a browser assertion that read the previous URL before navigation. Its second run was cancelled through the API. The test now explicitly waits for the new run URL. Both attempts remain in the measured run ledger; no failed test is presented as a pass.
- Local paid API cost: **$0**; electricity/hardware cost was not measured. Complete per-run accounting: `web-live-validation.json`.
- Source/security review: no high-confidence credential patterns or prohibited dataset/private transcript paths found. New Python adapter lint checks passed.

No benchmark accuracy improvement is claimed from adding the web adapter. All measurements are local observations, not general performance guarantees.

## Fixes verified during development

Replay position is not overwritten while the initial event list loads. Live events are scoped to the selected run and reconnect from persisted sequence numbers. Atomic cancellation wins against a concurrent completion; terminal and interrupted executions reject stale worker writes. Final status and its completion event commit together. Each data directory permits one backend owner and one active live run. Scope/cutoff configuration produces a new hashed input while preserving original evidence. Timestamp display is UTC and retains the exact cutoff unless explicitly edited. Host and agent events share an elapsed-time origin without rewriting original agent traces. Evidence bytes are bounded and hash-checked before parsing; changed files and symlinks are rejected. Exported untrusted strings are escaped for Markdown.

## Limitations and remaining release work

- JSON bundles only; no PDF, image OCR, arbitrary SQL/log connector or bundle merging.
- Localhost only; no multi-user authentication or suitability for public exposure. This is not an OS sandbox or independent source-authenticity attestation.
- One API inference slot. Separate CLI clients are not coordinated. An in-flight model call can take up to its timeout before cancellation settles.
- Backend restart preserves progress and marks an active run interrupted; model execution is not automatically resumed.
- Scope completeness and source authenticity remain explicit kernel assumptions. VERIFIED_WITHIN_SCOPE is not universal deletion proof. Human display labels do not grant identity ownership or deletion authorization.
- No production database migrations, retention-management UI or native Windows test. GitHub Actions is configured, not remotely executed.
- Dependency audit on 2026-11-03: **3 moderate development-tool advisories**, affecting `openapi-typescript` → `@redocly/openapi-core` → `minimatch` (GHSA-g3hv-75wg-m249). Production dependency audit has no known advisories. No forced major-version override was silently applied. Recheck before publication.
- One upstream TestClient deprecation warning remains. Local inference performance and a small integration test do not establish general accuracy or prompt-injection immunity.

See `web-architecture.md`, generated `openapi.json`, `web-live-validation.json` and actual screenshots. Milestone 4 adds UI/API observability; it does not claim to solve earlier model-reasoning limitations.
