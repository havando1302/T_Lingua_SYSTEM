import { useEffect, useRef, useState } from 'react';
import api, { apiErrorMessage } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Button } from '../components/ui/Button';
import { AlertCircle, Check, Download, Edit2, Sparkles, Upload, Volume2 } from 'lucide-react';

import { usePaginatedList } from '../lib/usePaginatedList';
import { ListSearch, ListStatus, ListPagination } from '../components/ListControls';

type FilterStatus = 'all' | 'pending' | 'reviewed';
type ReviewStatus = 'pending' | 'correct' | 'corrected' | 'unusable';
interface QualityLog {
  id: number; source_text: string; translated_text: string; client_id?: string;
  source_lang?: string; target_lang?: string; is_flagged: boolean; is_reviewed: boolean; model_source?: string;
  input_mode?: 'voice' | 'text' | 'unknown'; stt_raw?: string; stt_corrected?: string | null;
  translation_raw?: string; stt_status?: string; translation_status?: string;
  has_audio?: boolean; audio_duration_ms?: number | null;
}

const QA = () => {
  const [filter, setFilter] = useState<FilterStatus>('all');
  const list = usePaginatedList<QualityLog>('/quality/logs', `qa_only=true&review_status=${filter}`);
  const logs = list.items;
  const [editingId, setEditingId] = useState<number | null>(null);
  const [correctedSource, setCorrectedSource] = useState('');
  const [correctedText, setCorrectedText] = useState('');
  const [originalSnapshot, setOriginalSnapshot] = useState('');
  const [excludeWhisper, setExcludeWhisper] = useState(false);
  const [excludeNllb, setExcludeNllb] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadingId, setUploadingId] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const mutationRef = useRef(false);
  const fetching = list.fetching;
  const currentSnapshot = JSON.stringify({ correctedSource, correctedText, excludeWhisper, excludeNllb });
  const dirty = editingId !== null && currentSnapshot !== originalSnapshot;

  useEffect(() => {
    if (!dirty) return;
    const beforeUnload = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ''; };
    const beforeNavigation = (event: MouseEvent) => {
      if (event.target instanceof Element && event.target.closest('a[href]') && !window.confirm('Bản sửa chưa được lưu. Rời trang và bỏ bản nháp?')) {
        event.preventDefault(); event.stopPropagation();
      }
    };
    window.addEventListener('beforeunload', beforeUnload);
    document.addEventListener('click', beforeNavigation, true);
    return () => { window.removeEventListener('beforeunload', beforeUnload); document.removeEventListener('click', beforeNavigation, true); };
  }, [dirty]);

  const beginEditing = (log: QualityLog) => {
    const next = {
      correctedSource: log.stt_corrected || log.source_text,
      correctedText: log.translated_text,
      excludeWhisper: log.stt_status === 'unusable',
      excludeNllb: log.translation_status === 'unusable',
    };
    setCorrectedSource(next.correctedSource); setCorrectedText(next.correctedText);
    setExcludeWhisper(next.excludeWhisper); setExcludeNllb(next.excludeNllb);
    setOriginalSnapshot(JSON.stringify(next)); setEditingId(log.id); setError(''); setNotice('');
  };

  const handleResolve = async (log: QualityLog) => {
    if (mutationRef.current) return;
    const source = correctedSource.trim(); const target = correctedText.trim();
    if (!source || !target) { setError('Vui lòng nhập cả transcript nguồn và bản dịch đã xác nhận.'); return; }
    const rawSource = (log.stt_raw || log.source_text).trim();
    const rawTranslation = (log.translation_raw || log.translated_text).trim();
    const hasVoiceAudio = Boolean(log.has_audio || log.input_mode === 'voice');
    const sttStatus: ReviewStatus | 'not_applicable' = !hasVoiceAudio ? 'not_applicable' : excludeWhisper ? 'unusable' : source === rawSource ? 'correct' : 'corrected';
    const translationStatus: ReviewStatus = excludeNllb ? 'unusable' : target === rawTranslation ? 'correct' : 'corrected';
    mutationRef.current = true; setLoading(true); setError(''); setNotice('');
    let saved = false;
    const savedLog = { ...log, stt_corrected: source, translated_text: target, stt_status: sttStatus, translation_status: translationStatus, is_reviewed: true, is_flagged: false };
    try {
      await api.post(`/quality/logs/${log.id}/resolve`, {
        corrected_source_text: source, corrected_text: target, stt_status: sttStatus,
        translation_status: translationStatus,
      });
      saved = true; list.setItems(previous => previous.map(item => item.id === log.id ? savedLog : item));
      setEditingId(null);
      setNotice('Đã lưu QA. Mẫu hợp lệ sẽ tự động được đưa vào dataset.');
    } catch (err) {
      setError(apiErrorMessage(err, 'Chưa lưu được QA.'));
    } finally { if (saved) await list.refresh(); setLoading(false); mutationRef.current = false; }
  };

  const handleAudioUpload = async (log: QualityLog, file?: File) => {
    if (!file) return;
    setUploadingId(log.id); setError(''); setNotice('');
    const form = new FormData(); form.append('file', file);
    try { await api.post(`/quality/logs/${log.id}/audio`, form); setNotice('Đã gắn audio nguồn cho mẫu Whisper.'); await list.refresh(); }
    catch (err) { setError(apiErrorMessage(err, 'Không thể tải audio nguồn.')); }
    finally { setUploadingId(null); }
  };

  const playAudio = async (log: QualityLog) => {
    try {
      const response = await api.get(`/quality/logs/${log.id}/audio`, { responseType: 'blob' });
      const url = URL.createObjectURL(response.data); const player = new Audio(url);
      player.addEventListener('ended', () => URL.revokeObjectURL(url), { once: true }); await player.play();
    } catch (err) { setError(apiErrorMessage(err, 'Không thể phát audio nguồn.')); }
  };

  const download = async (path: string, name: string) => {
    try {
      const response = await api.get(path, { responseType: 'blob' }); const url = URL.createObjectURL(response.data);
      const link = document.createElement('a'); link.href = url; link.download = name; link.click(); URL.revokeObjectURL(url);
    } catch (err) { setError(apiErrorMessage(err, 'Không thể xuất dữ liệu.')); }
  };

  const isLogReviewed = (log: QualityLog) => Boolean(log.is_reviewed || (!log.is_flagged && log.model_source === 'user_flagged'));

  return <div className="space-y-6">
    <div><h1 className="text-3xl font-bold tracking-tight">QA dữ liệu huấn luyện</h1>
      <p className="text-text-muted mt-2">Nghe, sửa transcript và bản dịch rồi lưu. Mẫu hợp lệ được tự động đưa vào dataset.</p></div>
    {error && <p role="alert" className="rounded-lg bg-red-500/10 p-3 text-red-600">{error}</p>}
    {notice && <p role="status" className="text-emerald-600">{notice}</p>}
    <Card><CardHeader>
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex items-center gap-2 text-primary"><Sparkles size={22}/><CardTitle>Whisper → NLLB → Dataset</CardTitle></div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={() => download('/quality/reviews/export', 'quality-reviews.csv')}><Download size={15} className="mr-1"/>Xuất QA</Button>
          <Button variant="secondary" onClick={() => download('/training/export/nllb', 'nllb-training.jsonl')}><Download size={15} className="mr-1"/>Dataset NLLB</Button>
          <Button variant="secondary" onClick={() => download('/training/export/whisper', 'whisper-training.zip')}><Download size={15} className="mr-1"/>Dataset Whisper</Button>
        </div>
        <fieldset disabled={editingId !== null || loading || fetching} className="w-full xl:w-80"><ListSearch list={list}/></fieldset>
      </div>
      <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-border/50">
        {(['all','pending','reviewed'] as FilterStatus[]).map(value => <button key={value} type="button" disabled={editingId !== null || loading || fetching}
          aria-pressed={filter === value} onClick={() => setFilter(value)}
          className={`px-3 py-1.5 rounded-md text-xs font-medium border ${filter === value ? 'bg-primary text-white' : 'bg-surface text-text-muted border-border'}`}>
          {value === 'all' ? 'Tất cả' : value === 'pending' ? 'Chưa chỉnh sửa' : 'Đã chỉnh sửa'}
        </button>)}
      </div>
    </CardHeader><CardContent>
      <ListStatus list={list}/>
      {editingId !== null && <p className="mb-3 text-sm text-text-muted">Sửa nội dung chưa đúng rồi bấm Lưu. Không cần chọn dataset thủ công.</p>}
      <Table><TableHeader><TableRow>
        <TableHead className="min-w-72">Audio và Whisper</TableHead><TableHead className="min-w-72">Bản dịch NLLB</TableHead>
        <TableHead>Trạng thái</TableHead><TableHead className="text-right">Thao tác</TableHead>
      </TableRow></TableHeader><TableBody>
        {fetching && logs.length === 0 ? <TableRow><TableCell colSpan={4} className="h-24 text-center text-text-muted">Đang tải QA...</TableCell></TableRow>
        : logs.length === 0 ? <TableRow><TableCell colSpan={4} className="h-24 text-center text-text-muted">Không có bản ghi phù hợp.</TableCell></TableRow>
        : logs.map(log => {
          const reviewed = isLogReviewed(log); const isEditing = editingId === log.id;
          return <TableRow key={log.id}>
            <TableCell className="align-top space-y-2">
              <div className="flex flex-wrap gap-2">
                {log.has_audio && <Button size="sm" variant="secondary" onClick={() => playAudio(log)}><Volume2 size={14} className="mr-1"/>Nghe {log.audio_duration_ms ? `${(log.audio_duration_ms/1000).toFixed(1)}s` : ''}</Button>}
                <label className="inline-flex cursor-pointer items-center rounded border border-border px-2 py-1 text-xs"><Upload size={13} className="mr-1"/>{uploadingId === log.id ? 'Đang tải...' : log.has_audio ? 'Thay audio' : 'Gắn audio'}
                  <input className="hidden" type="file" accept="audio/wav,.wav" disabled={uploadingId !== null} onChange={event => handleAudioUpload(log, event.target.files?.[0])}/>
                </label>
              </div>
              <p className="text-xs text-text-muted">Whisper thô · {log.input_mode || 'unknown'} · {log.source_lang || '?'} → {log.target_lang || '?'}</p>
              <p className="rounded bg-surface-muted p-2 text-sm">{log.stt_raw || log.source_text}</p>
              {isEditing ? <><label className="text-xs font-medium">Transcript đúng</label><textarea aria-label={`Transcript đã sửa cho bản ghi ${log.id}`} value={correctedSource} onChange={e => setCorrectedSource(e.target.value)} maxLength={5000} className="w-full min-h-24 rounded border border-border bg-surface p-2 text-sm"/>
                {(log.has_audio || log.input_mode === 'voice') && <label className="flex items-center gap-2 text-xs text-text-muted"><input type="checkbox" checked={excludeWhisper} onChange={e => setExcludeWhisper(e.target.checked)}/>Audio không dùng được</label>}</>
              : log.stt_corrected && <p className="text-sm font-medium text-emerald-600">Đã xác nhận: {log.stt_corrected}</p>}
            </TableCell>
            <TableCell className="align-top space-y-2">
              <p className="text-xs text-text-muted">NLLB thô</p><p className="rounded bg-surface-muted p-2 text-sm">{log.translation_raw || log.translated_text}</p>
              {isEditing ? <><label className="text-xs font-medium">Bản dịch đúng</label><textarea aria-label={`Bản dịch đã sửa cho bản ghi ${log.id}`} value={correctedText} onChange={e => setCorrectedText(e.target.value)} maxLength={5000} className="w-full min-h-24 rounded border border-border bg-surface p-2 text-sm"/>
                <label className="flex items-center gap-2 text-xs text-text-muted"><input type="checkbox" checked={excludeNllb} onChange={e => setExcludeNllb(e.target.checked)}/>Cặp dịch không dùng được</label></>
              : reviewed && <p className="text-sm font-medium text-emerald-600">Đã duyệt: {log.translated_text}</p>}
            </TableCell>
            <TableCell className="align-top">{reviewed ? <span className="text-xs font-semibold text-emerald-600"><Check size={12} className="inline mr-1"/>Đã QA</span> : <span className="text-xs font-semibold text-amber-600"><AlertCircle size={12} className="inline mr-1"/>Chờ QA</span>}</TableCell>
            <TableCell className="align-top text-right">{isEditing ? <div className="flex flex-col gap-2">
              <Button size="sm" onClick={() => handleResolve(log)} isLoading={loading}><Check size={14} className="mr-1"/>Lưu</Button>
              <Button size="sm" variant="ghost" onClick={() => { if (!dirty || window.confirm('Bỏ bản sửa chưa lưu?')) setEditingId(null); }}>Hủy</Button></div>
              : <Button size="sm" variant={reviewed ? 'secondary' : 'primary'} onClick={() => beginEditing(log)} disabled={editingId !== null}><Edit2 size={14} className="mr-1"/>{reviewed ? 'Chỉnh sửa' : 'Kiểm tra'}</Button>}</TableCell>
          </TableRow>;
        })}
      </TableBody></Table>
      <ListPagination list={list} disabled={editingId !== null || loading}/>
    </CardContent></Card>
  </div>;
};

export default QA;
