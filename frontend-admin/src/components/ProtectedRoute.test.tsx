import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { ProtectedRoute } from './ProtectedRoute';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ user: null, loading: false }),
}));

describe('ProtectedRoute', () => {
  it('redirects anonymous admins to login', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<ProtectedRoute><div>Панель</div></ProtectedRoute>} />
          <Route path="/login" element={<div>Страница входа</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('Страница входа')).toBeInTheDocument();
  });
});
