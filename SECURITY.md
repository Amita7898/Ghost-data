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
- Identity lookups require an authorized audit and return only the selected subject’s
  rows; a shared-alias ambiguity flag does not disclose another person’s history.
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
Experimental model questions have scope/citation checks, not semantic validation of
their premises. Do not treat their wording as evidence or permission to act.

Do not expose either local service through a tunnel, public bind or reverse proxy
without a separate authentication, authorization, rate-limit and deployment review.
Do not use real personal data in public screenshots, recordings or bug reports.
Private cases/events live in `.localdata/` or the configured private directory.
No automatic data-retention/deletion interface is provided yet.

## Dependency review

Recorded audit results are in machine-readable docs/*dependency-audit.json.
Current review checks and limitations are in docs/evaluation.md. Audit databases change; recheck before
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

The repository is public. Do not paste real evidence, secrets or private traces into
public issues. Use GitHub private vulnerability reporting if the repository Security
tab offers “Report a vulnerability”; otherwise contact the owner privately through
an existing trusted channel. Enabling that GitHub feature is recommended; this local
review does not change repository settings or invent a contact address.
