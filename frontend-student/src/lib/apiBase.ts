/** Keep same-origin API requests on the page's HTTPS connection. */
export function resolveApiBaseUrl(configuredUrl: string | undefined, pageUrl: string): string {
  const candidate = configuredUrl?.trim() || '/api'
  try {
    const page = new URL(pageUrl)
    const api = new URL(candidate, page)
    if (!['http:', 'https:'].includes(api.protocol)) return '/api'
    if (page.protocol === 'https:' && api.protocol !== 'https:') return '/api'
    return candidate
  } catch {
    return '/api'
  }
}
