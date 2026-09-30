import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';

interface ListState {
  search: string;
  setSearch: (value: string) => void;
  appliedSearch: string;
  page: number;
  items: unknown[];
  hasMore: boolean;
  fetching: boolean;
  error: string;
  submitSearch: () => Promise<void>;
  previous: () => Promise<void>;
  next: () => Promise<void>;
  refresh: () => Promise<void>;
}

export function ListSearch({ list, label = 'Tìm kiếm nội dung' }: { list: ListState; label?: string }) {
  return <form onSubmit={(event) => { event.preventDefault(); void list.submitSearch(); }} className="flex flex-wrap items-end gap-2">
    <div className="flex-1 min-w-40"><Input label={label} maxLength={200} value={list.search}
      onChange={(event) => list.setSearch(event.target.value)} icon={<Search size={16} />} /></div>
    <Button type="submit" isLoading={list.fetching}>Tìm kiếm</Button>
  </form>;
}

export function ListStatus({ list }: { list: ListState }) {
  return <>
    {list.error && <div role="alert" className="mb-3 rounded-lg bg-red-500/10 p-3 text-red-600">
      {list.error} {list.items.length > 0 && 'Danh sách vẫn là dữ liệu tải lần trước.'}
      <Button variant="ghost" size="sm" onClick={() => void list.refresh()}>Thử lại</Button>
    </div>}
    {list.fetching && <p role="status" className="mb-3 text-sm text-text-muted">Đang tải danh sách…</p>}
    {list.appliedSearch && <p className="mb-3 text-sm text-text-muted">Đang lọc theo: “{list.appliedSearch}”</p>}
  </>;
}

export function ListPagination({ list, disabled = false }: { list: ListState; disabled?: boolean }) {
  return <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
    <span className="text-sm text-text-muted">Trang {list.page + 1} · {list.items.length} bản ghi trên trang</span>
    <div className="flex gap-2">
      <Button variant="secondary" size="sm" disabled={disabled || list.fetching || list.page === 0} onClick={() => void list.previous()}>
        <ChevronLeft size={16} /> Trước
      </Button>
      <Button variant="secondary" size="sm" disabled={disabled || list.fetching || !list.hasMore} onClick={() => void list.next()}>
        Sau <ChevronRight size={16} />
      </Button>
    </div>
  </div>;
}
