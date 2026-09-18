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

  it('renders match percentage, reasons, and gaps', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: [
        {
          id: '1',
          title: 'Бэкенд-стажировка',
          company: 'MAX Labs',
          location: 'Кампус',
          type: 'internship',
          description: 'Разработка API.',
          requirements: ['Python', 'Docker'],
          matchPercentage: 82,
          matchReasons: ['Подходит Python'],
          gaps: ['Не хватает Docker'],
          isSaved: false,
          postedDate: '2026-09-09T00:00:00Z',
        },
      ],
    });

    renderWithProviders(<Opportunities />);

    expect(await screen.findByText('Бэкенд-стажировка')).toBeInTheDocument();
    expect(screen.getByText('82%')).toBeInTheDocument();
    expect(screen.getByText('Подходит Python')).toBeInTheDocument();
    expect(screen.getByText('Не хватает Docker')).toBeInTheDocument();
  });
});
