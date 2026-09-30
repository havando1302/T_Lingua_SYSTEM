import { useState, useRef } from 'react';
import api, { apiErrorMessage } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, } from '../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Plus, Trash2, Book, Download, Upload } from 'lucide-react';
import { useAuthUser } from '../lib/auth';
import { usePaginatedList } from '../lib/usePaginatedList';
import { ListSearch, ListStatus, ListPagination } from '../components/ListControls';

interface DictionaryEntry { source_text: string; translated_text: string; source_lang?: string; target_lang?: string; }
const entryKey = (item: DictionaryEntry) => JSON.stringify([item.source_text, item.source_lang, item.target_lang]);

const Dictionary = () => {
  const canWrite = useAuthUser()?.role === 'superadmin';
  const list = usePaginatedList<DictionaryEntry>('/dictionary');
  const items = list.items;
  const [sourceLang, setSourceLang] = useState('vi');
  const [targetLang, setTargetLang] = useState('en');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [deleting, setDeleting] = useState<string | null>(null);
  const [source, setSource] = useState('');
  const [target, setTarget] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canWrite || loading || uploading) return;
    setError(''); setNotice('');
    if (!source.trim() || !target.trim()) { setError('Vui lòng nhập văn bản gốc và bản dịch; không chỉ nhập khoảng trắng.'); return; }
    if (sourceLang === targetLang) { setError('Chọn hai ngôn ngữ khác nhau.'); return; }
    setLoading(true);
    try {
      await api.post('/dictionary', { source_text: source.trim(), translated_text: target.trim(), source_lang: sourceLang, target_lang: targetLang });
      setSource('');
      setTarget('');
      setNotice('Đã lưu cặp dịch vào từ điển.');
      await list.firstPage();
    } catch (err) {
      setError(apiErrorMessage(err, 'Lỗi khi thêm từ'));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (item: DictionaryEntry) => {
    if (!canWrite || deleting !== null) return;
    if (!confirm('Bạn có chắc muốn xóa cặp dịch này khỏi Từ điển?')) return;
    setDeleting(entryKey(item));
    setError(''); setNotice('');
    try {
      await api.post('/dictionary/delete', { source_text: item.source_text, source_lang: item.source_lang, target_lang: item.target_lang });
      setNotice('Đã xóa cặp dịch.');
      await list.refresh();
    } catch (err) {
      setError(apiErrorMessage(err, 'Lỗi khi xóa từ'));
    } finally { setDeleting(null); }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!canWrite) return;
    const file = e.target.files?.[0];
    if (!file) return;
    setError(''); setNotice('');
    if (!/\.(csv|xlsx)$/i.test(file.name) || file.size > 1_000_000 || file.size === 0 || sourceLang === targetLang) {
      setError('Chọn file CSV UTF-8 hoặc XLSX có dữ liệu, tối đa 1 MB và hai ngôn ngữ khác nhau.');
      e.target.value = '';
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_lang', sourceLang);
    formData.append('target_lang', targetLang);

    try {
      const res = await api.post('/dictionary/upload', formData);
      setNotice(`Đã nhập ${res.data.added} cặp dịch vào từ điển.`);
      await list.firstPage();
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Lỗi khi tải file lên'));
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleExport = async () => {
    setError(''); setNotice('');
    try {
      const response = await api.get('/dictionary/export', { responseType: 'blob' });
      const url = URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url; link.download = 'translation-dictionary.csv'; link.click();
      URL.revokeObjectURL(url);
      setNotice('Đã xuất từ điển CSV.');
    } catch (err) {
      setError(apiErrorMessage(err, 'Không thể xuất từ điển.'));
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Từ điển (Glossary)</h1>
      </div>

      {error && <p role="alert" className="text-red-600">{error}</p>}
      {notice && <p role="status" className="text-emerald-600">{notice}</p>}
      {canWrite && <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <div className="flex items-center gap-2 text-primary">
                <Book size={24} />
                <CardTitle>Thêm từ vựng mới</CardTitle>
              </div>
            </div>
            
            <div>
              <input 
                type="file" 
                accept=".csv,.xlsx"
                aria-label="Chọn file từ điển CSV hoặc XLSX"
                className="hidden" 
                ref={fileInputRef} 
                onChange={handleFileUpload} 
              />
              <Button 
                variant="secondary" 
                onClick={() => fileInputRef.current?.click()}
                isLoading={uploading}
                disabled={loading}
              >
                <Upload size={18} className="mr-2" />
                Tải lên CSV / XLSX
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="mb-4 flex flex-wrap gap-4">
            <label className="text-sm">Ngôn ngữ nguồn
              <select className="ml-2 rounded border border-border bg-surface p-2" value={sourceLang} disabled={loading || uploading} onChange={(event) => setSourceLang(event.target.value)}>
                <option value="vi">Tiếng Việt</option><option value="en">Tiếng Anh</option>
              </select>
            </label>
            <label className="text-sm">Ngôn ngữ đích
              <select className="ml-2 rounded border border-border bg-surface p-2" value={targetLang} disabled={loading || uploading} onChange={(event) => setTargetLang(event.target.value)}>
                <option value="en">Tiếng Anh</option><option value="vi">Tiếng Việt</option>
              </select>
            </label>
          </div>
          <form onSubmit={handleAdd} className="flex flex-col sm:flex-row gap-4 items-end">
            <div className="flex-1 w-full">
              <Input
                label="Văn bản gốc (Source)"
                placeholder="VD: Cảm ơn bạn rất nhiều"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                maxLength={5000}
                required
              />
            </div>
            <div className="flex-1 w-full">
              <Input
                label="Bản dịch chuẩn (Target)"
                placeholder="VD: Thank you very much"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                maxLength={5000}
                required
              />
            </div>
            <Button type="submit" isLoading={loading} disabled={uploading} className="w-full sm:w-auto">
              <Plus size={18} className="mr-2" />
              Thêm vào bộ nhớ
            </Button>
          </form>
        </CardContent>
      </Card>}

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle>Thư viện Từ vựng & Câu mẫu</CardTitle>
            <Button variant="secondary" onClick={handleExport}><Download size={16} className="mr-2" />Xuất CSV</Button>
          </div>
          <ListSearch list={list} />
        </CardHeader>
        <CardContent>
          <ListStatus list={list} />
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
                    {list.fetching ? 'Đang tải…' : list.error ? 'Chưa tải được từ điển.' : 'Không tìm thấy cặp dịch.'}
                  </TableCell>
                </TableRow>
              ) : (
                items.map((item) => (
                  <TableRow key={entryKey(item)}>
                    <TableCell className="font-medium whitespace-pre-wrap break-words">{item.source_text}<p className="text-xs text-text-muted">{item.source_lang || "Chưa xác định"} → {item.target_lang || "Chưa xác định"}</p></TableCell>
                    <TableCell className="whitespace-pre-wrap break-words">{item.translated_text}</TableCell>
                    <TableCell className="text-right">
                      {canWrite && <Button variant="danger" size="sm" onClick={() => handleDelete(item)} disabled={deleting !== null} isLoading={deleting === entryKey(item)} aria-label={`Xóa cặp dịch ${item.source_text}`}>
                        <Trash2 size={16} />
                      </Button>}
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

export default Dictionary;
