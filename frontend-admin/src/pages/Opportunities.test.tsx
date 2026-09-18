import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { Opportunities } from './Opportunities';
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
  title: 'Backend Internship',
  company: 'MAX Labs',
  description: 'Build APIs.',
  type: 'internship',
  location: 'Campus',
  remote: true,
  requirements: ['Python'],
  skills: [{ name: 'Python', level: 4, weight: 1 }],
  status: 'active',
  published: true,
  verifiedStatus: 'pending',
  deadline: '2030-01-15T00:00:00Z',
  sourceUrl: 'https://example.org/jobs/1',
  createdAt: '2026-09-09T00:00:00Z',
  updatedAt: '2026-09-09T00:00:00Z',
};

describe('Admin Opportunities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('lists real opportunity data including its verification status', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [sample] });

    renderWithRouter(<Opportunities />);

    // The desktop table and mobile card list both render in the DOM at once
    // (CSS breakpoints toggle visibility), so each row appears twice here.
    expect((await screen.findAllByText('Backend Internship')).length).toBeGreaterThan(0);
    expect(screen.getAllByText('На проверке').length).toBeGreaterThan(0);
  });

  it('submits edited fields to the update endpoint so changes persist', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [sample] });
    vi.mocked(api.put).mockResolvedValueOnce({ data: { ...sample, verifiedStatus: 'verified' } });

    renderWithRouter(<Opportunities />);

    const editButton = (await screen.findAllByLabelText('Редактировать'))[0];
    await userEvent.click(editButton);

    const statusSelect = await screen.findByLabelText('Статус проверки');
    await userEvent.selectOptions(statusSelect, 'verified');

    const submit = screen.getByRole('button', { name: 'Сохранить' });
    await userEvent.click(submit);

    await waitFor(() => expect(api.put).toHaveBeenCalledTimes(1));
    const [url, payload] = vi.mocked(api.put).mock.calls[0];
    expect(url).toBe('/admin/opportunities/1');
    expect(payload).toMatchObject({ title: 'Backend Internship', verifiedStatus: 'verified' });
  });
});
