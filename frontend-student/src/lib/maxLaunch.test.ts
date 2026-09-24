import { describe, expect, it, vi } from 'vitest'
import {
  createMaxSdkLoader,
  launchMaxApp,
  MaxLaunchStartupError,
  maxRoleDestination,
  MaxWebAppBridge,
} from './maxLaunch'

const shortWait = (milliseconds: number) => new Promise<void>((resolve) => setTimeout(resolve, milliseconds))

function launchOptions(overrides: Partial<Parameters<typeof launchMaxApp>[0]> = {}) {
  const webApp: MaxWebAppBridge = { initData: 'signed-context-fixture' }
  return {
    getWebApp: () => webApp,
    loadSdk: async () => undefined,
    completeLaunch: async () => ({ role: 'student' }),
    timeoutMs: 30,
    pollIntervalMs: 1,
    sleep: shortWait,
    ...overrides,
  }
}

describe('MAX role routing', () => {
  it('routes students to the student app based on the backend role', () => {
    expect(maxRoleDestination('student')).toBe('/home')
  })

  it('routes administrators to the public admin app', () => {
    expect(maxRoleDestination('admin')).toBe('/admin/')
    expect(maxRoleDestination('university_admin')).toBe('/admin/')
  })

  it('does not route an unsupported role into the admin app', () => {
    expect(maxRoleDestination('unknown')).toBeNull()
  })
})

describe('MAX Mini App startup', () => {
  it('waits for a delayed SDK and then for initData before contacting the backend', async () => {
    let webApp: MaxWebAppBridge | undefined
    const stages: string[] = []
    const completeLaunch = vi.fn(async () => ({ role: 'student' }))
    const loadSdk = vi.fn(async () => {
      await shortWait(5)
      webApp = {}
      setTimeout(() => { if (webApp) webApp.initData = 'signed-context-fixture' }, 5)
    })

    const result = await launchMaxApp({
      getWebApp: () => webApp,
      loadSdk,
      completeLaunch,
      onStage: (stage) => stages.push(stage),
      timeoutMs: 250,
      pollIntervalMs: 1,
      sleep: shortWait,
    })

    expect(result.destination).toBe('/home')
    expect(loadSdk).toHaveBeenCalledTimes(1)
    expect(completeLaunch).toHaveBeenCalledWith('signed-context-fixture')
    expect(stages).toEqual(['waiting_for_sdk', 'waiting_for_context', 'checking_backend', 'authenticated'])
  })

  it('shares SDK readiness work and re-reads context on every launch, regardless of stale storage flags', async () => {
    sessionStorage.setItem('max-launch-processed', 'true')
    let reads = 0
    const baseLoad = vi.fn(async () => undefined)
    const loadSdk = createMaxSdkLoader(baseLoad)
    const getWebApp = vi.fn(() => {
      reads += 1
      return { initData: `signed-context-${reads}` }
    })
    const completeLaunch = vi.fn(async () => ({ role: 'student' }))

    await Promise.all([
      launchMaxApp({ ...launchOptions(), getWebApp, loadSdk, completeLaunch }),
      launchMaxApp({ ...launchOptions(), getWebApp, loadSdk, completeLaunch }),
    ])
    await launchMaxApp({ ...launchOptions(), getWebApp, loadSdk, completeLaunch })

    expect(baseLoad).toHaveBeenCalledTimes(1)
    expect(getWebApp.mock.calls.length).toBeGreaterThanOrEqual(3)
    expect(completeLaunch).toHaveBeenNthCalledWith(1, 'signed-context-1')
    expect(completeLaunch).toHaveBeenNthCalledWith(2, 'signed-context-2')
    expect(completeLaunch).toHaveBeenNthCalledWith(3, 'signed-context-3')
  })

  it('does not send an absent or URL-only context to the backend', async () => {
    window.history.replaceState({}, '', '/?initData=unsigned&hash=forged#WebAppData=unsigned')
    const completeLaunch = vi.fn()

    await expect(launchMaxApp({
      getWebApp: () => ({}),
      loadSdk: async () => undefined,
      completeLaunch,
      timeoutMs: 5,
      pollIntervalMs: 1,
      sleep: shortWait,
    })).rejects.toMatchObject({ kind: 'context_timeout' })

    expect(completeLaunch).not.toHaveBeenCalled()
  })

  it('keeps backend signature errors as failures and retries with freshly read context', async () => {
    let contextVersion = 0
    const getWebApp = vi.fn(() => ({ initData: `signed-context-${++contextVersion}` }))
    const invalidContext = { response: { status: 400, data: { detail: 'Invalid MAX launch context.' } } }
    const completeLaunch = vi.fn()
      .mockRejectedValueOnce(invalidContext)
      .mockResolvedValueOnce({ role: 'admin' })
    const failedStages: string[] = []

    await expect(launchMaxApp({
      ...launchOptions(),
      getWebApp,
      completeLaunch,
      onStage: (stage) => failedStages.push(stage),
    }))
      .rejects.toBe(invalidContext)
    expect(failedStages).not.toContain('authenticated')
    const result = await launchMaxApp({ ...launchOptions(), getWebApp, completeLaunch })

    expect(result.destination).toBe('/admin/')
    expect(getWebApp.mock.calls.length).toBeGreaterThanOrEqual(2)
    expect(completeLaunch).toHaveBeenNthCalledWith(1, 'signed-context-1')
    expect(completeLaunch).toHaveBeenNthCalledWith(2, 'signed-context-2')
  })

  it('can retry SDK readiness after a timed-out attempt', async () => {
    let ready = false
    const loadSdk = createMaxSdkLoader(async () => {
      if (!ready) throw new MaxLaunchStartupError('sdk_timeout')
    })
    const completeLaunch = vi.fn(async () => ({ role: 'student' }))

    await expect(launchMaxApp({ ...launchOptions(), loadSdk, completeLaunch })).rejects.toMatchObject({ kind: 'sdk_timeout' })
    ready = true
    const result = await launchMaxApp({ ...launchOptions(), loadSdk, completeLaunch })

    expect(result.destination).toBe('/home')
    expect(completeLaunch).toHaveBeenCalledTimes(1)
  })
})
