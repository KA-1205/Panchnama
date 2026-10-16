# Performance evidence and open measurements

Latency budgets are targets until a run records the actual environment and raw outputs. The 80% API / 70% ML coverage settings are enforced thresholds, not achieved-coverage claims.

## Automated local evidence

The [SQL harness](../../apps/api/src/routes/search-perf.integration.test.ts) seeds 1,000 synthetic assets inside a rolled-back transaction and checks each filter's index applicability. It logs query timing but does not assert the staging 500 ms budget. Run it with a disposable local Supabase database:

```bash
pnpm --filter @panchnama/api test:perf
```

Record the commit, database/Postgres/PostGIS versions, host CPU/RAM, indexes, asset count, query, warm/cold state, concurrent workload, repetitions, raw timings and query plans. A CI index-applicability check is not end-to-end staging latency.

## Read-only staging API benchmark

```bash
# Configure PANCHNAMA_API_URL, PANCHNAMA_TOKEN, BENCH_ASSET_ID in your local environment.
# Use a known intact synthetic asset and an org containing at least 1,000 searchable assets.
node scripts/benchmark-api.mjs
node --test scripts/benchmark-api.test.mjs
```

The runner records sequential search and nonempty verified-chain timing samples, excluded warmups, status codes, percentiles and client environment. It fails for missing data, HTTP errors or a failed/empty audit verification; it does not print credentials, IDs or response contents. Remote requests are paced below the documented search rate limit. Set `BENCH_OUTPUT` for the result path and `BENCH_SAMPLES` (1–10) for repetitions. Attach server/database and dataset details separately. Harness unit tests use a synthetic HTTP fixture and are not staging evidence.

## Capture-to-dashboard and human audit

These remain **unmeasured** without a real capture device, configured staging services and a user-run session. Use one monotonic observer clock or a stopwatch to time capture→visible verified dashboard media; do not subtract untrusted device/server clocks. Record photo/video sizes, network, device, cold/warm state, failed attempts, and every sample. For the under-five-minute manual audit target, time a person verifying a generated report and record success/failure plus checklist. Do not equate API verify-chain response time with a complete human audit.
