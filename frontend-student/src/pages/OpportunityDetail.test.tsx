import { screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import OpportunityDetail from './OpportunityDetail';
import { renderWithProviders } from '@/test/render';
import { apiClient } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('OpportunityDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders match reasons and gaps for the opportunity', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: {
        id: '1',
        title: 'Бэкенд-стажировка',
        company: 'MAX Labs',
        location: 'Кампус',
        type: 'internship',
        description: 'Разработка API.',
        requirements: ['Python', 'Docker'],
        skills: [],
        status: 'active',
        published: true,
        verifiedStatus: 'verified',
        deadline: null,
        sourceUrl: 'https://example.org/apply',
        matchPercentage: 82,
        matchReasons: ['Подходит Python'],
        gaps: ['Не хватает Docker'],
        isSaved: false,
        postedDate: '2026-09-09T00:00:00Z',
        createdAt: '2026-09-09T00:00:00Z',
        updatedAt: '2026-09-09T00:00:00Z',
      },
    });

    renderWithProviders(<OpportunityDetail />, {
      route: { path: '/opportunities/:id', initialEntry: '/opportunities/1' },
    });

    expect(await screen.findByText('Бэкенд-стажировка')).toBeInTheDocument();
    expect(screen.getByText('Подходит Python')).toBeInTheDocument();
    expect(screen.getByText('Не хватает Docker')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /откликнуться/i })).toHaveAttribute('href', 'https://example.org/apply');
  });
});
