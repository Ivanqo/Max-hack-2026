import { describe, expect, it } from 'vitest'
import { resolveApiBaseUrl } from './apiBase'

describe('student API base URL', () => {
  it('routes an insecure configured API through the public HTTPS host', () => {
    expect(resolveApiBaseUrl('http://api.example.test/api', 'https://app.example.test/')).toBe('/api')
  })

  it('preserves an explicitly secure API URL', () => {
    expect(resolveApiBaseUrl('https://api.example.test/api', 'https://app.example.test/'))
      .toBe('https://api.example.test/api')
  })

  it('keeps relative API paths and local HTTP development working', () => {
    expect(resolveApiBaseUrl('/api', 'https://app.example.test/')).toBe('/api')
    expect(resolveApiBaseUrl('http://localhost:8000/api', 'http://localhost:3000/'))
      .toBe('http://localhost:8000/api')
  })
})
