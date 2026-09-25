import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Login } from './Login';

const { loginMock, linkMaxProfileMock } = vi.hoisted(() => ({
  loginMock: vi.fn(),
  linkMaxProfileMock: vi.fn(),
}));

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ login: loginMock, linkMaxProfile: linkMaxProfileMock }),
}));

describe('admin login MAX linking feedback', () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.clearAllMocks();
    window.WebApp = { initData: 'signed-context-fixture' };
    loginMock.mockResolvedValue({ id: 12, role: 'admin' });
    linkMaxProfileMock.mockRejectedValue({
      response: { status: 400, data: { detail: 'Invalid MAX launch context.' } },
    });
  });

  it('explains how to recover from a rejected MAX context after local sign-in', async () => {
    render(<MemoryRouter basename="/admin" initialEntries={['/admin/login']}><Login /></MemoryRouter>);

    fireEvent.change(screen.getByPlaceholderText('admin@demo.local'), { target: { value: 'admin@example.test' } });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'fixture-password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Войти' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Вход выполнен, но MAX не подтвердил данные запуска');
    expect(screen.getByRole('alert')).toHaveTextContent('откройте его заново из MAX');
    expect(linkMaxProfileMock).toHaveBeenCalledWith('signed-context-fixture');
  });
});
