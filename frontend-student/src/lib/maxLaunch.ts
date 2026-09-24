const ADMIN_ROLES = new Set(['admin', 'editor', 'institute_admin', 'university_admin'])

export function maxRoleDestination(role: string): '/home' | '/admin/' | null {
  if (role === 'student') return '/home'
  if (ADMIN_ROLES.has(role)) return '/admin/'
  return null
}
