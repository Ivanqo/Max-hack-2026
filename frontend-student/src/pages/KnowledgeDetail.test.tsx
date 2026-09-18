import { screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import KnowledgeDetail from './KnowledgeDetail';
import { renderWithProviders } from '@/test/render';
import { apiClient } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe('KnowledgeDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the article with its verified source and link', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: {
        id: '1',
        title: 'Как оформить производственную практику',
        content: 'Подайте заявление в деканат.',
        summary: 'Подайте заявление.',
        category: 'Учебный офис',
        audience: ['students'],
        source: { id: '1', name: 'Учебный офис', url: 'https://demo.local/practice', type: 'web' },
        sourceUrl: 'https://demo.local/practice',
        published: true,
        verified: true,
        verifiedStatus: 'verified',
        actualUntil: '2030-01-01',
        createdAt: '2026-09-09T00:00:00Z',
        updatedAt: '2026-09-09T00:00:00Z',
      },
    });

    renderWithProviders(<KnowledgeDetail />, {
      route: { path: '/knowledge/:id', initialEntry: '/knowledge/1' },
    });

    expect(await screen.findByText('Как оформить производственную практику')).toBeInTheDocument();
    expect(screen.getByText(/Подайте заявление в деканат/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /открыть источник/i })).toHaveAttribute('href', 'https://demo.local/practice');
  });
});
