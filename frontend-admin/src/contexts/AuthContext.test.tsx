import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider, useAuth } from './AuthContext';
import api from '@/api/client';

vi.mock('@/api/client', () => ({ default: { get: vi.fn(), post: vi.fn() } }));

describe('admin MAX account linking', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.clearAllMocks();
  });

  it('links the MAX profile to the authenticated editor account without changing its role', async () => {
    const editor = {
      id: 303,
      email: 'editor@example.test',
      role: 'editor',
      university: 'МАИ',
      first_name: 'Editor',
      last_name: 'Test',
      full_name: 'Editor Test',
      is_active: true,
      date_joined: '',
      last_login: null,
    };
    vi.mocked(api.post).mockImplementation((url: string) => {
      if (url === '/v1/accounts/login/') {
        return Promise.resolve({ data: { access: 'login-session-fixture', user: editor } }) as any;
      }
      return Promise.resolve({
        data: { user: editor, tokens: { access: 'linked-session-fixture' } },
      }) as any;
    });
    const queryClient = new QueryClient();
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        <AuthProvider>{children}</AuthProvider>
      </QueryClientProvider>
    );
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.login(editor.email, 'fixture-password');
      await result.current.linkMaxProfile('signed-context-fixture');
    });

    expect(api.post).toHaveBeenNthCalledWith(1, '/v1/accounts/login/', {
      email: editor.email,
      password: 'fixture-password',
    });
    expect(api.post).toHaveBeenNthCalledWith(2, '/max/launch/', { initData: 'signed-context-fixture' });
    expect(result.current.user?.role).toBe('editor');
    expect(JSON.parse(localStorage.getItem('auth-storage') || '{}').state.user.role).toBe('editor');
    expect(JSON.parse(localStorage.getItem('auth-storage') || '{}').state.token).toBe('linked-session-fixture');
  });
});
