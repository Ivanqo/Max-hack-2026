import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import Knowledge from './Knowledge';
import { renderWithProviders } from '@/test/render';
import { apiClient } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe('Knowledge', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders verified source details from search results', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        query: 'практика',
        total: 1,
        results: [
          {
            id: '1',
            title: 'Как оформить производственную практику',
            content: 'Подайте заявление.',
            summary: 'Подайте заявление.',
            source: { id: '1', name: 'Учебный офис', url: 'https://demo.local/practice', type: 'web' },
            verified: true,
            relevanceScore: 1,
            createdAt: '2026-09-09T00:00:00Z',
            updatedAt: '2026-09-09T00:00:00Z',
          },
        ],
      },
    });

    renderWithProviders(<Knowledge />);
    await userEvent.type(screen.getByLabelText(/поиск по базе знаний/i), 'практика');

    expect(await screen.findByText('Как оформить производственную практику')).toBeInTheDocument();
    expect(screen.getByText('Учебный офис')).toBeInTheDocument();
  });

  it('renders safe fallback when backend has no verified answer', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        found: false,
        query: 'unknown',
        total: 0,
        results: [],
        message: 'Не найден подтвержденный актуальный материал.',
        escalation: { unit: 'Учебный офис', contact: 'helpdesk@demo.local' },
      },
    });

    renderWithProviders(<Knowledge />);
    await userEvent.type(screen.getByLabelText(/поиск по базе знаний/i), 'unknown');

    await waitFor(() => expect(screen.getByText('Не найден подтвержденный актуальный материал.')).toBeInTheDocument());
    expect(screen.getByText(/helpdesk@demo.local/)).toBeInTheDocument();
  });
});
