# Provenance and licensing review

The standalone project was developed as a personal data-deletion investigation
platform, inspired by an auditing challenge. Its Python package, UI, synthetic
world generator, prompts and fictional demonstrations were built for this project.
Competition datasets, canonical answers, problem text, organizer internals,
submission archives and private development transcripts are not publication assets.

The benchmark's `evaluator_only` directories are this project's independently
created fictional reference worlds, not challenge truth. They are intentionally
excluded from runtime tool inputs; tests enforce that application-level boundary.
Source and generators permit reproduction of these visible/expected pairs.

## Checks performed

Reviewed the original public challenge repository root/README and official program
help page on 2026-11-03. The inspected material did not establish a broad permission
to redistribute challenge assets; no repository license was visible in that root.
The challenge page could not be retrieved by the web tool. Public visibility alone
must not be treated as a reuse license. Participation emails, private agreements
and all possible event terms were not available for review.

Sources (linked, not redistributed):
- [Original public repository](https://github.com/interviewstreet/hackerrank-orchestrate-october26)
- [Official program description](https://help.hackerrank.com/articles/3728112689-hackerrank-orchestrate)

The owner has explicitly confirmed the necessary rights and permission to reuse
and publicly publish the original project. No legal clearance or certification is
claimed. Do not add original competition materials to make the demo easier.

## Recommended application license

**MIT**, selected and approved by the owner, with the holder/year in LICENSE. It is a
short permissive license requiring preservation of copyright/license notices;
it includes warranty/liability limitations. See the
[official selection guidance](https://choosealicense.com/licenses/mit/).
It suits a portfolio project intended for study and reuse. Apache-2.0 is a reasonable
alternative if an explicit patent grant is preferred, with more notice obligations.

The owner explicitly approved MIT and public publication; LICENSE and package
metadata now reflect that decision. Earlier review states remain historical records.

## Third-party components

Python/JavaScript packages retain their upstream licenses. Dependencies are installed
from package registries, not vendored; lockfile metadata is not an endorsement or
replacement for required notices when distributing builds. Review dependency notices
before a packaged binary/release distribution. This phase prepares source publication,
not bundled model/runtime distribution.

Ollama binaries and Qwen weights are not included. The cached Qwen model metadata
reported Apache-2.0; confirm the actual selected model card/license and runtime
notices before redistributing anything. Mutable tags can resolve to different
artifacts. Source publication does not relicense model weights or competition data.

## Owner decisions applied for publication

The owner explicitly confirmed the necessary rights and permission to reuse and
publicly publish their original project, approved public amita7898/ghost-data,
selected MIT, and confirmed the copyright-holder text used in LICENSE. The owner
also accepted the three documented moderate development-only advisory entries
under the trusted-local-schema restriction. These later decisions supersede the
pending items in the historical prepublication review above. Private agreements
are not redistributed; this record does not claim independent legal clearance.

The application license is now MIT. Historical milestone/review reports describe
their then-current approval state; they are preserved as development evidence.
