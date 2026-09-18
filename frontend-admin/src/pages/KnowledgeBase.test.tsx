import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { KnowledgeBase } from './KnowledgeBase';
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

const sample = {
  id: '1',
  title: 'How to apply for practice',
  content: 'Visit the career office.',
  category: 'Career Center',
  responsibleUnit: 'Career Center',
  audience: ['students'],
  tags: ['students'],
  sourceUrl: 'https://example.org/practice',
  published: false,
  verified: false,
  verifiedStatus: 'draft',
  actualUntil: null,
  createdAt: '2026-09-09T00:00:00Z',
  updatedAt: '2026-09-09T00:00:00Z',
};

describe('Admin KnowledgeBase', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('lists articles with their real draft/published status', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [sample] });

    renderWithRouter(<KnowledgeBase />);

    expect(await screen.findByText('How to apply for practice')).toBeInTheDocument();
    expect(screen.getByText('Черновик')).toBeInTheDocument();
  });

  it('publishing an article sends published:true to the backend', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [sample] });
    vi.mocked(api.put).mockResolvedValueOnce({ data: { ...sample, published: true } });

    renderWithRouter(<KnowledgeBase />);

    const editButton = (await screen.findAllByLabelText('Редактировать'))[0];
    await userEvent.click(editButton);

    const publishSwitch = await screen.findByRole('switch', { name: /Опубликовано/i });
    await userEvent.click(publishSwitch);

    const submit = screen.getByRole('button', { name: 'Сохранить' });
    await userEvent.click(submit);

    await waitFor(() => expect(api.put).toHaveBeenCalledTimes(1));
    const [url, payload] = vi.mocked(api.put).mock.calls[0];
    expect(url).toBe('/admin/knowledge/1');
    expect(payload).toMatchObject({ published: true });
  });
});
