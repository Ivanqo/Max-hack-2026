import { act, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import Opportunities from './Opportunities';
import { renderWithProviders } from '@/test/render';
import { apiClient } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';

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
    useAuthStore.setState({ user: null, token: null });
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

  it('does not show one student\'s cached opportunities while another account loads', async () => {
    let releaseMai: ((value: { data: any[] }) => void) | undefined;
    const maiResponse = new Promise<{ data: any[] }>((resolve) => { releaseMai = resolve; });
    const opportunity = (id: string, title: string) => ({
      id,
      title,
      company: 'Университет',
      location: 'Москва',
      type: 'internship',
      description: 'Тестовая возможность.',
      requirements: [],
      skills: [],
      status: 'active',
      published: true,
      verifiedStatus: 'verified',
      deadline: null,
      sourceUrl: '',
      matchPercentage: 70,
      matchReasons: [],
      gaps: [],
      isSaved: false,
      postedDate: '2026-09-09T00:00:00Z',
      createdAt: '2026-09-09T00:00:00Z',
      updatedAt: '2026-09-09T00:00:00Z',
    });
    const firstStudent = { id: 101, email: 'mgsu@test.local', name: 'Студент', role: 'student' };
    const secondStudent = { id: 202, email: 'mai@test.local', name: 'Студент', role: 'student' };
    useAuthStore.setState({ user: firstStudent, token: 'first-token' });
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url !== '/student/opportunities') return Promise.resolve({ data: [] });
      return useAuthStore.getState().user?.id === 101
        ? Promise.resolve({ data: [opportunity('14', 'Возможность МГСУ')] })
        : maiResponse;
    });

    const view = renderWithProviders(<Opportunities />);
    expect(await screen.findByText('Возможность МГСУ')).toBeInTheDocument();

    act(() => useAuthStore.setState({ user: secondStudent, token: 'second-token' }));
    expect(screen.queryByText('Возможность МГСУ')).not.toBeInTheDocument();

    await act(async () => releaseMai?.({ data: [opportunity('26', 'Возможность МАИ')] }));
    expect(await screen.findByText('Возможность МАИ')).toBeInTheDocument();
    view.unmount();
    useAuthStore.setState({ user: null, token: null });
  });
});
