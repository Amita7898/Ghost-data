# Changelog

## Unreleased — proposed v0.5.0

- Preserve tool activity, hypotheses, usage and proof errors when independent
  verification fails; withhold the audit report and show a terminal failure state
  across API, SQLite, SSE, replay and React. Proof failure takes precedence over a
  racing cancellation rather than being hidden by it.
- Broaden conservative first-person deletion grammar; remove exact French/Portuguese
  sentence exceptions. Add multilingual, refusal, conditional and reported-speech
  regressions. Ambiguous intent remains non-authorizing.
- Reject negative-consent statements, quoted/reported commands, bare questions and
  marketing-list opt-outs without weakening genuine deletion-request tests.
- Keep identity lookups within authorized subject scope, including shared aliases.
- Mark advisory generation experimental; add six missing-proof/control fixtures and
  a reproducible local-model probe that retains budget failures.
- Search evidence values instead of JSON keys. Parse bounded bytes in memory, close
  CLI SQLite connections, escape exported error text and correctly parse IPv6 hosts.
- Format Python with Ruff, enforce Python/frontend style checks in CI, separate tool
  handlers and package versioned prompts. Preserve v4 prompt content; v5 adds optional
  source-linked advisory questions for unresolved resources, without changing proof
  or execution authority.
- Add randomized independent-verifier tests, trace-failure regressions and historical
  identifier reassignment coverage. Retain documented benchmark failures and latency.
- Consolidate public documentation and archive redundant report/prototype snapshots.
  Keep replay inputs/recordings, benchmark generators, independent fixtures, security
  disclosures and provenance. No public Git history rewrite or release performed.

The published v0.4.0 tag/release and package version remain unchanged during review.
Current checks and limitations are documented in [evaluation](docs/evaluation.md).
