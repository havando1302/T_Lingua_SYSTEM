import { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Button } from '../components/ui/Button';
import { Check, Edit2, AlertCircle } from 'lucide-react';

const QA = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [correctedText, setCorrectedText] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchFlaggedLogs = async () => {
    try {
      const res = await api.get('/quality/logs?flagged_only=true');
      setLogs(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchFlaggedLogs();
  }, []);

  const handleResolve = async (id: number) => {
    setLoading(true);
    try {
      await api.post(`/quality/logs/${id}/resolve`, {
        corrected_text: correctedText
      });
      setEditingId(null);
      setCorrectedText('');
      fetchFlaggedLogs();
    } catch (err) {
      console.error(err);
      alert('Lỗi khi giải quyết bản dịch');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Cải thiện QA</h1>
        <p className="text-text-muted mt-2">Sửa các bản dịch lỗi do người dùng báo cáo để đưa vào Từ điển (Translation Memory).</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2 text-yellow-600 dark:text-yellow-500">
            <AlertCircle size={24} />
            <CardTitle>Các bản dịch bị cảnh báo (Cắm cờ)</CardTitle>
          </div>
          <CardDescription>
            Đây là những bản dịch bị người dùng báo lỗi sai. Hãy sửa chúng, và AI sẽ học từ bản sửa này để không mắc lại trong tương lai.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-1/3">Văn bản gốc</TableHead>
                <TableHead className="w-1/3">Bản dịch (AI)</TableHead>
                <TableHead>Thao tác</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} className="h-24 text-center text-text-muted">
                    Tuyệt vời! Không có bản dịch nào bị báo lỗi.
                  </TableCell>
                </TableRow>
              ) : (
                logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="align-top">
                      <p className="text-sm font-medium">{log.source_text}</p>
                      <p className="text-xs text-text-muted mt-1">App/Client: {log.client_id}</p>
                    </TableCell>
                    
                    <TableCell className="align-top">
                      {editingId === log.id ? (
                        <div className="space-y-2">
                          <textarea
                            className="w-full min-h-[100px] p-3 bg-surface border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            value={correctedText}
                            onChange={(e) => setCorrectedText(e.target.value)}
                            placeholder="Nhập bản dịch chuẩn vào đây..."
                          />
                        </div>
                      ) : (
                        <p className="text-sm text-red-500 line-through decoration-red-500/50">{log.translated_text}</p>
                      )}
                    </TableCell>
                    
                    <TableCell className="align-top">
                      {editingId === log.id ? (
                        <div className="flex items-center gap-2">
                          <Button size="sm" onClick={() => handleResolve(log.id)} isLoading={loading}>
                            <Check size={16} className="mr-1" /> Lưu bộ nhớ
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>
                            Hủy
                          </Button>
                        </div>
                      ) : (
                        <Button size="sm" variant="secondary" onClick={() => {
                          setEditingId(log.id);
                          setCorrectedText(log.translated_text);
                        }}>
                          <Edit2 size={16} className="mr-1" /> Sửa lỗi
                        </Button>
                      )}
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

export default QA;
