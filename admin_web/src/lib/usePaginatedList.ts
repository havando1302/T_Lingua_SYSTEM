import { useCallback, useEffect, useRef, useState } from 'react';
import api, { apiErrorMessage, locallyHandledRequest } from './api';

const PAGE_SIZE = 25;

interface CacheRecord<T> {
  items: T[];
  hasMore: boolean;
  page: number;
  search: string;
  timestamp: number;
}

// Global in-memory cache preserving table items across tab navigations
const listCache = new Map<string, CacheRecord<any>>();

export function usePaginatedList<T>(endpoint: string, fixedParams = '') {
  const cacheKey = `${endpoint}?${fixedParams}`;
  const cached = listCache.get(cacheKey);

  const [items, setItems] = useState<T[]>(() => (cached?.items as T[]) || []);
  const [search, setSearch] = useState(() => cached?.search || '');
  const [appliedSearch, setAppliedSearch] = useState(() => cached?.search || '');
  const [page, setPage] = useState(() => cached?.page || 0);
  const [hasMore, setHasMore] = useState(() => cached?.hasMore || false);
  const [fetching, setFetching] = useState(() => !cached);
  const [error, setError] = useState('');
  const controllerRef = useRef<AbortController | null>(null);
  const visibleRef = useRef({ page: cached?.page || 0, search: cached?.search || '' });

  const fetchPage = useCallback(async (targetPage: number, query: string, showLoading = true) => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    if (showLoading) setFetching(true);
    setError('');
    try {
      const params = new URLSearchParams(fixedParams);
      params.set('skip', String(targetPage * PAGE_SIZE));
      params.set('limit', String(PAGE_SIZE + 1));
      if (query.trim()) params.set('search', query.trim());
      const response = await api.get<T[]>(endpoint, { ...locallyHandledRequest, params, signal: controller.signal });
      if (controller.signal.aborted) return;
      if (!Array.isArray(response.data)) throw new Error('Danh sách trả về không hợp lệ.');
      const newItems = response.data.slice(0, PAGE_SIZE);
      const newHasMore = response.data.length > PAGE_SIZE;
      setItems(newItems);
      setHasMore(newHasMore);
      setPage(targetPage);
      setAppliedSearch(query.trim());
      visibleRef.current = { page: targetPage, search: query.trim() };
      listCache.set(cacheKey, {
        items: newItems,
        hasMore: newHasMore,
        page: targetPage,
        search: query.trim(),
        timestamp: Date.now(),
      });
    } catch (err) {
      if (!controller.signal.aborted) setError(apiErrorMessage(err));
    } finally {
      if (!controller.signal.aborted) setFetching(false);
    }
  }, [endpoint, fixedParams, cacheKey]);

  useEffect(() => {
    // If cached data exists, fetch quietly in background without flashing blank
    const hasCached = !!listCache.get(cacheKey);
    void fetchPage(visibleRef.current.page, visibleRef.current.search, !hasCached);
    return () => controllerRef.current?.abort();
  }, [fetchPage, cacheKey]);

  return {
    items, setItems, search, setSearch, appliedSearch, page, hasMore, fetching, error,
    submitSearch: () => fetchPage(0, search, true),
    previous: () => fetchPage(Math.max(0, page - 1), appliedSearch, true),
    next: () => fetchPage(page + 1, appliedSearch, true),
    refresh: () => fetchPage(page, appliedSearch, false),
    firstPage: () => fetchPage(0, appliedSearch, true),
  };
}
