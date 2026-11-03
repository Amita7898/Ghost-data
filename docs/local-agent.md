# Local investigation agent

See [architecture](architecture.md) for tools, prompt versions, proposal admission
and independent validation. [Setup](setup.md#live-local-inference) documents local
Ollama configuration, hardware assumptions and the optional CLI. No cloud API or
weight download is performed by the application.

The model gets scoped goals and bounded tool results, not expected answers or the
repository. Tools use strict schemas; unknown citations/resources and oversized
results fail closed. Default limits: six turns, 24 tools, 64,000 cumulative reported
tokens, 16,384 context and 300 seconds. The last budgeted turns request structured
completion without tools. Request timeout and conservative context bounds can stop
an investigation early. No automatic retry follows an uncertain model timeout.

The v5 prompt adds source-linked advisory questions; it does not expand evidence
contracts or authorization. Readability changes preserved v4 prompt bytes and its
recorded digest. LLM opportunity remains deliberately narrow: it can interpret
registered receipt prose, investigate gaps and ask follow-ups, but cannot create
sources or make an unverified compliance decision. A fixed parser may be preferable
for stable structured contracts. Dynamic orchestration is slower and not presumed
more accurate; see [measurements](evaluation.md).

Reproduce the four-case model comparison using an installed local tool-capable model:

```sh
python -m ghost_data_bench.local_agent benchmarks/agent-challenge --output .localdata/model-comparison
```

Use a new output directory. It runs deterministic, extraction and dynamic investigation
serially on identical visible files. Labels are loaded after prediction; live traces
and actual runtime token counts are saved. Local API cost is zero, but hardware,
electricity and coding-assistant costs are unmeasured. Avoid running other inference
clients concurrently. Mutable model tags and runtime versions can change results.


## Experimental advisory probe

```sh
python -m ghost_data_bench.advisory benchmarks/advisory --output .localdata/advisory-probe
```

The six fictional visible bundles cover missing readback, partial coverage, missing
field inventory, conflicts, compliant control and refusal control. The same goal is
used throughout; labels are read only after each investigation. The probe allows
six turns/240 seconds and 768 completion tokens, rather than the normal 512 output
limit. Actual traces and usage are saved; budget failures are retained. See
[evaluation](evaluation.md) for results. Questions are not currently demonstrated as
a dependable model capability and remain experimental. Link validation is not
semantic validation of a question's premise or advice.
