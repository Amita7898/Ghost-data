# Milestone 3 results — actual local inference

Implemented a single bounded local-model investigator, six typed tools, deterministic proposal validation, independent audit verification, trace recording, offline replay, CLI controls and SQLite persistence. The React/FastAPI milestone has not started.

## Model and installation

Apple M3 (8 CPU / 10 GPU cores), 16 GiB unified memory. Selected cached Qwen3.5 latest, 9.7B Q4_K_M, model digest `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`. Ollama 0.40.13 runs on 127.0.0.1:11434 with cloud features disabled. No API keys, accounts, paid APIs or additional model-weight downloads were used.

Cached assets: 6,594,474,711 bytes. Official runtime archive: 229,773,910 bytes; installed app: 711,564 KiB. Snapshot runner RSS: 6,767,360 KiB (~6.45 GiB); Ollama allocation: 5,956,907,825 bytes. These overlap in unified memory and are not peak measurements. The other cached model (Gemma3 4B) does not advertise native tools. No head-to-head quality or speed superiority is claimed. Cached model license: Apache-2.0; weights are not distributed here.

## Real demonstrations

| Recording | Execution | Calls | Input tokens | Output tokens | Result |
|---|---|---:|---:|---:|---|
| remaining-replica-v3-live.json | completed | 6 | 10058 | 639 | NON_COMPLIANT |
| receipt-absent-v4-live.json | completed | 5 | 8302 | 460 | VERIFIED_WITHIN_SCOPE |

The baseline demonstration took 169.83 s and made five dynamic tool calls, accepting one hypothesis. Its model-reported aggregate decoding speed was 5.47 tokens/s. The prose-receipt demonstration took 263.20 s while another diagnostic was active; use the serialized comparison below for a less confounded latency measurement. Both traces are genuine and offline replay was tested without runtime access. Earlier failed/budget-limited prototypes are retained honestly.

## Serialized final comparison

Four independently authored readback-note cases: absence, presence, contradiction and prompt injection. Hidden world facts/expected conclusions remain separate; filenames and labels are never passed to the runtime. Inputs are reproducible with ghost_data_bench.challenges. The registered source-contract grammar is intentionally narrow; a deterministic receipt parser could also solve it. Gains establish interpretation/orchestration value relative to the current kernel, not unique LLM capability or broad reasoning superiority.

| Mode | Accuracy | Completed | Unsupported verified | False noncompliant | Median seconds | Calls | Input / output tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| deterministic | 25% | 100% | 0 | 0 | 0.0003 | 0 | 0 / 0 |
| extraction | 75% | 100% | 0 | 0 | 25.9286 | 4 | 1642 / 362 |
| agent | 75% | 100% | 0 | 0 | 148.7462 | 20 | 33435 / 2072 |

| Case | Deterministic | Extraction | Agent | Expected |
|---|---|---|---|---|
| receipt_absent | INCONCLUSIVE | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE | VERIFIED_WITHIN_SCOPE |
| receipt_conflict | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE |
| receipt_injection | INCONCLUSIVE | NON_COMPLIANT | INCONCLUSIVE | NON_COMPLIANT |
| receipt_present | INCONCLUSIVE | NON_COMPLIANT | NON_COMPLIANT | NON_COMPLIANT |

- Agent: 21 model-selected tool calls, zero tool-result errors, two accepted and three rejected hypotheses. Accepted citation/source checks: 2/2.
- Extraction: two accepted and two rejected candidates. Accepted citation/source checks: 2/2. It abstained on absence but handled injection correctly.
- Agent discovered two previously unparsed source states. It established the one provable absence obligation (1/1); extraction and kernel established 0/1. This is a tiny coverage denominator.
- The agent abstained on the injection case instead of establishing the supported remaining record. No false verified claim escaped validation. This is a recall limitation, not proof of general injection immunity.
- All four final agent runs completed. Earlier concurrent exploratory runs had timeouts/cancellation/budget failures; they remain under local-agent-results and local-agent-v3-results and must not be pooled with the serialized final result.
- Full structured regressions: original 32/128/512-case seeds retain 100% accuracy and zero unsupported verified conclusions. Original kernel and all 136 prior test source files are unchanged (CLI extended).

## Testing and reproducibility

171 tests passed in a fresh environment with the opt-in real local-model smoke test enabled. Default offline suite: 170 passed, one real-model test skipped. The original 136 tests are preserved. Built wheel installation and CLI replay/kernel execution passed from a fresh venv; runtime Python source in the wheel matches this source tree.

New tests cover actual native tool calls (opt-in), typed scope and source-locator resolution, unsupported citations, partial/future/late evidence, claim-vs-readback separation, contradictory prose, rejected-fact rollback, cancellation, deadlines, token/tool/context budgets, malformed responses, unavailable runtime and HTTP timeout, redirects/cloud-model denial, completion-schema recovery, immutable event snapshots, SQLite persistence, offline replay integrity and input reproduction.

Token totals use Ollama counters for received responses, including repeated context; they are not unique evidence tokens. Failed requests may have unmeasured compute/tokens. Runtime API expenditure is $0; electricity and coding-assistant usage are not measured. Total final comparison: 24 model calls, 35,077 input tokens and 2,434 generated tokens.

## Remaining limits and next steps

Local inference is slow (agent median ~149 s here), and throughput varies with memory/system load. Serialize investigations; no session admission/job queue exists. General prose, PDFs/OCR and new identity links beyond registered evidence need reviewed extraction/source contracts. Source authenticity and inventory completeness remain adapter/caller assumptions. The model cannot authorize deletion or mutate resources. Traces are local evidence-bearing files, not signed attestations or durable per-event crash journals. Privacy review is required before exporting private traces. Only synthetic recordings are included here.

The four templates and a single model/seed are insufficient to establish general quality or select a challenger architecture. Extraction and agent have complementary errors. Collect held-out, broader source contracts before claiming consistent agent superiority or adding multi-agent complexity. No frontend, public repository or GitHub push was created.

See local-agent.md for architecture, commands, trust boundaries and limits; see local-agent-final-results/results.json for raw measurements. Original competition assets and internal transcripts are excluded.

Official references: [native tool calling](https://docs.ollama.com/capabilities/tool-calling), [chat API and counters](https://docs.ollama.com/api/chat), [model family](https://ollama.com/library/qwen3.5), [macOS support](https://docs.ollama.com/macos).
