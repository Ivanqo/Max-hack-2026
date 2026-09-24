import type { User } from '@/types'

type AdminIdentity = Pick<User, 'id' | 'university'> | null | undefined

export function adminQueryKey(user: AdminIdentity, resource: string, ...parts: unknown[]) {
  return ['admin', user?.id ?? 'anonymous', user?.university?.trim() || 'unknown', resource, ...parts] as const
}

export function adminIdentityKey(user: AdminIdentity) {
  return `${user?.id ?? 'anonymous'}:${user?.university?.trim() || 'unknown'}`
}
