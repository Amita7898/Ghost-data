# GitHub presentation and release plan

Nothing in this document creates a repository, remote, tag or release.

| Field | Recommendation |
|---|---|
| Repository | `amita7898/ghost-data` (proposed; no publication authorization) |
| Description | An AI-powered data deletion auditing platform with local LLM agents, evidence verification, and an interactive investigation workspace. |
| First public tag | `v0.4.0`, matching current application metadata; not created |
| Topics | `agentic-ai`, `llm`, `python`, `react`, `fastapi`, `ollama`, `privacy`, `full-stack` |
| License | MIT, only after explicit owner approval and copyright details |
| Demo | README GIF plus `docs/demo.md`; actual synthetic recording walkthrough |
| Main image | `docs/screenshots/workspace-desktop.png` |
| Social image | Owner may choose a cropped synthetic workspace screenshot; none uploaded |
| CI | `.github/workflows/tests.yml`; link actual run only after publication |

README order: purpose → genuine demo → model-free quickstart → implemented features
→ architecture/workflow → optional inference → measured comparisons → tests/screenshots
→ limits and licensing. Keep detailed setup/security/performance in linked documents.
No stars, badges, hosted URL or CI success is fabricated for an unpublished repository.

## Accurate resume highlights

- Built a React/TypeScript and FastAPI investigation console with SQLite persistence,
  reconnectable SSE progress, idempotent run starts and cooperative cancellation.
- Integrated a genuine local tool-calling LLM with six read-only tools, provenance
  checks, structured hypotheses and independently validated policy conclusions.
- Designed synthetic evidence/oracle separation and safety regressions for authorization,
  historical identities, incomplete snapshots and temporal availability; documented
  narrow benchmark gains alongside model failures and inference costs.

Use actual test counts from release-readiness.md at the time of applying. Do not
claim production certification, a universal deletion guarantee, broad model accuracy
or that this agent outperformed single extraction overall.

## Bounded roadmap

1. Broaden held-out evidence templates/languages and measure recall, abstention and
   unsupported conclusions; profile context redundancy and latency.
2. Add reviewed read-only connectors and richer source contracts, with fake/test
   services first, provenance, availability rules and independent validation.
3. Improve evidence/relationship exploration and user-controlled storage retention.
4. Add PDF/OCR only with quality gates and uncertainty tests.
5. Consider hosted/multi-user use only after authentication, authorization, tenant
   isolation, quotas, migrations and a deployment security review.

No multi-agent framework, distributed queue or cloud service is justified by the
current measurements. These are future ideas, not implemented capabilities.

## Owner decisions before publication

- Confirm rights/participation terms for independently authored source and synthetic assets.
- Approve MIT (or choose another license) and specify the copyright holder.
- Approve the repository name/description/topics, chosen account and initial version.
- Accept or require remediation of the documented development-only advisory chain.
- Explicitly authorize creation/publication/push; preparation alone does not authorize it.

After approval: apply the chosen license, rerun publication/dependency audits, review
the exact staged file list and diff, commit the release changes, create the approved
remote and push. Then verify a real GitHub Actions run before claiming remote CI
success. Keep `.localdata`, private transcripts and model weights local.

The owner supplied GitHub username amita7898 for the proposed repository. This is metadata, not publication approval. See github-publication-plan.md for the exact gated commands.

## Publication authorization

The owner subsequently approved public amita7898/ghost-data, MIT with the holder
specified in LICENSE, v0.4.0, and the documented moderate development advisories.
The publication workflow still requires final scans and successful remote CI before
creating the approved release. The earlier unchecked decisions above are historical.
