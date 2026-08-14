import { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Trash2, UserPlus } from 'lucide-react';

const Users = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('employee');
  const [loading, setLoading] = useState(false);

  const fetchUsers = async () => {
    try {
      const res = await api.get('/users');
      setUsers(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post('/users', { username, password, role });
      setUsername('');
      setPassword('');
      setRole('employee');
      fetchUsers();
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || 'Có lỗi xảy ra');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Bạn có chắc chắn muốn xóa tài khoản này?')) return;
    try {
      await api.delete(`/users/${id}`);
      fetchUsers();
    } catch (err) {
      alert('Không thể xóa superadmin hoặc có lỗi xảy ra.');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Quản lý Nhân sự</h1>
        <p className="text-text-muted mt-2">Thêm mới, xóa và phân quyền các tài khoản quản trị.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Tạo Tài khoản mới</CardTitle>
          <CardDescription>Cấp tài khoản cho nhân viên hoặc người quản lý hệ thống.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="flex flex-col sm:flex-row gap-4 items-end">
            <div className="flex-1">
              <Input label="Tên đăng nhập" value={username} onChange={(e) => setUsername(e.target.value)} required />
            </div>
            <div className="flex-1">
              <Input type="password" label="Mật khẩu" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-text-muted mb-1">Chức vụ (Quyền)</label>
              <select 
                className="flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                value={role} 
                onChange={(e) => setRole(e.target.value)}
              >
                <option value="employee">Nhân viên (Employee)</option>
                <option value="admin">Quản trị viên (Admin)</option>
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
        </CardHeader>
        <CardContent>
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
              {users.map((u) => (
                <TableRow key={u.id}>
                  <TableCell>#{u.id}</TableCell>
                  <TableCell className="font-medium">{u.username}</TableCell>
                  <TableCell>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                      u.role === 'superadmin' ? 'bg-primary text-surface border-primary' : 
                      u.role === 'admin' ? 'bg-blue-500/10 text-blue-500 border-blue-500/20' : 
                      'bg-border/50 text-text border-border'
                    }`}>
                      {u.role.toUpperCase()}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    {u.role !== 'superadmin' && (
                      <Button variant="danger" size="sm" onClick={() => handleDelete(u.id)}>
                        <Trash2 size={16} />
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default Users;
