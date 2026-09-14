import { screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import CareerGPS from './CareerGPS';
import { renderWithProviders } from '@/test/render';
import { apiClient } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe('CareerGPS', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders readiness, strengths, gaps, and next actions', async () => {
    vi.mocked(apiClient.get).mockImplementation(async (url: string) => {
      if (url === '/career/goals') {
        return {
          data: [
            { id: 1, title: 'Backend Developer', description: 'Build APIs.', category: 'Career role' },
          ],
        };
      }
      return {
        data: {
          goal: { id: 1, title: 'Backend Developer', description: 'Build APIs.', category: 'Career role' },
          readinessScore: 67,
          strengths: ['Python: уровень 4/5 покрывает требуемый 4/5'],
          gaps: [{ skill: 'Docker', currentLevel: 0, requiredLevel: 3, priority: 'high' }],
          nextActions: [{ id: 1, title: 'Подтянуть Docker', type: 'resource', estimatedTime: '1 week', priority: 1 }],
          lastUpdated: '2026-09-09T00:00:00Z',
        },
      };
    });

    renderWithProviders(<CareerGPS />);

    expect(await screen.findByText('67%')).toBeInTheDocument();
    expect(screen.getByText('Docker')).toBeInTheDocument();
    expect(screen.getByText('Подтянуть Docker')).toBeInTheDocument();
  });
});
