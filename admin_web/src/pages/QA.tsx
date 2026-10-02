import { useEffect, useRef, useState } from 'react';
import api, { apiErrorMessage } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Button } from '../components/ui/Button';
import { AlertCircle, Check, Database, Download, Edit2, Mic2, ShieldCheck, Sparkles, Upload, Volume2 } from 'lucide-react';

import { usePaginatedList } from '../lib/usePaginatedList';
import { ListSearch, ListStatus, ListPagination } from '../components/ListControls';
import { useAuthUser } from '../lib/auth';

type FilterStatus = 'all' | 'pending' | 'reviewed';
type ReviewStatus = 'pending' | 'correct' | 'corrected' | 'unusable';
type DatasetSplit = 'auto' | 'train' | 'validation' | 'test';
interface QualityLog {
  id: number; source_text: string; translated_text: string; client_id?: string;
  source_lang?: string; target_lang?: string; is_flagged: boolean; is_reviewed: boolean; model_source?: string;
  input_mode?: 'voice' | 'text' | 'unknown'; stt_raw?: string; stt_corrected?: string | null;
  translation_raw?: string; stt_status?: string; translation_status?: string;
  has_audio?: boolean; audio_duration_ms?: number | null;
  consent_for_training?: boolean; pii_status?: 'pending' | 'clean' | 'redacted' | 'rejected';
  use_for_whisper?: boolean; use_for_nllb?: boolean; domain?: string | null;
  whisper_split?: Exclude<DatasetSplit, 'auto'> | null; nllb_split?: Exclude<DatasetSplit, 'auto'> | null;
}

interface TrainingOverview {
  qa?: { reviewed: number; pending: number; eligible_nllb: number; eligible_whisper: number; blocked_consent: number; blocked_pii: number };
  nllb: { samples: number; ready: boolean };
  whisper: { samples: number; ready: boolean };
}

const QA = () => {
  const user = useAuthUser();
  const [filter, setFilter] = useState<FilterStatus>('all');
  const list = usePaginatedList<QualityLog>('/quality/logs', `qa_only=true&review_status=${filter}`);
  const logs = list.items;
  const [editingId, setEditingId] = useState<number | null>(null);
  const [correctedSource, setCorrectedSource] = useState('');
  const [correctedText, setCorrectedText] = useState('');
  const [originalSnapshot, setOriginalSnapshot] = useState('');
  const [excludeWhisper, setExcludeWhisper] = useState(false);
  const [excludeNllb, setExcludeNllb] = useState(false);
  const [consentForTraining, setConsentForTraining] = useState(false);
  const [piiStatus, setPiiStatus] = useState<'pending' | 'clean' | 'redacted' | 'rejected'>('pending');
  const [includeNllb, setIncludeNllb] = useState(true);
  const [includeWhisper, setIncludeWhisper] = useState(false);
  const [nllbSplit, setNllbSplit] = useState<DatasetSplit>('auto');
  const [whisperSplit, setWhisperSplit] = useState<DatasetSplit>('auto');
  const [domain, setDomain] = useState('');
  const [overview, setOverview] = useState<TrainingOverview | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadingId, setUploadingId] = useState<number | null>(null);
  const [downloadingName, setDownloadingName] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const mutationRef = useRef(false);
  const fetching = list.fetching;
  const currentSnapshot = JSON.stringify({ correctedSource, correctedText, excludeWhisper, excludeNllb, consentForTraining, piiStatus, includeNllb, includeWhisper, nllbSplit, whisperSplit, domain });
  const dirty = editingId !== null && currentSnapshot !== originalSnapshot;

  const loadOverview = async () => {
    try { setOverview((await api.get<TrainingOverview>('/quality/overview')).data); }
    catch { setOverview(null); }
  };

  useEffect(() => { void loadOverview(); }, []);

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
      consentForTraining: Boolean(log.consent_for_training),
      piiStatus: log.pii_status || 'pending',
      includeNllb: log.use_for_nllb ?? log.translation_status !== 'unusable',
      includeWhisper: log.use_for_whisper ?? Boolean(log.has_audio && log.stt_status !== 'unusable'),
      nllbSplit: (log.nllb_split || 'auto') as DatasetSplit,
      whisperSplit: (log.whisper_split || 'auto') as DatasetSplit,
      domain: log.domain || '',
    };
    setCorrectedSource(next.correctedSource); setCorrectedText(next.correctedText);
    setExcludeWhisper(next.excludeWhisper); setExcludeNllb(next.excludeNllb);
    setConsentForTraining(next.consentForTraining); setPiiStatus(next.piiStatus);
    setIncludeNllb(next.includeNllb); setIncludeWhisper(next.includeWhisper); setDomain(next.domain);
    setNllbSplit(next.nllbSplit); setWhisperSplit(next.whisperSplit);
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
    const savedLog = { ...log, stt_corrected: source, translated_text: target, stt_status: sttStatus, translation_status: translationStatus, is_reviewed: true, is_flagged: false, consent_for_training: consentForTraining, pii_status: piiStatus, use_for_nllb: includeNllb && !excludeNllb, use_for_whisper: includeWhisper && !excludeWhisper, nllb_split: nllbSplit === 'auto' ? null : nllbSplit, whisper_split: whisperSplit === 'auto' ? null : whisperSplit, domain };
    try {
      await api.post(`/quality/logs/${log.id}/resolve`, {
        corrected_source_text: source, corrected_text: target, stt_status: sttStatus,
        translation_status: translationStatus,
        consent_for_training: consentForTraining, pii_status: piiStatus,
        use_for_nllb: includeNllb && !excludeNllb,
        use_for_whisper: includeWhisper && !excludeWhisper,
        nllb_split: nllbSplit === 'auto' ? null : nllbSplit,
        whisper_split: whisperSplit === 'auto' ? null : whisperSplit,
        domain: domain.trim() || null,
      });
      saved = true; list.setItems(previous => previous.map(item => item.id === log.id ? savedLog : item));
      setEditingId(null);
      setNotice('Đã lưu QA. Mẫu đủ điều kiện sẽ có trong lần tạo snapshot dataset tiếp theo.');
    } catch (err) {
      setError(apiErrorMessage(err, 'Chưa lưu được QA.'));
    } finally { if (saved) { await list.refresh(); await loadOverview(); } setLoading(false); mutationRef.current = false; }
  };

  const handleAudioUpload = async (log: QualityLog, file?: File) => {
    if (!file) return;
    setUploadingId(log.id); setError(''); setNotice('');
    const form = new FormData(); form.append('file', file);
    try { await api.post(`/quality/logs/${log.id}/audio`, form); setNotice('Đã gắn audio nguồn cho mẫu Whisper. Hãy mở QA và xác nhận quyền sử dụng.'); await list.refresh(); await loadOverview(); }
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
      setDownloadingName(name);
      setError('');
      setNotice('');
      const response = await api.get(path, { responseType: 'blob' });
      const url = URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url;
      link.download = name;
      link.click();
      URL.revokeObjectURL(url);
      setNotice(`Xuất thành công: ${name}`);
    } catch (err) {
      setError(apiErrorMessage(err, 'Không thể xuất dữ liệu.'));
    } finally {
      setDownloadingName(null);
    }
  };

  const isLogReviewed = (log: QualityLog) => Boolean(log.is_reviewed || (!log.is_flagged && log.model_source === 'user_flagged'));

  return <div className="space-y-6">
    <div><h1 className="text-3xl font-bold tracking-tight">QA dữ liệu huấn luyện</h1>
      <p className="text-text-muted mt-2">Duyệt nội dung, quyền sử dụng và PII. Dataset chỉ lấy snapshot từ những mẫu đã đủ điều kiện.</p></div>
    {error && <p role="alert" className="rounded-lg bg-red-500/10 p-3 text-red-600">{error}</p>}
    {notice && <p role="status" className="rounded-lg bg-emerald-500/10 p-3 text-emerald-600">{notice}</p>}
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <ReadinessCard icon={AlertCircle} label="Chờ QA" value={overview?.qa?.pending ?? 0} tone="amber" />
      <ReadinessCard icon={Database} label="Sẵn sàng NLLB" value={overview?.qa?.eligible_nllb ?? overview?.nllb.samples ?? 0} tone="blue" />
      <ReadinessCard icon={Mic2} label="Sẵn sàng Whisper" value={overview?.qa?.eligible_whisper ?? overview?.whisper.samples ?? 0} tone="violet" />
      <ReadinessCard icon={ShieldCheck} label="Bị chặn quyền/PII" value={Math.max(overview?.qa?.blocked_consent ?? 0, overview?.qa?.blocked_pii ?? 0)} tone="red" />
    </div>
    <Card><CardHeader>
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex items-center gap-2 text-primary"><Sparkles size={22}/><CardTitle>Whisper → NLLB → Dataset</CardTitle></div>
        {user?.role !== 'employee' && <div className="flex flex-wrap gap-2">
          <Button variant="secondary" disabled={downloadingName !== null} onClick={() => download('/quality/reviews/export', 'quality-reviews.csv')}>
            <Download size={15} className={`mr-1 ${downloadingName === 'quality-reviews.csv' ? 'animate-spin' : ''}`}/>
            {downloadingName === 'quality-reviews.csv' ? 'Đang xuất QA...' : 'Xuất QA'}
          </Button>
          <Button variant="secondary" disabled={downloadingName !== null} onClick={() => download('/training/export/nllb', 'nllb-training.jsonl')}>
            <Download size={15} className={`mr-1 ${downloadingName === 'nllb-training.jsonl' ? 'animate-spin' : ''}`}/>
            {downloadingName === 'nllb-training.jsonl' ? 'Đang xuất NLLB...' : 'Dataset NLLB'}
          </Button>
          <Button variant="secondary" disabled={downloadingName !== null} onClick={() => download('/training/export/whisper', 'whisper-training.zip')}>
            <Download size={15} className={`mr-1 ${downloadingName === 'whisper-training.zip' ? 'animate-spin' : ''}`}/>
            {downloadingName === 'whisper-training.zip' ? 'Đang nén Whisper...' : 'Dataset Whisper'}
          </Button>
        </div>}
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
      {editingId !== null && <p className="mb-3 rounded-lg border border-primary/20 bg-primary/5 p-3 text-sm text-text-muted">Hoàn tất nội dung, quyền sử dụng và kiểm tra PII. Split được gán ổn định tự động khi lưu.</p>}
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
            <TableCell className="min-w-64 align-top">{isEditing ? <div className="space-y-3 rounded-lg border border-border bg-background/50 p-3 text-xs">
              <label className="flex items-start gap-2"><input className="mt-0.5" type="checkbox" checked={consentForTraining} onChange={e => setConsentForTraining(e.target.checked)}/><span><b>Có quyền huấn luyện</b><br/><span className="text-text-muted">Đã có đồng ý hoặc quyền sử dụng hợp lệ.</span></span></label>
              <label className="block space-y-1"><span className="font-medium">Kiểm tra PII</span><select value={piiStatus} onChange={e => setPiiStatus(e.target.value as typeof piiStatus)} className="field"><option value="pending">Chưa kiểm tra</option><option value="clean">Không có PII</option><option value="redacted">Đã che PII</option><option value="rejected">Loại do PII</option></select></label>
              <label className="block space-y-1"><span className="font-medium">Nhóm dữ liệu</span><input value={domain} onChange={e => setDomain(e.target.value.replace(/[^A-Za-z0-9_-]/g, ''))} placeholder="general" maxLength={64} className="field"/></label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={includeNllb && !excludeNllb} disabled={excludeNllb} onChange={e => setIncludeNllb(e.target.checked)}/>Đưa vào nguồn NLLB</label>
              {includeNllb && !excludeNllb && <label className="block space-y-1"><span className="font-medium">Tập dữ liệu NLLB</span><select value={nllbSplit} onChange={e => setNllbSplit(e.target.value as DatasetSplit)} className="field"><option value="auto">Tự động</option><option value="train">Train</option><option value="validation">Validation</option><option value="test">Test</option></select></label>}
              {(log.has_audio || log.input_mode === 'voice') && <label className="flex items-center gap-2"><input type="checkbox" checked={includeWhisper && !excludeWhisper} disabled={!log.has_audio || excludeWhisper} onChange={e => setIncludeWhisper(e.target.checked)}/>Đưa vào nguồn Whisper</label>}
              {includeWhisper && log.has_audio && !excludeWhisper && <label className="block space-y-1"><span className="font-medium">Tập dữ liệu Whisper</span><select value={whisperSplit} onChange={e => setWhisperSplit(e.target.value as DatasetSplit)} className="field"><option value="auto">Tự động</option><option value="train">Train</option><option value="validation">Validation</option><option value="test">Test</option></select></label>}
            </div> : <EligibilityStatus log={log} reviewed={reviewed}/>}</TableCell>
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

function ReadinessCard({ icon: Icon, label, value, tone }: { icon: typeof ShieldCheck; label: string; value: number; tone: 'amber' | 'blue' | 'violet' | 'red' }) {
  const colors = {
    amber: 'bg-amber-500/10 text-amber-700 dark:text-amber-300',
    blue: 'bg-blue-500/10 text-blue-700 dark:text-blue-300',
    violet: 'bg-violet-500/10 text-violet-700 dark:text-violet-300',
    red: 'bg-red-500/10 text-red-700 dark:text-red-300',
  };
  return <div className="flex items-center gap-3 rounded-xl border border-border bg-surface p-4 shadow-sm">
    <div className={`rounded-lg p-2 ${colors[tone]}`}><Icon size={18}/></div>
    <div><p className="text-xs text-text-muted">{label}</p><p className="text-2xl font-bold">{value.toLocaleString('vi-VN')}</p></div>
  </div>;
}

function EligibilityStatus({ log, reviewed }: { log: QualityLog; reviewed: boolean }) {
  if (!reviewed) return <span className="text-xs font-semibold text-amber-600"><AlertCircle size={12} className="mr-1 inline"/>Chờ QA</span>;
  const cleared = log.consent_for_training && ['clean', 'redacted'].includes(log.pii_status || 'pending');
  return <div className="space-y-2 text-xs">
    <div className={cleared ? 'font-semibold text-emerald-600' : 'font-semibold text-red-600'}>
      {cleared ? <><ShieldCheck size={12} className="mr-1 inline"/>Đủ quyền và PII</> : <><AlertCircle size={12} className="mr-1 inline"/>Chưa đủ quyền hoặc PII</>}
    </div>
    <div className="flex flex-wrap gap-1.5">
      {cleared && log.use_for_nllb && <span className="rounded-full bg-blue-500/10 px-2 py-1 font-medium text-blue-700 dark:text-blue-300">NLLB</span>}
      {cleared && log.use_for_nllb && log.nllb_split && <span className="rounded-full bg-surface-muted px-2 py-1 text-text-muted">{log.nllb_split}</span>}
      {cleared && log.use_for_whisper && log.has_audio && <span className="rounded-full bg-violet-500/10 px-2 py-1 font-medium text-violet-700 dark:text-violet-300">Whisper</span>}
      {!log.use_for_nllb && !log.use_for_whisper && <span className="text-text-muted">Không đưa vào train</span>}
    </div>
  </div>;
}

export default QA;
