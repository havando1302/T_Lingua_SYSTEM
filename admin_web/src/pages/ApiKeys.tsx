import { useEffect, useRef, useState } from 'react';
import api, { apiErrorMessage } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Copy, Plus, RefreshCw, Trash2 } from 'lucide-react';
import { usePaginatedList } from '../lib/usePaginatedList';
import { ListSearch, ListStatus, ListPagination } from '../components/ListControls';
import { formatApiDate, parseApiDate } from '../lib/date';

interface ApiKeyMetadata {
  id: number;
  name: string;
  prefix: string;
  scopes: string[];
  expires_at: string | null;
  created_at: string;
  is_active: boolean;
}

function NewKeyDialog({ secret, onClose }: { secret: string; onClose: () => void }) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [copyStatus, setCopyStatus] = useState('');
  useEffect(() => { dialogRef.current?.showModal(); }, []);
  const copySecret = async () => {
    try {
      await navigator.clipboard.writeText(secret);
      setCopyStatus('Đã sao chép. Hãy lưu mã ở nơi an toàn.');
    } catch {
      setCopyStatus('Không thể sao chép tự động. Bạn có thể chọn và sao chép mã trong ô bên dưới.');
    }
  };
  return <dialog ref={dialogRef} onCancel={onClose} aria-labelledby="new-key-title"
    className="m-auto w-full max-w-xl rounded-xl border border-border bg-surface p-6 text-text shadow-xl backdrop:bg-black/60">
    <h2 id="new-key-title" className="text-xl font-bold">Mã API mới</h2>
    <p className="my-4 text-text-muted">Mã đầy đủ chỉ được hiển thị lần này. Lưu mã trước khi đóng cửa sổ; bạn sẽ không thể xem lại.</p>
    <textarea aria-label="Mã API đầy đủ" readOnly value={secret} rows={3}
      className="w-full rounded-lg border border-border bg-background p-3 font-mono text-sm" />
    <p role="status" className="my-3 text-sm">{copyStatus}</p>
    <div className="flex justify-end gap-3">
      <Button variant="secondary" onClick={copySecret}><Copy size={16} className="mr-2" />Sao chép</Button>
      <Button onClick={onClose}>Đã lưu, đóng cửa sổ</Button>
    </div>
  </dialog>;
}

const ApiKeys = () => {
  const list = usePaginatedList<ApiKeyMetadata>('/apikeys');
  const keys = list.items;
  const [deleting, setDeleting] = useState<number | null>(null);
  const [rotating, setRotating] = useState<number | null>(null);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [expiresInDays, setExpiresInDays] = useState(30);
  const [scopes, setScopes] = useState<string[]>(['translate', 'audio']);
  const [createdSecret, setCreatedSecret] = useState<string | null>(null);
  const [error, setError] = useState('');

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading || createdSecret) return;
    if (!name.trim()) { setError('Vui lòng nhập tên mã API.'); return; }
    if (scopes.length === 0 || !Number.isInteger(expiresInDays) || expiresInDays < 1 || expiresInDays > 90) {
      setError('Chọn ít nhất một quyền và thời hạn từ 1 đến 90 ngày.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const response = await api.post<ApiKeyMetadata & { key: string }>('/apikeys', {
        name: name.trim(), scopes, expires_in_days: expiresInDays,
      });
      if (typeof response.data.key !== 'string' || !response.data.key) {
        throw new Error('Máy chủ chưa trả mã mới. Kiểm tra danh sách trước khi tạo lại.');
      }
      setCreatedSecret(response.data.key);
      setName('');
      await list.firstPage();
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (deleting !== null) return;
    if (!confirm('Bạn có chắc chắn muốn thu hồi và xóa mã kết nối này không?')) return;
    setDeleting(id);
    setError('');
    try {
      await api.delete(`/apikeys/${id}`);
      await list.refresh();
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally { setDeleting(null); }
  };

  const handleRotate = async (id: number, keyName: string) => {
    if (rotating !== null || deleting !== null || createdSecret) return;
    if (!confirm(`Tạo mã mới và thu hồi ngay mã ${keyName}?`)) return;
    setRotating(id); setError('');
    try {
      const response = await api.post<ApiKeyMetadata & { key: string }>(`/apikeys/${id}/rotate`);
      setCreatedSecret(response.data.key);
      await list.refresh();
    } catch (err) {
      setError(apiErrorMessage(err, 'Không thể luân chuyển mã API.'));
    } finally { setRotating(null); }
  };

  return (
    <div className="space-y-6">
      {createdSecret && <NewKeyDialog secret={createdSecret} onClose={() => setCreatedSecret(null)} />}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Mã kết nối (API Keys)</h1>
        <p className="text-text-muted mt-2">Quản lý mã kết nối cho các ứng dụng và phần mềm bên ngoài.</p>
      </div>
      {error && <p role="alert" className="rounded-lg bg-red-500/10 p-4 text-red-600 dark:text-red-400">{error}</p>}

      <Card>
        <CardHeader>
          <CardTitle>Tạo Mã mới</CardTitle>
          <CardDescription>Sinh mã API mới để cấp quyền truy cập hệ thống dịch thuật.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 max-w-sm">
              <Input
                label="Tên mã (Dự án / App)"
                maxLength={100}
                placeholder="VD: Ứng dụng Mobile Android"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <Input label="Thời hạn (ngày)" type="number" min={1} max={90} step={1}
              value={expiresInDays} onChange={(event) => setExpiresInDays(Number(event.target.value))} required />
            <fieldset className="space-y-2">
              <legend className="text-sm text-text-muted">Quyền truy cập</legend>
              {([['translate', 'Dịch thuật'], ['audio', 'Âm thanh'], ['tm:read', 'Đọc bộ nhớ cá nhân'], ['tm:write', 'Sửa bộ nhớ cá nhân'], ['flag', 'Báo lỗi bản dịch']] as const).map(([scope, label]) => <label key={scope} className="mr-4 inline-flex items-center gap-2 text-sm">
                <input type="checkbox" checked={scopes.includes(scope)} onChange={(event) => {
                  setScopes((previous) => event.target.checked ? [...previous, scope] : previous.filter((value) => value !== scope));
                }} />{label}
              </label>)}
            </fieldset>
            <Button type="submit" isLoading={loading}>
              <Plus size={18} className="mr-2" />
              Tạo mã
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Danh sách Mã API</CardTitle>
          <ListSearch list={list} label="Tìm tên hoặc tiền tố mã API" />
        </CardHeader>
        <CardContent>
          <ListStatus list={list} />
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Tên/Dự án</TableHead>
                <TableHead>Tiền tố</TableHead>
                <TableHead>Quyền</TableHead>
                <TableHead>Hết hạn</TableHead>
                <TableHead>Trạng thái</TableHead>
                <TableHead className="text-right">Thao tác</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {keys.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center text-text-muted">
                    {list.fetching ? 'Đang tải…' : list.error ? 'Chưa tải được mã kết nối.' : 'Không tìm thấy mã kết nối.'}
                  </TableCell>
                </TableRow>
              ) : (
                keys.map((k) => (
                  <TableRow key={k.id}>
                    <TableCell className="font-medium">{k.name}</TableCell>
                    <TableCell>
                      <span className="font-mono text-sm">{k.prefix}…</span>
                    </TableCell>
                    <TableCell>{k.scopes.join(', ')}</TableCell>
                    <TableCell className="text-text-muted">
                      {formatApiDate(k.expires_at)}
                    </TableCell>
                    <TableCell>{!k.is_active ? 'Đã thu hồi' : !k.expires_at || parseApiDate(k.expires_at).getTime() <= Date.now() ? 'Đã hết hạn' : 'Đang hoạt động'}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="secondary" size="sm" onClick={() => handleRotate(k.id, k.name)} disabled={!k.is_active || deleting !== null || rotating !== null} isLoading={rotating === k.id} aria-label={`Luân chuyển mã ${k.name}`}>
                        <RefreshCw size={16} />
                      </Button>
                      <Button variant="danger" size="sm" onClick={() => handleDelete(k.id)} disabled={!k.is_active || deleting !== null || rotating !== null} isLoading={deleting === k.id} aria-label={`Thu hồi mã ${k.name}`}>
                        <Trash2 size={16} />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
          <ListPagination list={list} />
        </CardContent>
      </Card>
    </div>
  );
};

export default ApiKeys;
