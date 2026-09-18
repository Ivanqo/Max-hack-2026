import { screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { CareerRoles } from './CareerRoles';
import { renderWithRouter } from '@/test/render';
import api from '@/api/client';

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('Admin CareerRoles', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the real persisted salary and education path instead of hardcoded placeholders', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: [
        {
          id: '1',
          title: 'Backend Developer',
          description: 'Build APIs.',
          skills: ['Python', 'Django'],
          skillLevels: [{ name: 'Python', level: 4 }],
          avgSalary: '150 000 - 220 000 ₽',
          demandLevel: 'high',
          active: true,
          educationPath: ['Learn Python', 'Ship a project'],
          createdAt: '2026-09-09T00:00:00Z',
          updatedAt: '2026-09-09T00:00:00Z',
        },
      ],
    });

    renderWithRouter(<CareerRoles />);

    expect(await screen.findByText('Backend Developer')).toBeInTheDocument();
    expect(screen.getByText('150 000 - 220 000 ₽')).toBeInTheDocument();
    expect(screen.getByText('Высокий спрос')).toBeInTheDocument();
  });
});
