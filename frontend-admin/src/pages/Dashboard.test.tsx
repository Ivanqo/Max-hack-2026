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

  it('renders real analytics figures, not placeholder metrics', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: {
        totalUsers: 42,
        activeUsers: 31,
        totalOpportunities: 12,
        activeOpportunities: 9,
        totalKnowledgeBase: 24,
        publishedKnowledge: 20,
        userGrowth: [{ date: '2026-09-09', count: 5 }],
        popularRoles: [{ role: 'Бэкенд-разработчик', count: 7 }],
        topSearchQueries: [{ query: 'практика', count: 4 }],
        unansweredQueries: [{ query: 'военный учет', count: 2 }],
        opportunityViews: 18,
        opportunitySaves: 6,
      },
    });

    renderWithRouter(<Dashboard />);

    expect(await screen.findByText('42')).toBeInTheDocument();
    expect(screen.getByText('Бэкенд-разработчик')).toBeInTheDocument();
    expect(screen.getByText('Интересов: 7')).toBeInTheDocument();
    expect(screen.getByText('«военный учет»')).toBeInTheDocument();
    expect(screen.getByText('«практика»')).toBeInTheDocument();
  });
});
