import { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Copy, Plus, Trash2 } from 'lucide-react';

const ApiKeys = () => {
  const [keys, setKeys] = useState<any[]>([]);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchKeys = async () => {
    try {
      const res = await api.get('/apikeys');
      setKeys(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    try {
      await api.post('/apikeys', { name });
      setName('');
      fetchKeys();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Bạn có chắc chắn muốn thu hồi và xóa mã kết nối này không?')) return;
    try {
      await api.delete(`/apikeys/${id}`);
      fetchKeys();
    } catch (err) {
      console.error(err);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Đã chép vào bộ nhớ đệm!');
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Mã kết nối (API Keys)</h1>
        <p className="text-text-muted mt-2">Quản lý mã kết nối cho các ứng dụng và phần mềm bên ngoài.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Tạo Mã mới</CardTitle>
          <CardDescription>Sinh mã API mới để cấp quyền truy cập hệ thống dịch thuật.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="flex gap-4 items-end">
            <div className="flex-1 max-w-sm">
              <Input
                label="Tên mã (Dự án / App)"
                placeholder="VD: Ứng dụng Mobile Android"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <Button type="submit" isLoading={loading}>
              <Plus size={18} className="mr-2" />
              Tạo mã
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Danh sách Mã API đang hoạt động</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Tên/Dự án</TableHead>
                <TableHead>Mã (Key)</TableHead>
                <TableHead>Ngày tạo</TableHead>
                <TableHead className="text-right">Thao tác</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {keys.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="h-24 text-center text-text-muted">
                    Chưa có mã kết nối nào.
                  </TableCell>
                </TableRow>
              ) : (
                keys.map((k) => (
                  <TableRow key={k.id}>
                    <TableCell className="font-medium">{k.name}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2 font-mono text-sm">
                        <span className="blur-sm hover:blur-none transition-all cursor-pointer" onClick={() => copyToClipboard(k.key)} title="Nhấp để hiển thị">
                          {k.key}
                        </span>
                        <Button variant="ghost" size="sm" onClick={() => copyToClipboard(k.key)} className="h-8 w-8 p-0" title="Sao chép">
                          <Copy size={14} />
                        </Button>
                      </div>
                    </TableCell>
                    <TableCell className="text-text-muted">
                      {new Date(k.created_at).toLocaleDateString('vi-VN')}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="danger" size="sm" onClick={() => handleDelete(k.id)}>
                        <Trash2 size={16} />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default ApiKeys;
