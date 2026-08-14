import { useEffect, useState, useRef } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Plus, Trash2, Book, Upload } from 'lucide-react';

const Dictionary = () => {
  const [items, setItems] = useState<any[]>([]);
  const [source, setSource] = useState('');
  const [target, setTarget] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDictionary = async () => {
    try {
      const res = await api.get('/dictionary');
      setItems(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchDictionary();
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!source.trim() || !target.trim()) return;
    setLoading(true);
    try {
      await api.post('/dictionary', { source_text: source, translated_text: target });
      setSource('');
      setTarget('');
      fetchDictionary();
    } catch (err) {
      console.error(err);
      alert('Lỗi khi thêm từ');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (sourceText: string) => {
    if (!confirm('Bạn có chắc muốn xóa cặp dịch này khỏi Từ điển?')) return;
    try {
      await api.delete(`/dictionary/${encodeURIComponent(sourceText)}`);
      fetchDictionary();
    } catch (err) {
      console.error(err);
      alert('Lỗi khi xóa từ');
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('/dictionary/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      alert(`Đã thêm thành công ${res.data.added} mục từ vựng mới!`);
      fetchDictionary();
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || 'Lỗi khi tải file lên');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Từ điển (Glossary)</h1>
        <p className="text-text-muted mt-2">Quản lý thư viện từ vựng chuẩn do nhân viên cung cấp. AI sẽ ưu tiên dịch đúng theo các cặp từ này.</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <div className="flex items-center gap-2 text-primary">
                <Book size={24} />
                <CardTitle>Thêm từ vựng mới</CardTitle>
              </div>
              <CardDescription className="mt-1">
                Nhập chính xác câu/từ nguồn và bản dịch đích để AI học theo. Hoặc tải lên file CSV.
              </CardDescription>
            </div>
            
            <div>
              <input 
                type="file" 
                accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel" 
                className="hidden" 
                ref={fileInputRef} 
                onChange={handleFileUpload} 
              />
              <Button 
                variant="secondary" 
                onClick={() => fileInputRef.current?.click()}
                isLoading={uploading}
              >
                <Upload size={18} className="mr-2" />
                Tải lên CSV / Excel
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAdd} className="flex flex-col sm:flex-row gap-4 items-end">
            <div className="flex-1 w-full">
              <Input
                label="Văn bản gốc (Source)"
                placeholder="VD: Cảm ơn bạn rất nhiều"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                required
              />
            </div>
            <div className="flex-1 w-full">
              <Input
                label="Bản dịch chuẩn (Target)"
                placeholder="VD: Thank you very much"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                required
              />
            </div>
            <Button type="submit" isLoading={loading} className="w-full sm:w-auto">
              <Plus size={18} className="mr-2" />
              Thêm vào bộ nhớ
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Thư viện Từ vựng & Câu mẫu</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-1/2">Nguồn</TableHead>
                <TableHead className="w-1/2">Đích</TableHead>
                <TableHead className="text-right">Thao tác</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} className="h-24 text-center text-text-muted">
                    Chưa có dữ liệu từ điển nào.
                  </TableCell>
                </TableRow>
              ) : (
                items.map((item, i) => (
                  <TableRow key={i}>
                    <TableCell className="font-medium">{item.source_text}</TableCell>
                    <TableCell>{item.translated_text}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="danger" size="sm" onClick={() => handleDelete(item.source_text)}>
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

export default Dictionary;
