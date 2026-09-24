import { describe, expect, it } from 'vitest'
import { maxRoleDestination } from './maxLaunch'

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
