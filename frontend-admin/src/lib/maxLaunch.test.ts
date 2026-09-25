import { afterEach, describe, expect, it } from 'vitest';
import { currentMaxInitData } from './maxLaunch';

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
});
