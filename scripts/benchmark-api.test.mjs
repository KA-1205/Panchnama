import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { benchmark } from './benchmark-api.mjs';

async function fixture(handler, run) {
  const server = createServer(handler);
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  try {
    await run(`http://127.0.0.1:${server.address().port}`);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
}

test('records real response times and strips tokens and payloads from evidence', async () => {
  await fixture(
    (request, response) => {
      assert.equal(request.headers.authorization, 'Bearer fixture-only');
      response.setHeader('Content-Type', 'application/json');
      response.end(
        JSON.stringify({
          data: request.url.includes('search')
            ? { data: [{ confidential: 'not-recorded' }], total_matched: 1000 }
            : { ok: true, checked: 3 },
        }),
      );
    },
    async (baseUrl) => {
      const result = await benchmark({
        baseUrl,
        token: 'fixture-only',
        assetId: 'test-id',
        samples: 2,
        warmup: 1,
        intervalMs: 0,
      });
      assert.equal(result.results.length, 2);
      assert.equal(result.results[0].raw.length, 2);
      assert.ok(result.results[0].raw.every((r) => r.elapsed_ms >= 0 && r.status === 200));
      assert.ok(!JSON.stringify(result).includes('fixture-only'));
      assert.ok(!JSON.stringify(result).includes('not-recorded'));
    },
  );
});

test('rejects a failing verification or insufficient dataset rather than reporting a pass', async () => {
  await fixture(
    (_request, response) => {
      response.setHeader('Content-Type', 'application/json');
      response.end(
        JSON.stringify({ data: { data: [], total_matched: 10, ok: false, checked: 0 } }),
      );
    },
    async (baseUrl) => {
      await assert.rejects(
        benchmark({
          baseUrl,
          token: 'fixture-only',
          assetId: 'test-id',
          samples: 1,
          intervalMs: 0,
        }),
        /precondition failed/,
      );
    },
  );
});

test('refuses plain HTTP outside loopback and credential-bearing base URLs', async () => {
  await assert.rejects(
    benchmark({ baseUrl: 'http://example.invalid', token: 't', assetId: 'a' }),
    /HTTPS required/,
  );
  await assert.rejects(
    benchmark({ baseUrl: 'https://user:pass@example.invalid', token: 't', assetId: 'a' }),
    /must not contain/,
  );
});
