import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { ProtectedRoute } from './ProtectedRoute';

const authMock = vi.hoisted(() => ({ isAuthenticated: false, user: null as null | { role: string } }));

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => authMock,
}));

describe('ProtectedRoute', () => {
  it('redirects unauthenticated users to login', () => {
    authMock.isAuthenticated = false;
    authMock.user = null;
    render(
      <MemoryRouter initialEntries={['/home']}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/home" element={<div>Главная</div>} />
          </Route>
          <Route path="/login" element={<div>Страница входа</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('Страница входа')).toBeInTheDocument();
  });

  it('keeps a backend-authenticated student in the student interface', () => {
    authMock.isAuthenticated = true;
    authMock.user = { role: 'student' };
    render(
      <MemoryRouter initialEntries={['/home']}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/home" element={<div>Интерфейс студента</div>} />
          </Route>
          <Route path="/admin/*" element={<div>Интерфейс администратора</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('Интерфейс студента')).toBeInTheDocument();
  });

  it('routes a backend-authenticated admin to the public admin path', () => {
    authMock.isAuthenticated = true;
    authMock.user = { role: 'admin' };
    render(
      <MemoryRouter initialEntries={['/home']}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/home" element={<div>Интерфейс студента</div>} />
          </Route>
          <Route path="/admin/*" element={<div>Интерфейс администратора</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('Интерфейс администратора')).toBeInTheDocument();
  });
});
