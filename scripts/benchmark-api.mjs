/** Read-only search/chain timing. Tokens and response bodies are never recorded. */
import { writeFile } from 'node:fs/promises';
import { performance } from 'node:perf_hooks';
import { pathToFileURL } from 'node:url';
import { setTimeout as wait } from 'node:timers/promises';
import os from 'node:os';

function summary(values) {
  const sorted = [...values].sort((a, b) => a - b);
  return {
    p50: sorted[Math.floor((sorted.length - 1) * 0.5)],
    p95: sorted[Math.floor((sorted.length - 1) * 0.95)],
    min: sorted[0],
    max: sorted.at(-1),
  };
}

export async function benchmark({
  baseUrl,
  token,
  assetId,
  samples = 5,
  warmup = 1,
  expectedAssets = 1000,
  intervalMs = 1300,
}) {
  const base = new URL(baseUrl);
  if (base.username || base.password || base.search || base.hash)
    throw new Error('Base URL must not contain credentials, query, or fragment');
  const local = ['localhost', '127.0.0.1', '[::1]'].includes(base.hostname);
  if (base.protocol !== 'https:' && !(local && base.protocol === 'http:'))
    throw new Error('HTTPS required outside loopback');
  if (!token || !assetId) throw new Error('Token and benchmark asset id are required');
  if (
    !Number.isInteger(samples) ||
    samples < 1 ||
    samples > 10 ||
    !Number.isInteger(warmup) ||
    warmup < 0 ||
    warmup > 3
  )
    throw new Error('samples 1..10; warmup 0..3');
  if (!Number.isInteger(expectedAssets) || expectedAssets < 1)
    throw new Error('Expected asset count must be positive');
  if (!Number.isFinite(intervalMs) || intervalMs < (local ? 0 : 1250))
    throw new Error('Remote requests must respect the search rate limit');
  const endpoints = [
    {
      label: 'search',
      path: '/v1/search?limit=20',
      validate: (j) => Array.isArray(j.data?.data) && j.data.total_matched >= expectedAssets,
    },
    {
      label: 'verify_chain',
      path: `/v1/assets/${encodeURIComponent(assetId)}/verify-chain`,
      validate: (j) => j.data?.ok === true && j.data.checked > 0,
    },
  ];
  const results = [];
  for (const endpoint of endpoints) {
    const raw = [];
    for (let i = 0; i < samples + warmup; i += 1) {
      const start = performance.now();
      const response = await fetch(
        new URL(base.pathname.replace(/\/$/, '') + endpoint.path, base.origin),
        {
          headers: { Authorization: `Bearer ${token}` },
          signal: AbortSignal.timeout(30_000),
          redirect: 'error',
        },
      );
      let body;
      try {
        body = await response.json();
      } catch {
        throw new Error(`${endpoint.label}: invalid JSON (HTTP ${response.status})`);
      }
      const elapsed = performance.now() - start;
      if (!response.ok || !endpoint.validate(body))
        throw new Error(
          `${endpoint.label}: HTTP ${response.status} or benchmark precondition failed`,
        );
      if (i >= warmup) raw.push({ elapsed_ms: elapsed, status: response.status });
      if (intervalMs) await wait(intervalMs);
    }
    results.push({ label: endpoint.label, raw, summary_ms: summary(raw.map((r) => r.elapsed_ms)) });
  }
  return {
    schema: 'panchnama.readonly-api-benchmark.v1',
    generated_at: new Date().toISOString(),
    environment: { node: process.version, platform: os.platform(), architecture: os.arch() },
    workload: {
      samples,
      warmup_excluded: warmup,
      minimum_matching_assets: expectedAssets,
      concurrency: 1,
      interval_ms: intervalMs,
    },
    results,
    limitations: [
      'Read-only API timings; does not measure capture-to-dashboard or manual audit completion.',
      'API network and server time included; database isolation and production capacity are not established by timing.',
    ],
  };
}

async function main() {
  const result = await benchmark({
    baseUrl: process.env.PANCHNAMA_API_URL,
    token: process.env.PANCHNAMA_TOKEN,
    assetId: process.env.BENCH_ASSET_ID,
    samples: Number(process.env.BENCH_SAMPLES ?? 5),
    expectedAssets: Number(process.env.BENCH_EXPECTED_ASSETS ?? 1000),
  });
  await writeFile(
    process.env.BENCH_OUTPUT ?? 'api-benchmark.json',
    JSON.stringify(result, null, 2) + '\n',
  );
  console.log('Saved read-only API benchmark; no tokens or response bodies recorded.');
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}
