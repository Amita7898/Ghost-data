# Milestone 5 — publication readiness

> Historical review captured before the owner subsequently approved MIT and publication. See LICENSE and the current README; test and scan results below remain historical facts.
**Prepared for owner review. Publication is not authorized yet.** No public repository,
remote, release tag, license application or push was performed.

## Checkpoint and preservation

Safe local checkpoint: `1c780bc` (Milestone 4). Application metadata remains 0.4.0;
recommended first public tag is v0.4.0, not created. Existing kernel, agent,
benchmark source and all existing Python test files remain unchanged. The only
existing Python runtime change is an entry in the fixed replay registry for a
byte-identical genuine conflict recording. Original traces remain untouched.

## Changes made

- Reworked README around a two-minute overview, genuine demo, model-free quickstart,
  architecture, honest benchmark comparison, tests, limits and license status.
- Added setup/diagnostics, performance, demo, security, provenance/licensing and
  publication metadata/roadmap guidance; updated stale agent/benchmark documentation.
- Fixed backend-unavailable status presentation and source-dialog initial keyboard
  focus; improved measured low-contrast sidebar/evidence metadata. No engine rewrite.
- Curated an existing genuine final conflict trace and paired visible input, preserving
  their bytes/hashes. It exposes two rejected hypotheses and an inconclusive result.
- Added setup and publication-candidate/history audit helpers, six Python helper/replay
  tests, a frontend focus regression, and browser accessibility/error/rejection checks.
- Strengthened CI with Python 3.12/3.14, locked installs, production advisory gate,
  high-severity full npm gate, Python audit, API contract drift check, explicit startup
  failure/cleanup and offline browser tests. No remote CI success is claimed.

## Actual executed checks

| Check | Result |
|---|---|
| Fresh Python environment / no-cache pinned install / editable package | Passed |
| Fresh source import check | Confirmed source from the clean checkout |
| Final installed Python suite, actual-model smoke enabled | **206 passed** (18.72 s); one upstream deprecation warning |
| Clean Python suite (offline default) | **205 passed, 1 skipped**; upstream TestClient deprecation warning |
| Clean npm cache / npm ci / production build | Passed |
| Frontend Vitest / React Testing Library | **8 passed** |
| Fresh-install Chrome E2E | **5 passed, 1 skipped** (real-inference test intentionally opt-in) |
| Setup diagnostics | Passed; three curated recording hashes, no model queries |
| OpenAPI and TypeScript regeneration | Byte-identical to current contract |
| New helper lint | Passed |
| Published GitHub Actions | Not run; repository not published |

The clean install began without an environment, node_modules, production assets,
application database or reused package caches. Actual OS/browser were this Mac,
Python 3.14.0, Node 25.8.1, npm 11.19.1 and installed Chrome. This is not a claim of
fresh-OS, Linux or native Windows verification; those CI/platform paths remain pending.
The final opt-in model smoke test passed; see release-validation.json. M4's genuine full live browser test and actual 162.4-second run are
retained in web-live-validation.json; M5 does not claim a new latency benchmark.

Accessibility checks exercised dashboard, new form, workspace, evidence explorer,
history, mobile history and source modal using axe WCAG2A/AA/2.1AA tags, plus focus
trap/Escape/return. They found low-contrast text in sidebar and evidence metadata;
those were fixed and rerun. A new diagnostic regression also caught a missing third
recording check after curation; it was corrected and rerun. No failures were hidden
by removing assertions. Automated checks do not establish full WCAG conformance.

## Authentic media

`docs/demo/ghost-data-replay.gif`: six actual browser captures, 15 seconds, 532,428
bytes. It uses actual synthetic recorded events, including accepted and rejected
hypotheses; replay labels remain visible. It is not a real-time inference recording.
Source hashes, frame descriptions and GIF hash: docs/demo/capture.json. Capture and
encoding scripts are included; no original recording was edited. Browser screenshots
remain under docs/screenshots; the demonstration guide explains capture and limits.

## Security and dependency review

- Publication-candidate and reachable-history pattern scan: no findings. Two local
  checkpoint commits, 222 historical blobs reviewed; git fsck returned clean, with no
  dangling-object output. Candidate file count is reported at audit time in
  publication-audit.json. Metadata uses a local placeholder author; no remote exists.
- Email-like strings in historical blobs used only reserved example.test domains.
  Synthetic screenshots were visually checked; no OS/account chrome is included.
- No competition dataset, original statement/starter, submission ZIP/CSV, private
  transcript, keys, model weights, environment cache or runtime database is selected
  for publication. Local .localdata and .venv remain ignored and preserved.
- Scanning is scoped pattern/inventory review, not proof of exhaustive PII/secrets
  absence or legal clearance. Source authenticity and inventory scope remain assumptions.
- pip-audit of pinned web requirements: **no known vulnerabilities**.
- npm production audit: **no known vulnerabilities**.
- Full npm audit: **three moderate entries**, one development-only chain through
  openapi-typescript / Redocly / minimatch, GHSA-g3hv-75wg-m249. Raw audit JSON retained.
  No audit suppression or forced incompatible major override was applied. Its current
  use is generation from a trusted local schema, outside the running application.
  Prefer a compatible upstream update; do not accept untrusted schema/pattern input.
  CI fails production advisories and high/critical full-tree findings; moderate
  development findings remain visible for review. Owner acceptance/remediation is
  an explicit release decision, not a zero-risk claim. See SECURITY.md.

Existing API tests cover paths/file size/media type, duplicate JSON keys, integrity,
symlinks, forged client reports, temporal exclusion, origin/host checks, SSE cursor,
restart recovery, idempotency, cancellation races and offline runtime denial. Agent
prompt/source-contract tests remain unchanged. Tools stay read-only.

## Licensing, history and publication recommendation

No restricted material was found in reachable standalone history, so a replacement
history/repository is **not required by the observed findings**. Do not publish the
original competition checkout or copy its Git objects. If a later review uncovers
private material, prepare a clean export/history rather than relying on .gitignore.

MIT is recommended but **not applied**. The inspected public challenge material did
not establish redistribution rights for its assets; those remain excluded. Private
participation terms were unavailable. Owner must confirm rights for independently
authored source and approve a license/copyright holder before publication. See
provenance-and-licensing.md for sources and scope; no legal clearance is claimed.

## Owner checklist — remaining decisions

- [ ] Confirm rights/participation terms and intended copyright holder.
- [ ] Approve MIT or choose another license; no LICENSE currently exists.
- [ ] Accept or require remediation of documented development-only advisory risk.
- [ ] Approve ghost-data / description / topics / v0.4.0 and the intended GitHub account.
- [ ] Explicitly approve repository creation and push. No such action has been taken.
- [ ] After publication, inspect a real remote CI run and enable private vulnerability reporting.

**Recommendation:** ready for owner approval, not an automatic publication GO.
There are no failing local validation checks. Licensing/rights and explicit publication
permission remain gates; local-only safety and narrow evidence/model limitations are
intentional documented boundaries, not claims of production readiness.
