import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render } from '@testing-library/react';
import type { ReactElement } from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ToastProvider } from '@/ui';

interface RenderOptions {
  /** When set, wraps `ui` in a <Route path=...> and starts the router at this entry. */
  route?: { path: string; initialEntry: string };
}

export function renderWithProviders(ui: ReactElement, options: RenderOptions = {}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  const tree = options.route ? (
    <MemoryRouter initialEntries={[options.route.initialEntry]}>
      <Routes>
        <Route path={options.route.path} element={ui} />
      </Routes>
    </MemoryRouter>
  ) : (
    <MemoryRouter>{ui}</MemoryRouter>
  );

  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>{tree}</ToastProvider>
    </QueryClientProvider>,
  );
}
