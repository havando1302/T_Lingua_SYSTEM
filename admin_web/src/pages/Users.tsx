import { Fragment, useState } from 'react';
import api, { apiErrorMessage } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Pencil, RefreshCw, Save, Trash2, UserPlus, X } from 'lucide-react';
import { usePaginatedList } from '../lib/usePaginatedList';
import { ListSearch, ListStatus, ListPagination } from '../components/ListControls';

const Users = () => {
  const list = usePaginatedList<any>('/users');
  const users = list.items;
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState<number | null>(null);
  const [resetting, setResetting] = useState<number | null>(null);
  const [editing, setEditing] = useState<number | null>(null);
  const [updating, setUpdating] = useState(false);
  const [editRole, setEditRole] = useState('employee');
  const [editPassword, setEditPassword] = useState('');
  const [editActive, setEditActive] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('employee');
  const [loading, setLoading] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;
    if (username.trim().length < 3 || /\s/.test(username.trim())) { setError('Tên đăng nhập cần ít nhất 3 ký tự, không chứa khoảng trắng.'); return; }
    if (new TextEncoder().encode(password).length > 72) { setError('Mật khẩu tối đa 72 byte UTF-8. Ký tự có dấu có thể chiếm nhiều byte.'); return; }
    setError('');
    setLoading(true);
    try {
      await api.post('/users', { username: username.trim(), password, role });
      setUsername('');
      setPassword('');
      setRole('employee');
      await list.firstPage();
    } catch (err: unknown) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (deleting !== null) return;
    if (!confirm('Vô hiệu hóa tài khoản và thu hồi các phiên đăng nhập của người dùng này?')) return;
    setDeleting(id);
    setError('');
    try {
      await api.delete(`/users/${id}`);
      await list.refresh();
    } catch (err) {
      setError(apiErrorMessage(err, 'Không thể vô hiệu hóa tài khoản này.'));
    } finally { setDeleting(null); }
  };

  const handleResetSessions = async (id: number, username: string) => {
    if (resetting !== null || deleting !== null) return;
    if (!confirm(`Thu hồi toàn bộ phiên và API key do ${username} sở hữu/tạo?`)) return;
    setResetting(id); setError('');
    try {
      await api.post(`/users/${id}/reset-sessions`);
    } catch (err) {
      setError(apiErrorMessage(err, 'Không thể thu hồi phiên đăng nhập.'));
    } finally { setResetting(null); }
  };

  const startEditing = (user: any) => {
    setEditing(user.id);
    setEditRole(user.role);
    setEditPassword('');
    setEditActive(user.is_active !== false);
    setError('');
  };

  const handleUpdate = async (id: number) => {
    if (updating) return;
    if (editPassword && new TextEncoder().encode(editPassword).length > 72) {
      setError('Mật khẩu tối đa 72 byte UTF-8.');
      return;
    }
    setUpdating(true); setError('');
    try {
      await api.patch(`/users/${id}`, {
        role: editRole,
        is_active: editActive,
        ...(editPassword ? { password: editPassword } : {}),
      });
      setEditing(null);
      setEditPassword('');
      await list.refresh();
    } catch (err) {
      setError(apiErrorMessage(err, 'Không thể cập nhật tài khoản.'));
    } finally { setUpdating(false); }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Quản lý Nhân sự</h1>
      </div>

      {error && <p role="alert" className="text-red-600">{error}</p>}
      <Card>
        <CardHeader>
          <CardTitle>Tạo Tài khoản mới</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="flex flex-col sm:flex-row gap-4 items-end">
            <div className="flex-1">
              <Input label="Tên đăng nhập" minLength={3} maxLength={100} autoComplete="off" value={username} onChange={(e) => setUsername(e.target.value)} required />
            </div>
            <div className="flex-1">
              <Input type="password" label="Mật khẩu (ít nhất 12 ký tự)" minLength={12} maxLength={72} autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            <div className="flex-1">
              <label htmlFor="new-user-role" className="block text-sm font-medium text-text-muted mb-1">Chức vụ (Quyền)</label>
              <select id="new-user-role"
                className="flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                value={role} 
                onChange={(e) => setRole(e.target.value)}
              >
                <option value="employee">Nhân viên (Employee)</option>
                <option value="admin">Quản trị viên (Admin)</option>
                <option value="superadmin">Quản trị cấp cao (Superadmin)</option>
              </select>
            </div>
            <Button type="submit" isLoading={loading}>
              <UserPlus size={18} className="mr-2" />
              Tạo mới
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Danh sách Tài khoản</CardTitle>
          <ListSearch list={list} label="Tìm tên đăng nhập" />
        </CardHeader>
        <CardContent>
          <ListStatus list={list} />
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Tên đăng nhập</TableHead>
                <TableHead>Quyền hạn</TableHead>
                <TableHead className="text-right">Thao tác</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.length === 0 && <TableRow><TableCell colSpan={4} className="text-center text-text-muted">
                {list.fetching ? 'Đang tải…' : list.error ? 'Chưa tải được tài khoản.' : 'Không tìm thấy tài khoản.'}
              </TableCell></TableRow>}
              {users.map((u) => (
                <Fragment key={u.id}>
                <TableRow>
                  <TableCell>#{u.id}</TableCell>
                  <TableCell className="font-medium">{u.username}{u.is_active === false && <span className="ml-2 text-xs text-text-muted">Đã vô hiệu hóa</span>}</TableCell>
                  <TableCell>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                      u.role === 'superadmin' ? 'bg-primary text-white border-primary shadow-sm' : 
                      u.role === 'admin' ? 'bg-blue-500/10 text-blue-500 border-blue-500/20' : 
                      'bg-border/50 text-text border-border'
                    }`}>
                      {u.role.toUpperCase()}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    {u.role !== 'superadmin' && <Button variant="ghost" size="sm" onClick={() => startEditing(u)} disabled={updating || deleting !== null} aria-label={`Chỉnh sửa ${u.username}`}>
                      <Pencil size={16} />
                    </Button>}
                    {u.is_active !== false && <Button variant="secondary" size="sm" onClick={() => handleResetSessions(u.id, u.username)} disabled={resetting !== null || deleting !== null} isLoading={resetting === u.id} aria-label={`Thu hồi phiên ${u.username}`}>
                      <RefreshCw size={16} />
                    </Button>}
                    {u.role !== 'superadmin' && u.is_active !== false && (
                      <Button variant="danger" size="sm" onClick={() => handleDelete(u.id)} disabled={deleting !== null} isLoading={deleting === u.id} aria-label={`Vô hiệu hóa ${u.username}`}>
                        <Trash2 size={16} />
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
                {editing === u.id && <TableRow>
                  <TableCell colSpan={4}>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end rounded border border-border p-3">
                      <div><label htmlFor={`edit-user-role-${u.id}`} className="text-sm">Quyền của {u.username}</label>
                        <select id={`edit-user-role-${u.id}`} className="mt-1 block w-full rounded border border-border bg-surface p-2" value={editRole} onChange={(event) => setEditRole(event.target.value)} disabled={updating}>
                          <option value="employee">Nhân viên</option><option value="admin">Quản trị viên</option>
                        </select>
                      </div>
                      <Input type="password" label={`Mật khẩu mới của ${u.username} (để trống nếu giữ nguyên)`} minLength={12} maxLength={72} autoComplete="new-password" value={editPassword} onChange={(event) => setEditPassword(event.target.value)} disabled={updating} />
                      <label className="flex items-center gap-2 pb-2 text-sm"><input type="checkbox" checked={editActive} onChange={(event) => setEditActive(event.target.checked)} disabled={updating} /> Tài khoản hoạt động</label>
                      <div className="flex gap-2">
                        <Button size="sm" onClick={() => handleUpdate(u.id)} isLoading={updating}><Save size={16} className="mr-1" />Lưu</Button>
                        <Button size="sm" variant="ghost" onClick={() => setEditing(null)} disabled={updating}><X size={16} className="mr-1" />Hủy</Button>
                      </div>
                    </div>
                  </TableCell>
                </TableRow>}
                </Fragment>
              ))}
            </TableBody>
          </Table>
          <ListPagination list={list} />
        </CardContent>
      </Card>
    </div>
  );
};

export default Users;
