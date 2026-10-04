import { useState, useRef, useMemo } from 'react';
import { useTimedMessage } from '../lib/useTimedMessage';
import api, { apiErrorMessage } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Plus, Trash2, Book, Download, Upload, ArrowLeftRight, Filter } from 'lucide-react';
import { useAuthUser } from '../lib/auth';
import { usePaginatedList } from '../lib/usePaginatedList';
import { ListSearch, ListStatus, ListPagination } from '../components/ListControls';

interface DictionaryEntry {
  source_text: string;
  translated_text: string;
  source_lang?: string;
  target_lang?: string;
}

const entryKey = (item: DictionaryEntry) => JSON.stringify([item.source_text, item.source_lang, item.target_lang]);

const LANG_CONFIG: Record<string, { label: string; placeholder: string }> = {
  vi: {
    label: 'Tiếng Việt',
    placeholder: 'VD: Cảm ơn bạn rất nhiều (hoặc: Xin chào)',
  },
  en: {
    label: 'Tiếng Anh',
    placeholder: 'VD: Thank you very much (or: Hello)',
  },
};

const Dictionary = () => {
  const canWrite = useAuthUser()?.role === 'superadmin';

  // Filters for dictionary list
  const [filterSource, setFilterSource] = useState<string>('');
  const [filterTarget, setFilterTarget] = useState<string>('');

  const fixedParams = useMemo(() => {
    const params = new URLSearchParams();
    if (filterSource) params.set('source_lang', filterSource);
    if (filterTarget) params.set('target_lang', filterTarget);
    return params.toString();
  }, [filterSource, filterTarget]);

  const list = usePaginatedList<DictionaryEntry>('/dictionary', fixedParams);
  const items = list.items;

  // New entry form state
  const [sourceLang, setSourceLang] = useState('vi');
  const [targetLang, setTargetLang] = useState('en');
  const [error, setError] = useTimedMessage('');
  const [notice, setNotice] = useTimedMessage('');
  const [deleting, setDeleting] = useState<string | null>(null);
  const [source, setSource] = useState('');
  const [target, setTarget] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Dynamic placeholders and labels based on chosen languages
  const sourcePlaceholder = LANG_CONFIG[sourceLang]?.placeholder || `VD: Nhập văn bản (${sourceLang})...`;
  const targetPlaceholder = LANG_CONFIG[targetLang]?.placeholder || `VD: Nhập bản dịch (${targetLang})...`;
  const sourceLabel = LANG_CONFIG[sourceLang]?.label || sourceLang;
  const targetLabel = LANG_CONFIG[targetLang]?.label || targetLang;

  const handleSwapLangs = () => {
    setSourceLang(targetLang);
    setTargetLang(sourceLang);
    setSource(target);
    setTarget(source);
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canWrite || loading || uploading) return;
    setError('');
    setNotice('');
    if (!source.trim() || !target.trim()) {
      setError('Vui lòng nhập văn bản gốc và bản dịch; không chỉ nhập khoảng trắng.');
      return;
    }
    if (sourceLang === targetLang) {
      setError('Chọn hai ngôn ngữ khác nhau.');
      return;
    }
    setLoading(true);
    try {
      await api.post('/dictionary', {
        source_text: source.trim(),
        translated_text: target.trim(),
        source_lang: sourceLang,
        target_lang: targetLang,
      });
      setSource('');
      setTarget('');
      setNotice(`Đã lưu cặp dịch (${sourceLabel} → ${targetLabel}) vào từ điển.`);
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
    setError('');
    setNotice('');
    try {
      await api.post('/dictionary/delete', {
        source_text: item.source_text,
        source_lang: item.source_lang,
        target_lang: item.target_lang,
      });
      setNotice('Đã xóa cặp dịch.');
      await list.refresh();
    } catch (err) {
      setError(apiErrorMessage(err, 'Lỗi khi xóa từ'));
    } finally {
      setDeleting(null);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!canWrite) return;
    const file = e.target.files?.[0];
    if (!file) return;
    setError('');
    setNotice('');
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
    setError('');
    setNotice('');
    try {
      const exportPath = fixedParams ? `/dictionary/export?${fixedParams}` : '/dictionary/export';
      const response = await api.get(exportPath, { responseType: 'blob' });
      const url = URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url;
      const suffix = filterSource || filterTarget ? `-${filterSource || 'all'}-to-${filterTarget || 'all'}` : '';
      link.download = `translation-dictionary${suffix}.csv`;
      link.click();
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

      {canWrite && (
        <Card>
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
            {/* Language pair selectors with quick swap */}
            <div className="mb-4 flex flex-wrap items-center gap-3">
              <label className="text-sm font-medium flex items-center gap-2">
                <span className="text-text-muted">Ngôn ngữ nguồn:</span>
                <select
                  className="rounded-md border border-border bg-surface px-3 py-1.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/20"
                  value={sourceLang}
                  disabled={loading || uploading}
                  onChange={(event) => {
                    const newSrc = event.target.value;
                    setSourceLang(newSrc);
                    if (newSrc === targetLang) {
                      setTargetLang(newSrc === 'vi' ? 'en' : 'vi');
                    }
                  }}
                >
                  <option value="vi">Tiếng Việt</option>
                  <option value="en">Tiếng Anh</option>
                </select>
              </label>

              <button
                type="button"
                onClick={handleSwapLangs}
                disabled={loading || uploading}
                title="Đảo chiều ngôn ngữ nguồn và đích"
                className="p-1.5 rounded-md border border-border bg-surface hover:bg-surface-muted transition-colors text-text-muted hover:text-primary flex items-center gap-1 text-xs"
              >
                <ArrowLeftRight size={15} />
                <span className="hidden sm:inline">Đảo chiều</span>
              </button>

              <label className="text-sm font-medium flex items-center gap-2">
                <span className="text-text-muted">Ngôn ngữ đích:</span>
                <select
                  className="rounded-md border border-border bg-surface px-3 py-1.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/20"
                  value={targetLang}
                  disabled={loading || uploading}
                  onChange={(event) => {
                    const newTgt = event.target.value;
                    setTargetLang(newTgt);
                    if (newTgt === sourceLang) {
                      setSourceLang(newTgt === 'vi' ? 'en' : 'vi');
                    }
                  }}
                >
                  <option value="en">Tiếng Anh</option>
                  <option value="vi">Tiếng Việt</option>
                </select>
              </label>
            </div>

            {/* Inputs with dynamic labels & placeholders */}
            <form onSubmit={handleAdd} className="flex flex-col sm:flex-row gap-4 items-end">
              <div className="flex-1 w-full">
                <Input
                  label={`Văn bản gốc (${sourceLabel})`}
                  placeholder={sourcePlaceholder}
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  maxLength={5000}
                  required
                />
              </div>
              <div className="flex-1 w-full">
                <Input
                  label={`Bản dịch chuẩn (${targetLabel})`}
                  placeholder={targetPlaceholder}
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
        </Card>
      )}

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle>Thư viện Từ vựng & Câu mẫu</CardTitle>
            <Button variant="secondary" onClick={handleExport}>
              <Download size={16} className="mr-2" />
              Xuất CSV {filterSource || filterTarget ? '(Đã lọc)' : ''}
            </Button>
          </div>

          <ListSearch list={list} />

          {/* Quick Filter Bar by Source and Target Languages */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-border/50">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-text-muted font-medium flex items-center gap-1">
                <Filter size={13} />
                Lọc nhanh:
              </span>
              <button
                type="button"
                onClick={() => {
                  setFilterSource('');
                  setFilterTarget('');
                }}
                className={`px-3 py-1.5 rounded-md text-xs font-medium border transition-colors ${
                  !filterSource && !filterTarget
                    ? 'bg-primary text-white border-primary shadow-sm'
                    : 'bg-surface text-text-muted border-border hover:bg-surface-muted'
                }`}
              >
                Tất cả cặp từ
              </button>
              <button
                type="button"
                onClick={() => {
                  setFilterSource('vi');
                  setFilterTarget('en');
                }}
                className={`px-3 py-1.5 rounded-md text-xs font-medium border transition-colors ${
                  filterSource === 'vi' && filterTarget === 'en'
                    ? 'bg-primary text-white border-primary shadow-sm'
                    : 'bg-surface text-text-muted border-border hover:bg-surface-muted'
                }`}
              >
                🇻🇳 Tiếng Việt → 🇬🇧 Tiếng Anh
              </button>
              <button
                type="button"
                onClick={() => {
                  setFilterSource('en');
                  setFilterTarget('vi');
                }}
                className={`px-3 py-1.5 rounded-md text-xs font-medium border transition-colors ${
                  filterSource === 'en' && filterTarget === 'vi'
                    ? 'bg-primary text-white border-primary shadow-sm'
                    : 'bg-surface text-text-muted border-border hover:bg-surface-muted'
                }`}
              >
                🇬🇧 Tiếng Anh → 🇻🇳 Tiếng Việt
              </button>
            </div>

            <div className="flex items-center gap-2 text-xs">
              <label className="flex items-center gap-1.5 text-text-muted">
                <span>Nguồn:</span>
                <select
                  value={filterSource}
                  onChange={(e) => setFilterSource(e.target.value)}
                  className="rounded border border-border bg-surface px-2 py-1 text-xs text-text focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="">Tất cả nguồn</option>
                  <option value="vi">Tiếng Việt</option>
                  <option value="en">Tiếng Anh</option>
                </select>
              </label>
              <span className="text-text-muted">→</span>
              <label className="flex items-center gap-1.5 text-text-muted">
                <span>Đích:</span>
                <select
                  value={filterTarget}
                  onChange={(e) => setFilterTarget(e.target.value)}
                  className="rounded border border-border bg-surface px-2 py-1 text-xs text-text focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="">Tất cả đích</option>
                  <option value="en">Tiếng Anh</option>
                  <option value="vi">Tiếng Việt</option>
                </select>
              </label>
              {(filterSource || filterTarget) && (
                <button
                  type="button"
                  onClick={() => {
                    setFilterSource('');
                    setFilterTarget('');
                  }}
                  className="text-xs text-primary hover:underline ml-1 font-medium"
                >
                  Xóa lọc
                </button>
              )}
            </div>
          </div>
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
                    {list.fetching ? 'Đang tải…' : list.error ? 'Chưa tải được từ điển.' : 'Không tìm thấy cặp dịch phù hợp.'}
                  </TableCell>
                </TableRow>
              ) : (
                items.map((item) => (
                  <TableRow key={entryKey(item)}>
                    <TableCell className="font-medium whitespace-pre-wrap break-words">
                      {item.source_text}
                    </TableCell>
                    <TableCell className="whitespace-pre-wrap break-words">{item.translated_text}</TableCell>
                    <TableCell className="text-right">
                      {canWrite && (
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => handleDelete(item)}
                          disabled={deleting !== null}
                          isLoading={deleting === entryKey(item)}
                          aria-label={`Xóa cặp dịch ${item.source_text}`}
                        >
                          <Trash2 size={16} />
                        </Button>
                      )}
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
