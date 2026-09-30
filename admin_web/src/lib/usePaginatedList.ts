import { useCallback, useEffect, useRef, useState } from 'react';
import api, { apiErrorMessage } from './api';

const PAGE_SIZE = 25;

// Keep the visible page and its applied filter together until a new request succeeds.
export function usePaginatedList<T>(endpoint: string, fixedParams = '') {
  const [items, setItems] = useState<T[]>([]);
  const [search, setSearch] = useState('');
  const [appliedSearch, setAppliedSearch] = useState('');
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState('');
  const controllerRef = useRef<AbortController | null>(null);
  const visibleRef = useRef({ page: 0, search: '' });

  const fetchPage = useCallback(async (targetPage: number, query: string) => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setFetching(true);
    setError('');
    try {
      const params = new URLSearchParams(fixedParams);
      params.set('skip', String(targetPage * PAGE_SIZE));
      params.set('limit', String(PAGE_SIZE + 1));
      if (query.trim()) params.set('search', query.trim());
      const response = await api.get<T[]>(endpoint, { params, signal: controller.signal });
      if (controller.signal.aborted) return;
      if (!Array.isArray(response.data)) throw new Error('Danh sách trả về không hợp lệ.');
      setItems(response.data.slice(0, PAGE_SIZE));
      setHasMore(response.data.length > PAGE_SIZE);
      setPage(targetPage);
      setAppliedSearch(query.trim());
      visibleRef.current = { page: targetPage, search: query.trim() };
    } catch (err) {
      if (!controller.signal.aborted) setError(apiErrorMessage(err));
    } finally {
      if (!controller.signal.aborted) setFetching(false);
    }
  }, [endpoint, fixedParams]);

  useEffect(() => {
    // Changing a server filter starts at its first page, keeping the submitted search.
    setItems([]);
    setPage(0);
    setHasMore(false);
    void fetchPage(0, visibleRef.current.search);
    return () => controllerRef.current?.abort();
  }, [fetchPage]);

  return {
    items, setItems, search, setSearch, appliedSearch, page, hasMore, fetching, error,
    submitSearch: () => fetchPage(0, search),
    previous: () => fetchPage(Math.max(0, page - 1), appliedSearch),
    next: () => fetchPage(page + 1, appliedSearch),
    refresh: () => fetchPage(page, appliedSearch),
    firstPage: () => fetchPage(0, appliedSearch),
  };
}
