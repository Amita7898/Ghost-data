# License comparison — no license applied

> Historical review captured before the owner subsequently approved MIT and publication. See LICENSE and the current README; test and scan results below remain historical facts.
Recommendation: **MIT for the original Ghost Data application**, after the owner
confirms reuse rights and the copyright holder. This is a source-portfolio release,
not distribution of Ollama binaries or Qwen weights.

| Topic | MIT | Apache-2.0 |
|---|---|---|
| Reuse | Permissive commercial/private modification and redistribution | Also permissive; explicit copyright and contributor patent grants |
| Patent treatment | No explicit patent-license section | Explicit contributor patent grant and patent-litigation termination |
| Redistribution | Preserve copyright/license notice | Include license; preserve applicable notices; mark modified files; carry applicable upstream NOTICE contents |
| Trademark | Does not grant a trademark license explicitly | Explicitly excludes trademark rights except limited attribution use |
| Warranty | Warranty/liability disclaimer | Warranty/liability disclaimer, additional contribution terms |
| Practical fit | Concise, easy for portfolio reuse and study | Prefer if explicit patent terms/contributor framework are a priority |

Neither license creates rights to third-party code or competition assets that the
owner does not possess. Neither licenses independent package dependencies or model
weights on the application's behalf. Both require respecting upstream terms when
redistributing upstream material. A license choice cannot substitute for provenance.

Observed package metadata includes FastAPI/Pydantic MIT, Starlette/Uvicorn BSD-3-Clause,
and OpenTelemetry API Apache-2.0. These are dependencies installed separately, not
source copied into the application. An Apache-licensed dependency does not, by its
presence alone, require the original application to be Apache-licensed. Preserve
upstream notices when distributing bundled third-party code/builds; a packaged
binary/model release would need an additional distribution-specific review.

MIT is recommended because the intended use is a readable, reusable personal
engineering portfolio, with no stated patent-governance requirement. Apache-2.0
is equally reasonable if the owner specifically values its explicit patent terms.
No LICENSE, NOTICE, SPDX application license or copyright holder has been added.

Owner confirmation still needed: authorship/authority over original code and any
third-party contributions; applicable participation/employment terms; chosen license;
public copyright-holder identity. The public challenge root showed no broad reuse
license; restricted challenge assets remain excluded. Private agreements were not
available for this review, so no legal clearance is asserted.

Primary sources reviewed:
- [MIT text and guidance](https://choosealicense.com/licenses/mit/)
- [Apache License 2.0, sections 2–4, 6–9](https://www.apache.org/licenses/LICENSE-2.0)
- [Original challenge repository](https://github.com/interviewstreet/hackerrank-orchestrate-october26)
