import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

export const userQueryKey = (userId: number | null, ...parts: unknown[]) => [
  'account',
  userId ?? 'anonymous',
  ...parts,
]
