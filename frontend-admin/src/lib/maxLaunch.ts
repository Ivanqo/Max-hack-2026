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
