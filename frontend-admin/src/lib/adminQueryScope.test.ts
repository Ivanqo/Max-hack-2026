import { QueryClient } from '@tanstack/react-query'
import { describe, expect, it } from 'vitest'
import { adminIdentityKey, adminQueryKey } from './adminQueryScope'

describe('admin cache identity', () => {
  it('does not reuse cached MGSU data after switching the administrator to MAI', () => {
    const cache = new QueryClient()
    const mgsuAdmin = { id: 41, university: 'НИУ МГСУ' }
    const maiAdmin = { id: 52, university: 'МАИ' }
    const mgsuKey = adminQueryKey(mgsuAdmin, 'knowledge')
    const maiKey = adminQueryKey(maiAdmin, 'knowledge')

    cache.setQueryData(mgsuKey, [{ title: 'Материал МГСУ' }])

    expect(adminIdentityKey(mgsuAdmin)).not.toBe(adminIdentityKey(maiAdmin))
    expect(cache.getQueryData(maiKey)).toBeUndefined()
    expect(cache.getQueryData(mgsuKey)).toEqual([{ title: 'Материал МГСУ' }])
    cache.clear()
  })

  it('separates cached data when the same administrator changes organization', () => {
    const mgsuKey = adminQueryKey({ id: 41, university: 'НИУ МГСУ' }, 'analytics')
    const maiKey = adminQueryKey({ id: 41, university: 'МАИ' }, 'analytics')

    expect(mgsuKey).not.toEqual(maiKey)
  })
})
