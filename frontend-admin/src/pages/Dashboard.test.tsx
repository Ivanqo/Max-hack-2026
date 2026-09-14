import { screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { Dashboard } from './Dashboard';
import { renderWithRouter } from '@/test/render';
import api from '@/api/client';

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
  },
}));

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders analytics cards and lists', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: {
        totalUsers: 42,
        activeUsers: 31,
        totalOpportunities: 12,
        totalKnowledgeBase: 24,
        userGrowth: [{ date: '2026-09-09', count: 5 }],
        popularRoles: [{ role: 'Backend Developer', count: 7 }],
      },
    });

    renderWithRouter(<Dashboard />);

    expect(await screen.findByText('Total Users')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('Backend Developer')).toBeInTheDocument();
    expect(screen.getByText('7 interests')).toBeInTheDocument();
  });
});
