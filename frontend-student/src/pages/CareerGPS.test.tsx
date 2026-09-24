import { act, fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import CareerGPS from './CareerGPS';
import { renderWithProviders } from '@/test/render';
import { apiClient } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';

vi.mock('@/lib/api', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe('CareerGPS', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({ user: null, token: null });
  });

  it('renders readiness, strengths, gaps, and next actions', async () => {
    vi.mocked(apiClient.get).mockImplementation(async (url: string) => {
      if (url === '/career/goals') {
        return {
          data: [
            { id: 1, title: 'Бэкенд-разработчик', description: 'Разработка API.', category: 'Карьерная роль' },
          ],
        };
      }
      return {
        data: {
          goal: { id: 1, title: 'Бэкенд-разработчик', description: 'Разработка API.', category: 'Карьерная роль' },
          readinessScore: 67,
          strengths: ['Python: уровень 4/5 покрывает требуемый 4/5'],
          gaps: [{ skill: 'Docker', currentLevel: 0, requiredLevel: 3, priority: 'high' }],
          nextActions: [{ id: 1, title: 'Подтянуть Docker', type: 'resource', estimatedTime: '1 неделя', priority: 1 }],
          lastUpdated: '2026-09-09T00:00:00Z',
        },
      };
    });

    renderWithProviders(<CareerGPS />);

    expect(await screen.findByText('67%')).toBeInTheDocument();
    expect(screen.getByText('Docker')).toBeInTheDocument();
    expect(screen.getByText('Подтянуть Docker')).toBeInTheDocument();
  });

  it('drops the previous account analysis and reloads after retry', async () => {
    const firstStudent = { id: 101, email: 'mgsu@test.local', name: 'Student A', role: 'student' };
    const secondStudent = { id: 202, email: 'mai@test.local', name: 'Student B', role: 'student' };
    useAuthStore.setState({ user: firstStudent, token: 'student-a-token' });
    let maiAnalysisAttempts = 0;
    vi.mocked(apiClient.get).mockImplementation(async (url: string) => {
      const currentUserId = useAuthStore.getState().user?.id;
      if (url === '/career/goals') {
        return { data: [{ id: currentUserId === 101 ? 1 : 2, title: currentUserId === 101 ? 'Цель МГСУ' : 'Цель МАИ', description: 'Описание' }] };
      }
      if (currentUserId === 202 && ++maiAnalysisAttempts <= 3) throw new Error('temporary error');
      const readinessScore = currentUserId === 101 ? 62 : 47;
      return {
        data: {
          goal: { id: currentUserId === 101 ? 1 : 2, title: currentUserId === 101 ? 'Цель МГСУ' : 'Цель МАИ', description: 'Описание' },
          readinessScore,
          strengths: [],
          gaps: [],
          nextActions: [],
          lastUpdated: '2026-09-09T00:00:00Z',
        },
      };
    });

    const view = renderWithProviders(<CareerGPS />);
    expect(await screen.findByText('62%')).toBeInTheDocument();

    act(() => useAuthStore.setState({ user: secondStudent, token: 'student-b-token' }));
    expect(screen.queryByText('62%')).not.toBeInTheDocument();
    expect(await screen.findByRole('button', { name: 'Повторить' }, { timeout: 5000 })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Повторить' }));
    expect(await screen.findByText('47%')).toBeInTheDocument();
    await waitFor(() => expect(maiAnalysisAttempts).toBe(4));
    view.unmount();
    useAuthStore.setState({ user: null, token: null });
  });
});
