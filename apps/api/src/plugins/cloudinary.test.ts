/**
 * Phase 5 gate — Cloudinary signing goes through the SDK, never by hand (§3.11),
 * and URL signing grants no expiry (the `v{}` segment is a cache-buster; real
 * expiry lives on the authenticated original's auth_token).
 */
import { describe, expect, it } from 'vitest';
import { v2 as cloudinary } from 'cloudinary';
import { createCloudinaryAdapter } from './cloudinary.js';
import { testConfig } from '../testing/fakes.js';

const config = testConfig({
  CLOUDINARY_CLOUD_NAME: 'demo',
  CLOUDINARY_API_KEY: '123456789',
  CLOUDINARY_API_SECRET: 'abcdefghijklmnop',
});

describe('Cloudinary signing is SDK-produced (§3.11)', () => {
  const adapter = createCloudinaryAdapter(config);

  it('signRequest matches the SDK helper exactly (not string concat + digest)', () => {
    const params = { public_id: 'org/proj/sha', timestamp: 1700000000 };
    const fromAdapter = adapter.signRequest(params);
    const fromSdk = cloudinary.utils.api_sign_request(params, config.CLOUDINARY_API_SECRET);
    expect(fromAdapter).toBe(fromSdk);
    // A real SHA-1 hex signature, not an ad-hoc token.
    expect(fromAdapter).toMatch(/^[0-9a-f]{40}$/);
  });

  it('a derivative URL carries an SDK s-- signature segment', () => {
    const url = adapter.signedDerivativeUrl('org/proj/sha', 'c_limit,w_800');
    expect(url).toContain('/image/upload/');
    expect(url).toMatch(/s--[^/]+--/);
  });
});

describe('URL signing grants no expiry (§3.11)', () => {
  const adapter = createCloudinaryAdapter(config);

  it('an authenticated original carries an auth_token with a real deadline', () => {
    const { url, expiresAt } = adapter.originalUrl('org/proj/sha', 300);
    expect(url).toContain('/image/authenticated/');
    // Real expiry is the auth_token, not the version counter.
    expect(url).toMatch(/__cld_token__|exp=/);
    expect(expiresAt).toBeGreaterThan(Math.floor(Date.now() / 1000));
  });

  it('the v{} segment is a cache-buster, never treated as a deadline', () => {
    const url = adapter.signedDerivativeUrl('org/proj/sha', 'c_limit,w_800');
    // If a version segment is present it is a plain integer counter, not a TTL.
    const match = url.match(/\/v(\d+)\//);
    if (match !== null) {
      expect(Number(match[1])).toBeGreaterThan(0);
    }
    // The signed derivative URL is type upload and carries no auth_token expiry.
    expect(url).not.toContain('__cld_token__');
  });
});
