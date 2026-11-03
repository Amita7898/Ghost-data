# Final GitHub pre-publication review

> Historical review captured before the owner subsequently approved MIT and publication. See LICENSE and the current README; test and scan results below remain historical facts.
Target: **amita7898/ghost-data**. Review date: 2026-11-03.
Decision: **ready for owner review; publication remains NO-GO until explicit approvals**.
No repository creation, push, visibility change, tag, release, license application,
application-code change or real dependency update was performed in this review.

## Newly executed versus historical evidence

| Area | Newly executed during this review | Earlier results (not relabeled as new) |
|---|---|---|
| Python | All **206 passed**, including actual local-model smoke; 16.60 s, one upstream TestClient warning | M5 206 passed in 18.72 s |
| Installation | Fresh review source, fresh .venv, pinned requirements + editable install; npm ci into absent node_modules, build from source; setup diagnostics passed | M5 additionally disabled reuse of pip/npm package caches |
| Frontend | **8 tests passed**, TypeScript/Vite production build passed | M5 same counts |
| Offline full-stack | **5 real Chrome workflows passed**, model test skipped in offline suite; actual API, source/history/export/reload/upload/mobile/accessibility/error/rejection checks | M5 same workflows passed |
| SQLite | **4 investigations / 3 runs persisted across actual API process restart** | Existing API persistence/recovery/cancellation tests retained |
| Live Ollama | **1 actual live Chrome workflow passed**, including reload/SSE and a second run's cancellation | M4 genuine live browser run also retained |
| Live measurement | **187.869 s**, 5 model calls / 5 tools, 8,130 input + 443 output tokens; NON_COMPLIANT | M4 completed run 162.439 s; no claim of latency improvement |
| Cancellation | **3.784 s**, 1 real call, 1,132 input + 14 output tokens, 0 tools, CANCELLED | M4 separate cancellation 4.651 s |
| Media | Current GIF/source hashes verified; conflict copy byte-identical to original final trace | GIF/screenshots captured in M4/M5, not newly filmed in this review |
| Benchmark accuracy | Documentation/raw-measurement consistency reviewed; **not rerun** | Structured 32/128/512 controlled suites 100% after hardening; four-note diagnostic 25% / 75% / 75% kernel/extraction/agent |
| Remote CI | Not run; no publication/account changes | CI configured, never claimed as remote success |

These installations used a clean project/dependency environment on the same Mac,
not a fresh OS or a native Windows/Linux validation. New installs could use package
caches; only M5's no-cache claim applies to that earlier run. Live inputs are
independently authored synthetic examples; no expected answers enter runtime tools.
Paid local runtime API cost was $0; electricity/hardware and coding-assistant usage
were not measured. Raw new run measurements: live-validation.json.

## Repository and provenance findings

The standalone Git root is separate from the original competition checkout.
Original code.zip, output.csv and agent-trace.zip remain in that separate original
folder, not publication candidates. An exact-byte comparison of publication files
against original dataset files, problem text and submission artifacts found **no
matches**. This checks whole-file duplication, not every possible copied fragment
or legal right. Original submission files and private session traces were not edited.

Current candidate/history scan found no excluded paths, symlinks, secret-pattern or
machine-home-path matches. Additional read-only patterns for AWS keys, fine-grained
GitHub tokens, Google keys, Slack tokens, JWT-like values and quoted credential
assignments also found no matches. Historical email-like values were fictional
example.test addresses. Stored checkpoint author metadata uses Codex/local.invalid,
not a personal email. Public commit/tag identity still needs owner approval.

The two reachable standalone checkpoint commits were inspected; 222 historical blobs
were scanned. git fsck was clean with no dangling-object output. No object alternates
or existing remote is configured. Observed findings do not require a clean-history
replacement. If new sensitive material is discovered later, stop and prepare a clean
publication export/history; .gitignore cannot remove leaked historical content.

The exact current candidate path/hash snapshot is files.txt/files.json. Findings
and candidate count are recorded in audit.json at audit time. Private .localdata,
.venv, model weights, node_modules, browser failure traces, caches and private chat
records are ignored and are not in the snapshot. This is a scoped review, not an
exhaustive proof of no PII/secrets or of source ownership.

Source reuse rights need owner confirmation for independent authorship/contributions
and applicable participation/employment terms. Public challenge material inspected
provides no broad redistribution grant for its assets; those assets remain excluded.
Private agreements were unavailable. Do not interpret passing a scan as legal clearance.

## Dependency decision

The unchanged actual tree still reports **3 moderate development entries**, one
minimatch/Redocly/type-generator chain. Production npm and pinned Python audit newly
reported **no known vulnerabilities**. See the raw current reports and
[dependency-review.md](dependency-review.md) for actual scratch experiments:

- Redocly 2.72.1 override: clean audit, **broken type generation**.
- Suggested generator 6.7.6 downgrade: generator runs, but **2 high + 1 moderate entries**.

Neither candidate was applied. No safe drop-in fix was established. Recommend the
current pinned generator only for trusted local schemas, subject to owner acceptance;
otherwise wait for a compatible upstream release or approve a reviewed replacement.
The running application does not invoke the generator for user uploads.

## License recommendation and presentation

Recommend **MIT** for the original application if ownership/reuse rights are clear.
Apache-2.0 adds explicit contributor patent terms and more redistribution/notice
requirements; it is appropriate if that is a project priority. Dependencies retain
their own licenses; no model/runtime binaries are redistributed. Neither choice
fixes unclear provenance. [Comparison and primary sources](license-comparison.md).
No license/copyright holder has been added.

The README has a genuine 15-second recorded demo, source inspection/rejection
walkthrough, architecture diagram, technical features, reproducible offline setup,
optional inference, tests/CI status, honest comparisons and explicit limits.
Benchmark coverage is narrow/shared-template; model abstention and complementary
extraction errors are disclosed. The UI is localhost-only and not a certified
compliance service. No model-free mode is mislabeled live.

Exact requested metadata, draft v0.4.0 notes, reviewed history and gated publication
commands are in [github-publication-plan.md](../github-publication-plan.md).
The proposed address is https://github.com/amita7898/ghost-data; no existence,
availability or authenticated ownership check is asserted. GitHub CLI was not
installed and account authentication was not attempted.

## Approvals still needed

1. Confirm source/contribution rights and applicable participation terms.
2. Choose MIT or Apache-2.0 and confirm the public copyright-holder identity.
3. Accept the documented moderate development-only risk, or require remediation.
4. Approve the final candidate manifest plus the explicitly approved LICENSE addition,
   public commit/tag no-reply identity, metadata and v0.4.0 notes.
5. Explicitly authorize creation of **public amita7898/ghost-data**, pushing main,
   and (separately or together) the proposed tag/release. Username alone is not consent.

Before external actions, recheck advisories, regenerate the final manifest after any
license/dependency changes, inspect staged files and the actual release commit, and
verify account/remote identity. Push only reviewed main/tag refs, never --mirror or
force-push. Inspect actual remote CI after publication before claiming success.
