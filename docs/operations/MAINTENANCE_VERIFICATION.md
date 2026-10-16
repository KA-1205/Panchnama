# Maintenance verification — 17 October 2026

These results describe this maintenance change, not a release certification.

| Check | Result | Command/evidence |
|---|---|---|
| Workspace lint | PASS (6 tasks) | `pnpm lint` |
| Workspace typecheck | PASS (7 tasks, including shared build) | `pnpm typecheck` |
| Workspace tests | PASS (6 tasks) | `pnpm test` |
| API tests | 222 passed, 7 skipped | Tests skip unavailable live database and renderer dependencies explicitly |
| API coverage | PASS: branches 80.22%, lines/statements 92.75%, functions 97.11% | `pnpm --filter @panchnama/api test:coverage`; original 80% thresholds unchanged |
| ML tests | 73 passed, 2 skipped; coverage above the enforced 70% | Run inside the pinned lightweight ML venv; learned-model training not executed |
| Benchmark runner unit checks | PASS (3) | `node --test scripts/benchmark-api.test.mjs`; synthetic HTTP fixtures, not staging evidence |
| Tracked-file secret scan | PASS | `bash scripts/check-secrets.sh`, including the new files |
| Notebook syntax | PASS | Code cells compiled after IPython magic transformation; no training was run |
| Live SQL/renderer integration | BLOCKED locally | Needs Supabase/Postgres and live renderer configuration; CI jobs retain their checks |
| Device capture and staging latency | BLOCKED | Needs a device and configured staging session |
| Five-minute manual audit | BLOCKED | Needs a human-run timed report verification |

The new tests exercise successful bounded polling, exhausted polling, absent polling capability, and provider failure. No coverage threshold or failure behavior was weakened. Notebook fixes sort imports, remove unused imports/f-string prefixes, split setup/import cells and wrap long strings; model architecture, hyperparameters and training outputs were not regenerated.

[CI runs](https://github.com/KA-1205/Panchnama/actions) are the current remote evidence. [Benchmark instructions](BENCHMARKS.md) distinguish SQL index checks, API timings, and manual exit criteria.
