# Advisory gap and control probes

Six manually authored fictional variants of examples/scoped_absence.json test:
missing cutoff readback, partial snapshot coverage, missing required field inventory,
conflicting readbacks, compliant evidence and explicit refusal.

Only visible/*.json enters runtime tools. evaluator_only/expectations.json contains
separate hashes, supported conclusions and missing-information rubrics. The runner
loads those references after inference. It does not send filenames, expected labels
or gap rubrics to the model. All cases use the same investigation goal.

Run from the repository root with the installed local Ollama model:

    python -m ghost_data_bench.advisory benchmarks/advisory --output .localdata/advisory-probe

Use a new output directory. No cloud API or automatic model download is used.
The recorded probe emitted zero questions; it establishes neither usefulness nor
reliable question generation. See docs/evaluation.md for complete results/limitations.
