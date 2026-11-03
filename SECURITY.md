# Security boundaries

Ghost Data is a **single-user, localhost-only demonstration application**. It is
not a certified compliance service or a hardened public deployment. Keep the API
and Ollama bound to loopback. There is no multi-user authentication.

## What the controls do

- API host/origin checks restrict browser access and reject non-local hostnames.
- Evidence upload accepts bounded schema-validated JSON only (5 MB), stores opaque
  server-generated filenames, and rejects paths, unsupported formats and duplicates
  in JSON keys. Registered bytes are hash-checked before use; symlinks are rejected.
- Previews are text; untrusted strings are not rendered as HTML. Source locators
  resolve only registered sections/rows. Report exports escape untrusted Markdown.
- Six scoped read-only agent tools cannot run arbitrary shell/SQL, inspect arbitrary
  files, call cloud providers, authorize deletion or change policy. Runtime redirects
  and remote-model configurations are rejected.
- Model hypotheses require supported citations/source contracts. Shared evidence
  admission checks timestamps/availability, identity, scope and coverage; the policy
  kernel and independently implemented proof checks retain conclusion authority.
- Execution budgets, single-run admission, idempotency, persistent events and atomic
  cancellation keep execution status distinct from a validated audit conclusion.

## What they do not establish

A trusted local process can still access application storage. This is not an OS
sandbox, source-authentication service or cryptographic attestation. Declared
inventory completeness and source authenticity are assumptions. Missing evidence
never proves absence. A hash proves consistency with registered bytes, not truth.
Passing a few injection tests is not evidence of general prompt-injection immunity.

Do not expose either local service through a tunnel, public bind or reverse proxy
without a separate authentication, authorization, rate-limit and deployment review.
Do not use real personal data in public screenshots, recordings or bug reports.
Private cases/events live in `.localdata/` or the configured private directory.
No automatic data-retention/deletion interface is provided yet.

## Dependency review

Current measured audit results and their scope are in docs/release-readiness.md and
machine-readable docs/*dependency-audit.json. Audit databases change; recheck before
publishing and periodically afterward.

The three moderate npm entries are one underlying advisory chain:
openapi-typescript → @redocly/openapi-core → minimatch
([GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249)).
It concerns glob-pattern resource amplification. The generator is a development
command for the checked-in local OpenAPI contract, not a browser/runtime endpoint.
Production frontend dependencies have no known advisories in the recorded audit;
pinned Python dependencies also have none in the recorded pip-audit result.

Residual development risk is documented, not hidden. Do not generate types from
untrusted remote schemas/patterns. No audit exclusion or forced incompatible major
version override is applied. The published current generator still depends on the
affected Redocly range; its old minimatch API cannot safely be assumed compatible
with a forced major upgrade. Prefer an upstream compatible generator release, then
regenerate/types/build/browser-test it. If untrusted schema generation becomes a
requirement, isolate or replace that build tool before enabling it.

## Reporting an issue

Do not paste real evidence, secrets or private traces into public issues. Until a
repository and private vulnerability-reporting channel are approved, report concerns
privately to the project owner. After publication, enable GitHub private vulnerability
reporting and document the approved contact. No email address is invented here.
