import { screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import Opportunities from './Opportunities';
import { renderWithProviders } from '@/test/render';
import { apiClient } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('Opportunities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders match percentage and the top reason for each card', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: [
        {
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
          sourceUrl: '',
          matchPercentage: 82,
          matchReasons: ['Подходит Python'],
          gaps: ['Не хватает Docker'],
          isSaved: false,
          postedDate: '2026-09-09T00:00:00Z',
          createdAt: '2026-09-09T00:00:00Z',
          updatedAt: '2026-09-09T00:00:00Z',
        },
      ],
    });

    renderWithProviders(<Opportunities />);

    expect(await screen.findByText('Бэкенд-стажировка')).toBeInTheDocument();
    expect(screen.getByText('82%')).toBeInTheDocument();
    expect(screen.getByText(/Подходит Python/)).toBeInTheDocument();
  });

  it('shows an empty state when there are no opportunities', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: [] });

    renderWithProviders(<Opportunities />);

    expect(await screen.findByText('Пока нет доступных возможностей')).toBeInTheDocument();
  });
});
