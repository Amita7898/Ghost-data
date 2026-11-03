# Final dependency review

The actual project package.json/package-lock.json were **not modified**. All
remediation experiments were outside the repository and are not publication assets.

## Current pinned tree — newly checked

The latest published openapi-typescript at review time was 7.13.0 and still requested
Redocly ^1.34.6. The actual lock resolves the affected development chain:
openapi-typescript → @redocly/openapi-core → minimatch. npm reports three moderate
entries for one underlying advisory, GHSA-g3hv-75wg-m249. Production npm audit and
pinned Python pip-audit found no known vulnerabilities in their scoped inventories.
These results are time-dependent and not an absence-of-vulnerabilities guarantee.

The advisory describes glob preprocessing resource amplification. This generator
is used only to produce TypeScript from the checked-in local OpenAPI schema; it is
not an application API endpoint or a browser-exposed parser. No user-uploaded schema
is sent to it by the running app. Do not extend it to untrusted input under the
current exception. The advisory's broad affected range remains authoritative for
this review; no unsupported false-positive dismissal or audit suppression is used.

## Actual scratch experiments

| Candidate | Audit result | Compatibility/result | Decision |
|---|---|---|---|
| Override Redocly to 2.72.1 | Zero known npm findings | API generation failed: ERR_PACKAGE_PATH_NOT_EXPORTED, missing exported ./lib/ref-utils.js. Build/component tests using pre-existing DTOs passed, which does not repair the failed generator | Reject; not a safe drop-in fix |
| npm-suggested openapi-typescript 6.7.6 downgrade | One moderate, two high npm entries via undici / @fastify/busboy | Generator ran, but the security inventory worsened | Reject; do not apply npm audit fix --force |

A metadata check of Redocly 2.7.0 also showed the restricted export map; it was not
installed/tested as a third candidate. Version 2.6.1 was not published. No claims
of compatibility are made for untested combinations.

## Recommendation

No safe drop-in remediation was established by these checks. Keep the current
pinned 7.13.0-compatible tree only if the owner accepts the documented development
risk; otherwise postpone publication until a compatible upstream fix or reviewed
replacement is validated. Do not apply a major override/downgrade without approval.

A future maintained generator release that supports modern Redocly, or a reviewed
build-tool replacement, should be tested by actual regeneration, API semantic diff,
TypeScript build, frontend tests, browser workflows and a fresh advisory audit. A
clean npm audit alone is insufficient, as the failed override demonstrates.

Raw refreshed current-tree reports are saved alongside this file. Experiment
summaries describe scratch results; rejected dependencies are not in the project.
CI currently blocks production advisories and high/critical full-tree entries while
leaving the known moderate development chain visible for review.

Source: [GitHub advisory](https://github.com/advisories/GHSA-g3hv-75wg-m249).
