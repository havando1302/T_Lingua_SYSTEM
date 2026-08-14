import { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { Search } from 'lucide-react';

const History = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const query = search ? `?search=${encodeURIComponent(search)}` : '';
      const res = await api.get(`/quality/logs${query}`);
      setLogs(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchLogs();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Lịch sử dịch thuật</h1>
        <p className="text-text-muted mt-2">Xem lại và tìm kiếm các yêu cầu dịch thuật đã xử lý.</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <CardTitle>Dữ liệu Audit</CardTitle>
              <CardDescription>Toàn bộ lịch sử các bản dịch được xử lý bởi hệ thống.</CardDescription>
            </div>
            <form onSubmit={handleSearch} className="flex items-center gap-2 w-full sm:w-auto">
              <Input
                placeholder="Tìm kiếm nội dung..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full sm:w-64"
                icon={<Search size={16} />}
              />
              <Button type="submit" isLoading={loading}>Tìm kiếm</Button>
            </form>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Khách hàng (Client)</TableHead>
                <TableHead className="w-1/3">Văn bản gốc</TableHead>
                <TableHead className="w-1/3">Bản dịch (AI)</TableHead>
                <TableHead>Độ trễ</TableHead>
                <TableHead>Thời gian</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center text-text-muted">
                    Không tìm thấy lịch sử nào.
                  </TableCell>
                </TableRow>
              ) : (
                logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="font-medium">#{log.id}</TableCell>
                    <TableCell>
                      <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-background text-text-muted border border-border">
                        {log.client_id || 'Không xác định'}
                      </span>
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate" title={log.source_text}>
                      {log.source_text}
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate" title={log.translated_text}>
                      {log.translated_text}
                    </TableCell>
                    <TableCell>{log.latency ? `${log.latency.toFixed(3)}s` : '-'}</TableCell>
                    <TableCell className="text-text-muted">
                      {new Date(log.created_at).toLocaleString('vi-VN')}
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

export default History;
