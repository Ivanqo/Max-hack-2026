interface MaxWebAppBridge {
  initData?: string;
}

declare global {
  interface Window {
    MAX?: { WebApp?: MaxWebAppBridge };
    WebApp?: MaxWebAppBridge;
    Telegram?: { WebApp?: MaxWebAppBridge };
  }
}

/** Reads provider SDK launch data only; URL values are not an identity source. */
export function currentMaxInitData(): string {
  const initData = window.MAX?.WebApp?.initData || window.WebApp?.initData || window.Telegram?.WebApp?.initData;
  return typeof initData === 'string' ? initData.trim() : '';
}

/** Wait briefly for the MAX Bridge to finish exposing its signed launch data. */
export async function waitForCurrentMaxInitData(options: {
  timeoutMs?: number;
  pollIntervalMs?: number;
} = {}): Promise<string> {
  const timeoutMs = options.timeoutMs ?? 10_000;
  const pollIntervalMs = options.pollIntervalMs ?? 80;
  const deadline = Date.now() + timeoutMs;
  while (Date.now() <= deadline) {
    const initData = currentMaxInitData();
    if (initData) return initData;
    await new Promise<void>((resolve) => window.setTimeout(resolve, Math.min(pollIntervalMs, Math.max(1, deadline - Date.now()))));
  }
  throw new Error('MAX launch context was not provided');
}
