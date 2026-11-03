# Development and validation

Use README setup first. Python dependencies are pinned in requirements-web-tested.txt;
JavaScript resolution is locked in frontend/package-lock.json. The original application is MIT licensed; see LICENSE and
docs/provenance-and-licensing.md for provenance and third-party boundaries.

```sh
pytest -q
npm test --prefix frontend
npm run build --prefix frontend
python scripts/check_setup.py --offline
python scripts/start.py --offline
# Another terminal, with installed Chrome on this Mac:
npm run test:e2e --prefix frontend
```

Standard tests do not need Ollama. CI installs Chromium; locally Playwright uses
Chrome unless CI is set. To use bundled Chromium locally, install it with
`npm exec --prefix frontend -- playwright install chromium`, then run tests with
`CI=1 npm run test:e2e --prefix frontend`. Accessibility checks are scoped automated
checks, not a declaration of full WCAG conformance; also review keyboard/mobile UX.

Optional real inference (serialize; actual installed model required):

```sh
GHOST_DATA_REAL_SMOKE=1 pytest -q tests/test_agent.py::test_real_model_emits_tool_call
# Normal live server must be running; do not combine with offline E2E:
GHOST_DATA_LIVE_WEB=1 npm run test:e2e --prefix frontend -- e2e/live.spec.ts
```

During frontend development start the backend and use `npm run dev --prefix frontend`.
Vite binds to localhost:5173 and proxies /api to port 8000. API docs: /docs. Regenerate
checked-in DTOs after intentional API changes:

```sh
python scripts/export_openapi.py
npm run api:types --prefix frontend
```

Only use the local generated schema; see SECURITY.md for the remaining type-generator
advisory. Review API diff and run TypeScript/build/browser tests after generation.

Before publication, from a Git checkout:

```sh
python scripts/release_audit.py
npm audit --prefix frontend --omit=dev
npm audit --prefix frontend
```

The full npm audit currently reports a documented development-only chain; do not
suppress it or apply a forced major dependency override without compatibility tests.
For Python audit use an isolated pip-audit installation against the pinned file.
Recheck advisories on the release date; a previous clean result is not a guarantee.

Never add private evidence, real personal data, original competition material,
credentials or development chats. Keep model tools read-only; do not promote claims
or partial snapshots to deletion proof. Changes to source contracts require targeted
safety/contradiction/temporal tests and an independent proof review. Preserve genuine
recordings and label all test runtimes distinctly. See docs/performance.md for
reproducible synthetic benchmarks and their limitations.
