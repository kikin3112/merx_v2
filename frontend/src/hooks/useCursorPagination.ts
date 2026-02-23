/**
 * Hook para paginación cursor-based usando TanStack Query's useInfiniteQuery.
 * Garantiza consistencia cuando se insertan/eliminan registros concurrentemente
 * (sin saltos ni duplicados que ocurren con offset pagination).
 */
import { useInfiniteQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import client from '../api/client';

interface CursorPage<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
}

export function useCursorPagination<T>(
  endpoint: string,
  queryKey: unknown[],
  params?: Record<string, unknown>,
  limit = 50,
) {
  const query = useInfiniteQuery<CursorPage<T>>({
    queryKey: [...queryKey, params],
    queryFn: ({ pageParam }) =>
      client
        .get<CursorPage<T>>(endpoint, {
          params: {
            ...params,
            ...(pageParam ? { cursor: pageParam } : {}),
            limit,
          },
        })
        .then((r) => r.data),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    staleTime: 30_000,
  });

  const allItems = useMemo(
    () => query.data?.pages.flatMap((p) => p.items) ?? [],
    [query.data],
  );

  return {
    ...query,
    allItems,
    hasMore: query.hasNextPage,
    loadMore: query.fetchNextPage,
  };
}
