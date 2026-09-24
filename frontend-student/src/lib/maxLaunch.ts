const ADMIN_ROLES = new Set(['admin', 'editor', 'institute_admin', 'university_admin'])

export interface MaxWebAppBridge {
  initData?: string
  ready?: () => void
}

export interface MaxLaunchContext {
  webApp: MaxWebAppBridge
  initData: string
}

export type MaxLaunchStage = 'waiting_for_sdk' | 'waiting_for_context' | 'checking_backend' | 'authenticated'

export class MaxLaunchStartupError extends Error {
  constructor(readonly kind: 'sdk_timeout' | 'context_timeout') {
    super(kind === 'sdk_timeout' ? 'MAX Bridge did not become ready' : 'MAX launch context was not provided')
    this.name = 'MaxLaunchStartupError'
  }
}

interface WaitOptions {
  timeoutMs?: number
  pollIntervalMs?: number
  sleep?: (milliseconds: number) => Promise<void>
}

interface LaunchMaxAppOptions extends WaitOptions {
  getWebApp: () => MaxWebAppBridge | undefined
  loadSdk: () => Promise<void>
  completeLaunch: (initData: string) => Promise<{ role: string; startParam?: string }>
  onStage?: (stage: MaxLaunchStage) => void
  onContext?: (context: MaxLaunchContext) => void
}

const defaultSleep = (milliseconds: number) =>
  new Promise<void>((resolve) => window.setTimeout(resolve, milliseconds))

async function waitForValue<T>(
  read: () => T | null | undefined,
  kind: MaxLaunchStartupError['kind'],
  options: WaitOptions,
): Promise<T> {
  const timeoutMs = options.timeoutMs ?? 10_000
  const pollIntervalMs = options.pollIntervalMs ?? 80
  const sleep = options.sleep ?? defaultSleep
  const deadline = Date.now() + timeoutMs

  while (Date.now() <= deadline) {
    const value = read()
    if (value) return value
    await sleep(Math.min(pollIntervalMs, Math.max(1, deadline - Date.now())))
  }

  throw new MaxLaunchStartupError(kind)
}

export async function waitForMaxBridgeSdk(
  getWebApp: () => MaxWebAppBridge | undefined,
  options: WaitOptions = {},
): Promise<void> {
  await waitForValue(getWebApp, 'sdk_timeout', options)
}

/** Shares one SDK readiness wait between concurrent React effects/retries. */
export function createMaxSdkLoader(waitForSdk: () => Promise<void>): () => Promise<void> {
  let sdkReady: Promise<void> | null = null
  return () => {
    if (!sdkReady) {
      sdkReady = waitForSdk().catch((error) => {
        sdkReady = null
        throw error
      })
    }
    return sdkReady
  }
}

/** Wait for the official bridge first, then read its signed launch context afresh. */
export async function launchMaxApp(options: LaunchMaxAppOptions) {
  options.onStage?.('waiting_for_sdk')
  await options.loadSdk()

  options.onStage?.('waiting_for_context')
  const context = await waitForValue(() => {
    const webApp = options.getWebApp()
    const initData = webApp?.initData
    return webApp && typeof initData === 'string' && initData.trim()
      ? { webApp, initData }
      : null
  }, 'context_timeout', options)

  options.onContext?.(context)
  options.onStage?.('checking_backend')
  const session = await options.completeLaunch(context.initData)
  const destination = maxRoleDestination(session.role)
  if (!destination) throw new Error('Unsupported account role')

  options.onStage?.('authenticated')
  return { ...session, destination }
}

export function maxRoleDestination(role: string): '/home' | '/admin/' | null {
  if (role === 'student') return '/home'
  if (ADMIN_ROLES.has(role)) return '/admin/'
  return null
}
