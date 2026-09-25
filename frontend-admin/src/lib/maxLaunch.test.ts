import { afterEach, describe, expect, it } from 'vitest';
import { currentMaxInitData, waitForCurrentMaxInitData } from './maxLaunch';

afterEach(() => {
  window.WebApp = undefined;
  window.history.replaceState({}, '', '/');
});

describe('admin MAX launch context', () => {
  it('reads only SDK-provided context and ignores URL parameters', () => {
    window.history.replaceState({}, '', '/admin/login?initData=unsigned#hash=forged');
    window.WebApp = undefined;
    expect(currentMaxInitData()).toBe('');

    window.WebApp = { initData: 'signed-context-fixture' };
    expect(currentMaxInitData()).toBe('signed-context-fixture');
  });

  it('waits for delayed MAX Bridge launch data without reading URL parameters', async () => {
    window.WebApp = {};
    window.setTimeout(() => { window.WebApp = { initData: 'delayed-context-fixture' }; }, 10);

    await expect(waitForCurrentMaxInitData({ timeoutMs: 200, pollIntervalMs: 1 }))
      .resolves.toBe('delayed-context-fixture');
  });
});
