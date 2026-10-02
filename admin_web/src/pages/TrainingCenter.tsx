import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity, AlertTriangle, BrainCircuit, CheckCircle2, Cloud, Cpu, Database,
  Download, FlaskConical, GitCompareArrows, Languages, Lock, Mic2, Play,
  RefreshCw, Rocket, ShieldCheck, Square, Terminal, Upload,
} from 'lucide-react';
import api, { apiErrorMessage } from '../lib/api';
import { useAuthUser } from '../lib/auth';
import { Button, cn } from '../components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';

type Tab = 'overview' | 'datasets' | 'training' | 'models' | 'playground';
type Task = 'nllb' | 'whisper';
type TrainingTask = Task | 'both';

interface Overview {
  runtime: { status: string; gpu: Record<string, unknown>; worker: string; active_job_id?: string; scope?: string };
  qa?: { reviewed: number; pending: number; eligible_nllb: number; eligible_whisper: number; blocked_consent: number; blocked_pii: number };
  whisper: { samples: number; hours: number; hours_by_language: Record<string, number>; splits: Record<string, number>; ready: boolean; recommended_hours: number };
  nllb: { samples: number; directions: Record<string, number>; splits: Record<string, number>; ready: boolean; recommended_pairs_per_direction: number };
  playground: { available: boolean; reason: string };
}

interface DatasetPreview {
  task: Task; reviewed: number; eligible: number; splits: Record<string, number>;
  directions: Record<string, number>; duration_seconds: number; ready: boolean;
  blockers: { no_consent: number; pii_not_cleared: number; not_approved: number; missing_audio: number };
  reasons: string[];
}

interface Dataset {
  id: string; name: string; task: Task; source_type: string; source_langs: string[];
  version: string; status: string; sample_count: number; duration_seconds: number;
  train_count: number; validation_count: number; test_count: number;
  sha256?: string; size_bytes: number; validation: { valid?: boolean; errors?: string[]; warnings?: string[]; speaker_count?: number; directions?: Record<string, number> };
  created_at: string; frozen_at?: string;
}

interface Job {
  id: string; group_id?: string; depends_on_job_id?: string; task: Task; dataset_id: string;
  base_model: string; output_version: string; method: string; config: Record<string, number | string>;
  worker_id?: string; status: string; progress_percent: number; current_epoch?: number;
  current_step?: number; total_steps?: number; train_loss?: number; validation_loss?: number;
  eta_seconds?: number; artifact_id?: string; error_code?: string; error_message?: string;
  created_at: string; started_at?: string; finished_at?: string;
}

interface JobEvent {
  id: number; level: string; event_type: string; message: string;
  metrics: Record<string, number>; created_at: string;
}

interface Artifact {
  id: string; component: Task; version: string; base_model: string; dataset_id: string;
  job_id: string; format: string; storage_uri: string; sha256: string; size_bytes: number; status: string;
  metrics: Record<string, unknown>; deployment_state: string; created_at: string;
  validated_at?: string; requires_runtime_reload: boolean;
}

const tabs: { key: Tab; label: string; icon: typeof Activity }[] = [
  { key: 'overview', label: 'Tổng quan', icon: Activity },
  { key: 'datasets', label: 'Datasets', icon: Database },
  { key: 'training', label: 'Huấn luyện', icon: FlaskConical },
  { key: 'models', label: 'Models & Deploy', icon: Rocket },
  { key: 'playground', label: 'A/B Playground', icon: GitCompareArrows },
];

const finalStates = new Set(['completed', 'failed', 'cancelled']);
const statusLabels: Record<string, string> = {
  draft: 'Bản nháp', validating: 'Đang kiểm tra', validated: 'Đã kiểm tra', invalid: 'Không hợp lệ', frozen: 'Đã đóng băng',
  queued: 'Đang chờ', preparing: 'Đang chuẩn bị', training: 'Đang huấn luyện', evaluating: 'Đang đánh giá',
  merging_lora: 'Đang gộp LoRA', converting: 'Đang đóng gói',
  completed: 'Hoàn thành', failed: 'Thất bại', cancelling: 'Đang dừng', cancelled: 'Đã hủy',
  candidate: 'Ứng viên', active: 'Đang dùng', previous: 'Bản trước', canary: 'Canary', idle: 'Rảnh', waiting: 'Đang chờ', busy: 'Đang chạy',
};

function Badge({ value }: { value: string }) {
  const good = ['frozen', 'validated', 'completed', 'active', 'online', 'idle'].includes(value);
  const bad = ['invalid', 'failed', 'cancelled'].includes(value);
  return <span className={cn('inline-flex rounded-full px-2.5 py-1 text-xs font-semibold',
    good ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' : bad ? 'bg-red-500/10 text-red-600 dark:text-red-400' : 'bg-amber-500/10 text-amber-700 dark:text-amber-400')}>{statusLabels[value] ?? value}</span>;
}

function Progress({ value, label }: { value: number; label?: string }) {
  const safe = Math.max(0, Math.min(100, value));
  return <div className="space-y-1.5">
    <div className="flex justify-between text-xs text-text-muted"><span>{label}</span><span>{Math.round(safe)}%</span></div>
    <div className="h-2 overflow-hidden rounded-full bg-border"><div className="h-full rounded-full bg-primary transition-all" style={{ width: `${safe}%` }} /></div>
  </div>;
}

function bytes(value: number) {
  if (!value) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  return `${(value / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}`;
}

function date(value?: string) {
  return value ? new Intl.DateTimeFormat('vi-VN', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value)) : '—';
}

function gpuLabel(gpu: Record<string, unknown>) {
  const name = gpu.name ?? gpu.device_name ?? gpu.gpu_name;
  const used = gpu.used_gb ?? gpu.allocated_gb ?? (typeof gpu.reserved_mb === 'number' ? (gpu.reserved_mb / 1024).toFixed(1) : undefined);
  const total = gpu.total_gb ?? (typeof gpu.total_mb === 'number' ? (gpu.total_mb / 1024).toFixed(1) : undefined);
  if (!name && !total) return 'Không phát hiện GPU';
  return `${String(name ?? 'GPU')}${total ? ` · ${String(used ?? '?')}/${String(total)} GB` : ''}`;
}

export default function TrainingCenter() {
  const user = useAuthUser();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>('overview');
  const [overview, setOverview] = useState<Overview | null>(null);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [events, setEvents] = useState<JobEvent[]>([]);
  const [selectedJobId, setSelectedJobId] = useState('');
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(async (quiet = false) => {
    if (!quiet) setBusy('refresh');
    try {
      const [overviewResponse, datasetsResponse, jobsResponse, artifactsResponse] = await Promise.all([
        api.get<Overview>('/training/overview'), api.get<Dataset[]>('/training/datasets'),
        api.get<Job[]>('/training/jobs'), api.get<Artifact[]>('/training/models'),
      ]);
      setOverview(overviewResponse.data); setDatasets(datasetsResponse.data);
      setJobs(jobsResponse.data); setArtifacts(artifactsResponse.data);
      setSelectedJobId((current) => current || jobsResponse.data[0]?.id || '');
      setError('');
    } catch (caught) {
      setError(apiErrorMessage(caught, 'Không tải được Training Center.'));
    } finally { if (!quiet) setBusy(''); }
  }, []);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    const active = jobs.some((job) => !finalStates.has(job.status));
    if (!active) return;
    const timer = window.setInterval(() => void load(true), 5000);
    return () => window.clearInterval(timer);
  }, [jobs, load]);
  useEffect(() => {
    if (!selectedJobId) { setEvents([]); return; }
    api.get<JobEvent[]>(`/training/jobs/${selectedJobId}/events`).then((response) => setEvents(response.data)).catch(() => setEvents([]));
  }, [selectedJobId, jobs]);

  const selectedJob = jobs.find((job) => job.id === selectedJobId);
  const act = async (key: string, action: () => Promise<unknown>, success: string) => {
    setBusy(key); setNotice(''); setError('');
    try { await action(); setNotice(success); await load(true); }
    catch (caught) { setError(apiErrorMessage(caught)); }
    finally { setBusy(''); }
  };
  const download = async (url: string, filename: string) => {
    setBusy(`download:${url}`);
    try {
      const response = await api.get(url, { responseType: 'blob' });
      const objectUrl = URL.createObjectURL(response.data);
      const anchor = document.createElement('a'); anchor.href = objectUrl; anchor.download = filename; anchor.click();
      URL.revokeObjectURL(objectUrl);
    } catch (caught) { setError(apiErrorMessage(caught, 'Không tải được tệp.')); }
    finally { setBusy(''); }
  };

  return <div className="mx-auto max-w-[1500px] space-y-6">
    <header className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
      <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-center">
        <div className="flex items-center gap-4">
          <div className="rounded-2xl bg-primary p-3 text-white"><BrainCircuit size={28} /></div>
          <div><h1 className="text-2xl font-bold md:text-3xl">Trung tâm huấn luyện AI</h1><p className="text-sm text-text-muted">Dataset · Training · Models · A/B Testing</p></div>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="flex items-center gap-2 rounded-lg border border-border px-3 py-2"><span className="h-2 w-2 rounded-full bg-emerald-500" />Runtime: {overview?.runtime.status ?? '...'}</span>
          <span className="rounded-lg border border-border px-3 py-2" title="Tài nguyên của máy đang chạy API; worker bên ngoài có thể khác"><Cpu className="mr-2 inline" size={15} />API host: {overview ? gpuLabel(overview.runtime.gpu) : 'Đang đọc GPU'}</span>
          <span className="rounded-lg border border-border px-3 py-2">Worker: {statusLabels[overview?.runtime.worker ?? ''] ?? '...'}</span>
          <Badge value={user?.role ?? 'admin'} />
          <Button variant="secondary" size="sm" onClick={() => load()} isLoading={busy === 'refresh'}><RefreshCw size={14} className="mr-1" />Làm mới</Button>
        </div>
      </div>
      <div role="tablist" aria-label="Các khu vực huấn luyện" className="mt-5 flex gap-1 overflow-x-auto border-t border-border pt-4">
        {tabs.map((item) => <button key={item.key} role="tab" aria-selected={tab === item.key} onClick={() => setTab(item.key)} className={cn('flex shrink-0 items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors', tab === item.key ? 'bg-primary text-white shadow-sm' : 'text-text-muted hover:bg-background hover:text-text')}><item.icon size={16} />{item.label}</button>)}
      </div>
    </header>

    {notice && <div role="status" className="flex items-center gap-3 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-emerald-700 dark:text-emerald-300"><CheckCircle2 size={18} />{notice}</div>}
    {error && <div role="alert" className="flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-red-700 dark:text-red-300"><AlertTriangle size={18} />{error}</div>}

    <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
      {['1. Duyệt QA', '2. Tạo dataset', '3. Validate & Freeze', '4. Chọn máy chạy', '5. Train & đánh giá'].map((step, index) =>
        <div key={step} className="rounded-xl border border-border bg-surface px-3 py-2 text-sm"><span className="mr-2 font-bold text-primary">{index + 1}</span>{step.replace(/^\d+\. /, '')}</div>)}
    </div>

    {tab === 'overview' && <OverviewTab overview={overview} navigateQA={() => navigate('/qa')} download={download} />}
    {tab === 'datasets' && <DatasetsTab datasets={datasets} busy={busy} act={act} download={download} />}
    {tab === 'training' && <TrainingTab datasets={datasets} jobs={jobs} events={events} selectedJob={selectedJob} selectedJobId={selectedJobId} setSelectedJobId={setSelectedJobId} isSuperadmin={user?.role === 'superadmin'} busy={busy} act={act} download={download} />}
    {tab === 'models' && <ModelsTab artifacts={artifacts} isSuperadmin={user?.role === 'superadmin'} busy={busy} act={act} setTab={setTab} />}
    {tab === 'playground' && <PlaygroundTab capability={overview?.playground} />}
  </div>;
}

function OverviewTab({ overview, navigateQA, download }: { overview: Overview | null; navigateQA: () => void; download: (url: string, name: string) => void }) {
  if (!overview) return <Card><CardContent className="p-8 text-text-muted">Đang tải thống kê dữ liệu…</CardContent></Card>;
  const whisperProgress = overview.whisper.recommended_hours ? overview.whisper.hours / overview.whisper.recommended_hours * 100 : 0;
  const viProgress = overview.nllb.directions['vi-en'] / overview.nllb.recommended_pairs_per_direction * 100;
  const enProgress = overview.nllb.directions['en-vi'] / overview.nllb.recommended_pairs_per_direction * 100;
  return <div className="space-y-6">
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><ShieldCheck size={20}/>Trạng thái nguồn dữ liệu</CardTitle><CardDescription>Chỉ mẫu đã QA, có quyền huấn luyện và PII sạch/đã che mới được tính.</CardDescription></CardHeader><CardContent>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <Metric label="Đã QA" value={(overview.qa?.reviewed ?? 0).toLocaleString('vi-VN')} />
        <Metric label="Chờ QA" value={(overview.qa?.pending ?? 0).toLocaleString('vi-VN')} />
        <Metric label="Đủ điều kiện NLLB" value={(overview.qa?.eligible_nllb ?? overview.nllb.samples).toLocaleString('vi-VN')} />
        <Metric label="Đủ điều kiện Whisper" value={(overview.qa?.eligible_whisper ?? overview.whisper.samples).toLocaleString('vi-VN')} />
        <Metric label="Bị chặn quyền/PII" value={Math.max(overview.qa?.blocked_consent ?? 0, overview.qa?.blocked_pii ?? 0).toLocaleString('vi-VN')} />
      </div>
      <div className="mt-4"><Button onClick={navigateQA}>Mở hàng đợi QA</Button></div>
    </CardContent></Card>
    <div className="grid gap-6 xl:grid-cols-2">
    <Card>
      <CardHeader><div className="flex items-center justify-between"><CardTitle className="flex items-center gap-2"><Mic2 size={20} />Whisper</CardTitle><Badge value={overview.whisper.ready ? 'validated' : 'draft'} /></div><CardDescription>Sẵn sàng kỹ thuật dựa trên train/validation; 10 giờ audio là mốc khuyến nghị.</CardDescription></CardHeader>
      <CardContent className="space-y-5">
        <Progress value={whisperProgress} label={`${overview.whisper.hours.toFixed(2)} / ${overview.whisper.recommended_hours} giờ audio`} />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Metric label="Mẫu hợp lệ" value={overview.whisper.samples.toLocaleString('vi-VN')} />
          <Metric label="Tiếng Việt" value={`${overview.whisper.hours_by_language.vi ?? 0} giờ`} />
          <Metric label="Tiếng Anh" value={`${overview.whisper.hours_by_language.en ?? 0} giờ`} />
        </div>
        <SplitLine splits={overview.whisper.splits} />
        <div className="flex flex-wrap gap-2"><Button variant="secondary" onClick={navigateQA}>Mở QA Whisper</Button><Button variant="secondary" onClick={() => download('/training/export/whisper', 'whisper-training.zip')}><Download size={15} className="mr-1" />Xuất Whisper ZIP</Button></div>
      </CardContent>
    </Card>
    <Card>
      <CardHeader><div className="flex items-center justify-between"><CardTitle className="flex items-center gap-2"><Languages size={20} />NLLB</CardTitle><Badge value={overview.nllb.ready ? 'validated' : 'draft'} /></div><CardDescription>Đếm riêng từng chiều dịch. Mốc số lượng là khuyến nghị, không phải khóa cứng.</CardDescription></CardHeader>
      <CardContent className="space-y-5">
        <Progress value={viProgress} label={`Việt → Anh: ${(overview.nllb.directions['vi-en'] ?? 0).toLocaleString('vi-VN')} / ${overview.nllb.recommended_pairs_per_direction.toLocaleString('vi-VN')}`} />
        <Progress value={enProgress} label={`Anh → Việt: ${(overview.nllb.directions['en-vi'] ?? 0).toLocaleString('vi-VN')} / ${overview.nllb.recommended_pairs_per_direction.toLocaleString('vi-VN')}`} />
        <div className="grid grid-cols-2 gap-3"><Metric label="Tổng cặp đã duyệt" value={overview.nllb.samples.toLocaleString('vi-VN')} /><Metric label="Điều kiện bắt buộc" value={overview.nllb.ready ? 'Đạt' : 'Chưa đạt'} /></div>
        <SplitLine splits={overview.nllb.splits} />
        <div className="flex flex-wrap gap-2"><Button variant="secondary" onClick={navigateQA}>Mở QA NLLB</Button><Button variant="secondary" onClick={() => download('/training/export/nllb', 'nllb-training.jsonl')}><Download size={15} className="mr-1" />Xuất NLLB JSONL</Button></div>
      </CardContent>
    </Card>
    </div>
  </div>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl border border-border bg-background/60 p-3"><div className="text-xs text-text-muted">{label}</div><div className="mt-1 font-semibold">{value}</div></div>;
}
function SplitLine({ splits }: { splits: Record<string, number> }) {
  return <div className="flex flex-wrap gap-4 rounded-xl border border-border p-3 text-sm"><span>Train: <b>{splits.train ?? 0}</b></span><span>Validation: <b>{splits.validation ?? 0}</b></span><span>Test: <b>{splits.test ?? 0}</b></span></div>;
}

function DatasetsTab({ datasets, busy, act, download }: { datasets: Dataset[]; busy: string; act: (key: string, action: () => Promise<unknown>, success: string) => Promise<void>; download: (url: string, name: string) => void }) {
  const [mode, setMode] = useState<'qa' | 'upload'>('qa');
  const [task, setTask] = useState<Task>('nllb');
  const [name, setName] = useState('');
  const [version, setVersion] = useState('v1.0');
  const [language, setLanguage] = useState('all');
  const [domain, setDomain] = useState('');
  const [createdFrom, setCreatedFrom] = useState('');
  const [createdTo, setCreatedTo] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [rights, setRights] = useState(false);
  const [preview, setPreview] = useState<(DatasetPreview & { signature: string }) | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const [previewError, setPreviewError] = useState('');
  const signature = JSON.stringify({ task, language, domain, createdFrom, createdTo });
  const qaPayload = { name: name || `${task}-preview`, version, task, language, domain: domain || null, created_from: createdFrom || null, created_to: createdTo || null };
  const runPreview = async () => {
    setPreviewing(true); setPreviewError('');
    try {
      const response = await api.post<DatasetPreview>('/training/datasets/preview-from-qa', qaPayload);
      setPreview({ ...response.data, signature });
    } catch (caught) { setPreviewError(apiErrorMessage(caught, 'Không xem trước được dữ liệu.')); }
    finally { setPreviewing(false); }
  };
  const create = async () => {
    if (mode === 'qa') return api.post('/training/datasets/from-qa', qaPayload);
    const form = new FormData(); form.append('name', name); form.append('version', version); form.append('task', task); form.append('rights_confirmed', String(rights)); if (file) form.append('file', file);
    return api.post('/training/datasets/upload', form, { timeout: 600_000 });
  };
  return <div className="space-y-6">
    <Card><CardHeader><CardTitle>Tạo phiên bản dataset</CardTitle><CardDescription>Dữ liệu upload không thể huấn luyện ngay: bắt buộc Validate rồi Freeze.</CardDescription></CardHeader><CardContent className="space-y-4">
      <div className="flex gap-2"><Button variant={mode === 'qa' ? 'primary' : 'secondary'} onClick={() => setMode('qa')}>Tạo từ QA</Button><Button variant={mode === 'upload' ? 'primary' : 'secondary'} onClick={() => setMode('upload')}><Upload size={15} className="mr-1" />Tải từ bên ngoài</Button></div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Field label="Tên dataset"><input value={name} onChange={(event) => setName(event.target.value)} placeholder="nllb-vi-en-v1.0" className="field" /></Field>
        <Field label="Phiên bản"><input value={version} onChange={(event) => setVersion(event.target.value)} className="field" /></Field>
        <Field label="Model"><select value={task} onChange={(event) => setTask(event.target.value as Task)} className="field"><option value="nllb">NLLB</option><option value="whisper">Whisper</option></select></Field>
        {mode === 'qa' ? <Field label="Ngôn ngữ nguồn"><select value={language} onChange={(event) => setLanguage(event.target.value)} className="field"><option value="all">Cả hai</option><option value="vi">Tiếng Việt</option><option value="en">Tiếng Anh</option></select></Field> : <Field label={task === 'nllb' ? 'JSONL hoặc CSV' : 'ZIP có manifest.jsonl'}><input type="file" accept={task === 'nllb' ? '.jsonl,.csv' : '.zip'} onChange={(event) => setFile(event.target.files?.[0] ?? null)} className="field" /></Field>}
      </div>
      {mode === 'qa' && <div className="grid gap-4 md:grid-cols-3"><Field label="Domain (để trống = tất cả)"><input value={domain} onChange={(event) => setDomain(event.target.value)} placeholder="general" className="field" /></Field><Field label="Từ ngày"><input type="date" value={createdFrom} onChange={(event) => setCreatedFrom(event.target.value)} className="field" /></Field><Field label="Đến ngày"><input type="date" value={createdTo} onChange={(event) => setCreatedTo(event.target.value)} className="field" /></Field></div>}
      {mode === 'upload' && <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={rights} onChange={(event) => setRights(event.target.checked)} className="mt-1" /><span>Tôi xác nhận có quyền sử dụng dữ liệu này để huấn luyện model.</span></label>}
      {mode === 'qa' && <div className="space-y-3 rounded-xl border border-border bg-background/50 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3"><div><div className="font-medium">Xem trước trước khi tạo</div><div className="text-xs text-text-muted">Dùng đúng bộ lọc và quy tắc sẽ áp dụng cho snapshot.</div></div><Button variant="secondary" isLoading={previewing} onClick={runPreview}><FlaskConical size={14} className="mr-1"/>Kiểm tra dữ liệu</Button></div>
        {previewError && <p className="text-sm text-red-600">{previewError}</p>}
        {preview && preview.signature === signature && <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 md:grid-cols-4"><Metric label="Đã QA" value={String(preview.reviewed)}/><Metric label="Đủ điều kiện" value={String(preview.eligible)}/><Metric label="Train / Val / Test" value={`${preview.splits.train}/${preview.splits.validation}/${preview.splits.test}`}/><Metric label={task === 'whisper' ? 'Thời lượng' : 'Số chiều dịch'} value={task === 'whisper' ? `${(preview.duration_seconds / 3600).toFixed(2)} giờ` : String(Object.keys(preview.directions).length)}/></div>
          {preview.ready ? <p className="flex items-center gap-2 text-sm font-medium text-emerald-600"><CheckCircle2 size={16}/>Đủ điều kiện kỹ thuật để tạo snapshot.</p> : <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-600"><div className="font-medium">Chưa thể tạo dataset train được</div><ul className="mt-1 list-disc pl-5">{preview.reasons.map(reason => <li key={reason}>{reason}</li>)}</ul><div className="mt-2 text-xs">Chặn bởi quyền: {preview.blockers.no_consent} · PII: {preview.blockers.pii_not_cleared} · Chưa duyệt: {preview.blockers.not_approved}{task === 'whisper' ? ` · Thiếu audio: ${preview.blockers.missing_audio}` : ''}</div></div>}
        </div>}
      </div>}
      <Button disabled={!name || (mode === 'qa' ? !preview?.ready || preview.signature !== signature : (!file || !rights))} isLoading={busy === 'dataset:create'} onClick={() => act('dataset:create', create, 'Đã tạo dataset bản nháp. Hãy chạy Validate trước khi Freeze.')}>Tạo dataset</Button>
    </CardContent></Card>
    <Card><CardHeader><CardTitle>Dataset Registry</CardTitle><CardDescription>Dataset đã Frozen là bất biến; muốn thay đổi phải tạo phiên bản mới.</CardDescription></CardHeader><CardContent>
      <Table><TableHeader><TableRow><TableHead>Phiên bản</TableHead><TableHead>Model</TableHead><TableHead>Train / Val / Test</TableHead><TableHead>Dung lượng</TableHead><TableHead>Trạng thái</TableHead><TableHead>Thao tác</TableHead></TableRow></TableHeader><TableBody>
        {datasets.map((dataset) => <TableRow key={dataset.id}><TableCell><div className="font-medium">{dataset.name}</div><div className="mt-1 text-xs text-text-muted">{dataset.version} · {dataset.source_type === 'qa' ? 'QA' : 'Upload'} · {dataset.sha256?.slice(0, 10) ?? 'chưa hash'}…</div></TableCell><TableCell className="uppercase">{dataset.task}</TableCell><TableCell>{dataset.train_count} / {dataset.validation_count} / {dataset.test_count}{dataset.task === 'whisper' && <div className="text-xs text-text-muted">{(dataset.duration_seconds / 3600).toFixed(2)} giờ</div>}</TableCell><TableCell>{bytes(dataset.size_bytes)}</TableCell><TableCell><Badge value={dataset.status} />{dataset.validation.errors?.length ? <div className="mt-1 max-w-xs text-xs text-red-500">{dataset.validation.errors[0]}</div> : null}</TableCell><TableCell><div className="flex flex-wrap gap-1.5">
          {!['frozen', 'validating'].includes(dataset.status) && <Button size="sm" variant="secondary" isLoading={busy === `validate:${dataset.id}`} onClick={() => act(`validate:${dataset.id}`, () => api.post(`/training/datasets/${dataset.id}/validate`, undefined, { timeout: 600_000 }), 'Đã hoàn tất kiểm tra dataset.')}>Validate</Button>}
          {dataset.status === 'validated' && <Button size="sm" isLoading={busy === `freeze:${dataset.id}`} onClick={() => act(`freeze:${dataset.id}`, () => api.post(`/training/datasets/${dataset.id}/freeze`), 'Dataset đã được đóng băng và sẵn sàng xếp job.') }><Lock size={13} className="mr-1" />Freeze</Button>}
          <Button size="sm" variant="ghost" onClick={() => download(`/training/datasets/${dataset.id}/download`, dataset.task === 'nllb' ? `${dataset.name}.jsonl` : `${dataset.name}.zip`)}><Download size={13} /></Button>
          {dataset.status === 'frozen' && <Button size="sm" variant="ghost" onClick={() => download(`/training/datasets/${dataset.id}/download?kind=manifest`, `${dataset.name}-manifest.json`)}>Manifest</Button>}
        </div></TableCell></TableRow>)}
        {!datasets.length && <TableRow><TableCell colSpan={6} className="py-10 text-center text-text-muted">Chưa có phiên bản dataset.</TableCell></TableRow>}
      </TableBody></Table>
    </CardContent></Card>
  </div>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) { return <label className="space-y-1.5 text-sm"><span className="font-medium">{label}</span>{children}</label>; }

function TrainingTab({ datasets, jobs, events, selectedJob, selectedJobId, setSelectedJobId, isSuperadmin, busy, act, download }: { datasets: Dataset[]; jobs: Job[]; events: JobEvent[]; selectedJob?: Job; selectedJobId: string; setSelectedJobId: (id: string) => void; isSuperadmin: boolean; busy: string; act: (key: string, action: () => Promise<unknown>, success: string) => Promise<void>; download: (url: string, name: string) => void }) {
  const [task, setTask] = useState<TrainingTask>('nllb');
  const [baseModel, setBaseModel] = useState('facebook/nllb-200-distilled-1.3B');
  const frozen = datasets.filter((dataset) => dataset.task === task && dataset.status === 'frozen');
  const frozenNllb = datasets.filter((dataset) => dataset.task === 'nllb' && dataset.status === 'frozen');
  const frozenWhisper = datasets.filter((dataset) => dataset.task === 'whisper' && dataset.status === 'frozen');
  const [datasetId, setDatasetId] = useState('');
  const [nllbDatasetId, setNllbDatasetId] = useState('');
  const [whisperDatasetId, setWhisperDatasetId] = useState('');
  const [preset, setPreset] = useState('recommended');
  const [output, setOutput] = useState('');
  const [config, setConfig] = useState({ epochs: 3, batch_size: 2, gradient_accumulation: 8, learning_rate: 0.0002, seed: 42, max_source_length: 256, max_target_length: 256, runtime: 'local_auto' });
  useEffect(() => { if (!frozen.some((item) => item.id === datasetId)) setDatasetId(frozen[0]?.id ?? ''); }, [task, datasets, datasetId, frozen]);
  useEffect(() => { if (!frozenNllb.some((item) => item.id === nllbDatasetId)) setNllbDatasetId(frozenNllb[0]?.id ?? ''); }, [datasets, nllbDatasetId, frozenNllb]);
  useEffect(() => { if (!frozenWhisper.some((item) => item.id === whisperDatasetId)) setWhisperDatasetId(frozenWhisper[0]?.id ?? ''); }, [datasets, whisperDatasetId, frozenWhisper]);
  const applyPreset = (value: string, chosenTask = task) => {
    setPreset(value);
    const settings = chosenTask === 'nllb' ? {
      quick: [1, 1, 4, 0.0002], recommended: [3, 2, 8, 0.0002], large: [2, 4, 8, 0.0001], colab_free: [3, 1, 16, 0.0002],
    } : { quick: [1, 1, 8, 0.0001], recommended: [3, 1, 16, 0.0001], large: [2, 2, 16, 0.00005], colab_free: [3, 1, 16, 0.0001] };
    const selected = settings[value as keyof typeof settings] ?? settings.recommended;
    setConfig((current) => ({ ...current, epochs: selected[0], batch_size: selected[1], gradient_accumulation: selected[2], learning_rate: selected[3],
      max_source_length: chosenTask === 'nllb' && value === 'colab_free' ? 128 : current.max_source_length,
      max_target_length: chosenTask === 'nllb' && value === 'colab_free' ? 128 : current.max_target_length }));
  };
  const chooseTask = (value: TrainingTask) => { setTask(value); if (value !== 'both') { setBaseModel(value === 'nllb' ? 'facebook/nllb-200-distilled-1.3B' : 'openai/whisper-large-v3-turbo'); applyPreset('recommended', value); } };
  const createJob = () => api.post('/training/jobs', task === 'both'
    ? { task, nllb_dataset_id: nllbDatasetId, whisper_dataset_id: whisperDatasetId, output_version: output, method: 'lora', config: { seed: config.seed, runtime: config.runtime } }
    : { task, dataset_id: datasetId, base_model: baseModel, output_version: output, method: 'lora', config });
  const canQueue = task === 'both' ? Boolean(nllbDatasetId && whisperDatasetId && output) : Boolean(datasetId && output);
  return <div className="grid gap-6 xl:grid-cols-[430px_minmax(0,1fr)]">
    <Card><CardHeader><CardTitle>Cấu hình huấn luyện</CardTitle><CardDescription>Chọn dataset, máy chạy và preset. Cùng một worker có thể chạy trên máy cá nhân, Colab hoặc GPU/CPU thuê ngoài.</CardDescription></CardHeader><CardContent className="space-y-4">
      <div className="grid grid-cols-3 gap-2"><Button variant={task === 'nllb' ? 'primary' : 'secondary'} onClick={() => chooseTask('nllb')}><Languages size={15} className="mr-1" />NLLB</Button><Button variant={task === 'whisper' ? 'primary' : 'secondary'} onClick={() => chooseTask('whisper')}><Mic2 size={15} className="mr-1" />Whisper</Button><Button variant={task === 'both' ? 'primary' : 'secondary'} onClick={() => chooseTask('both')}>Cả hai</Button></div>
      {task === 'both' ? <><Field label="Dataset NLLB đã Frozen"><select value={nllbDatasetId} onChange={(event) => setNllbDatasetId(event.target.value)} className="field"><option value="">Chọn dataset NLLB</option>{frozenNllb.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name}</option>)}</select></Field><Field label="Dataset Whisper đã Frozen"><select value={whisperDatasetId} onChange={(event) => setWhisperDatasetId(event.target.value)} className="field"><option value="">Chọn dataset Whisper</option>{frozenWhisper.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name}</option>)}</select></Field><div className="rounded-xl border border-border bg-background p-3 text-sm">Hệ thống tạo hai job nối tiếp: NLLB dùng preset khuyến nghị trước, Whisper chỉ được worker nhận sau khi NLLB hoàn thành.</div></> : <>
      <Field label="Dataset đã Frozen"><select value={datasetId} onChange={(event) => setDatasetId(event.target.value)} className="field"><option value="">Chọn dataset</option>{frozen.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name} · {dataset.train_count}/{dataset.validation_count}/{dataset.test_count}</option>)}</select></Field>
      <Field label="Base model"><select value={baseModel} onChange={(event) => setBaseModel(event.target.value)} className="field">{task === 'nllb' ? <><option value="facebook/nllb-200-distilled-600M">NLLB distilled 600M · Colab nhẹ hơn</option><option value="facebook/nllb-200-distilled-1.3B">NLLB distilled 1.3B</option></> : <><option value="openai/whisper-small">Whisper Small · Colab nhẹ hơn</option><option value="openai/whisper-large-v3-turbo">Whisper Large v3 Turbo</option><option value="openai/whisper-large-v3">Whisper Large v3</option></>}</select></Field>
      <Field label="Preset"><select value={preset} onChange={(event) => applyPreset(event.target.value)} className="field"><option value="quick">Kiểm tra nhanh</option><option value="recommended">Khuyến nghị</option><option value="colab_free">An toàn hơn cho Colab Free</option><option value="large">Dataset lớn / GPU lớn</option></select></Field>
      <div className="grid grid-cols-2 gap-3">
        <NumberField label="Epochs" value={config.epochs} step="1" set={(value) => setConfig({ ...config, epochs: value })} />
        <NumberField label="Batch size" value={config.batch_size} step="1" set={(value) => setConfig({ ...config, batch_size: value })} />
        <NumberField label="Gradient accum." value={config.gradient_accumulation} step="1" set={(value) => setConfig({ ...config, gradient_accumulation: value })} />
        <NumberField label="Learning rate" value={config.learning_rate} step="0.00001" set={(value) => setConfig({ ...config, learning_rate: value })} />
        <NumberField label="Seed" value={config.seed} step="1" set={(value) => setConfig({ ...config, seed: value })} />
        <Field label="Máy thực thi"><select value={config.runtime} onChange={(event) => setConfig({ ...config, runtime: event.target.value })} className="field"><option value="local_auto">Máy hiện tại · tự chọn CPU/GPU</option><option value="local_gpu">GPU trên máy hiện tại</option><option value="local_cpu">CPU trên máy hiện tại · kiểm tra nhanh</option><option value="external_worker">Worker/GPU thuê bên ngoài</option><option value="colab">Google Colab</option></select></Field>
        {task === 'nllb' && <><NumberField label="Max source length" value={config.max_source_length} step="1" set={(value) => setConfig({ ...config, max_source_length: value })} /><NumberField label="Max target length" value={config.max_target_length} step="1" set={(value) => setConfig({ ...config, max_target_length: value })} /></>}
      </div></>}
      <Field label="Phiên bản đầu ra"><input value={output} onChange={(event) => setOutput(event.target.value)} placeholder={`${task}-v1.1`} className="field" /></Field>
      {config.runtime === 'local_cpu' && <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-3 text-sm text-amber-800 dark:text-amber-200"><Cpu size={16} className="mr-1 inline" />CPU phù hợp để smoke test hoặc model nhỏ; huấn luyện đầy đủ có thể rất chậm.</div>}
      {config.runtime === 'colab' && <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-3 text-sm text-amber-800 dark:text-amber-200"><Cloud size={16} className="mr-1 inline" />Colab cần truy cập cùng database và TRAINING_CONTROL_ROOT. Không chạy inference và training trên cùng GPU.</div>}
      {config.runtime === 'external_worker' && <div className="rounded-xl border border-blue-500/20 bg-blue-500/10 p-3 text-sm text-blue-800 dark:text-blue-200"><Cloud size={16} className="mr-1 inline" />GPU/CPU thuê ngoài cần repository, database trung tâm và vùng lưu trữ dataset dùng chung; worker sẽ xác minh checksum trước khi train.</div>}
      <Button className="w-full" disabled={!isSuperadmin || !canQueue} isLoading={busy === 'job:create'} onClick={() => act('job:create', createJob, 'Job đã được đưa vào hàng đợi. Khởi động worker riêng để bắt đầu train.')}><Play size={16} className="mr-2" />Đưa vào hàng đợi</Button>
      {!isSuperadmin && <p className="text-xs text-text-muted">Chỉ superadmin có quyền tạo hoặc dừng job huấn luyện.</p>}
    </CardContent></Card>
    <div className="space-y-6">
      <Card><CardHeader><div className="flex flex-wrap items-center justify-between gap-3"><div><CardTitle>Live Training Monitor</CardTitle><CardDescription>Polling có xác thực; API cũng cung cấp SSE cho client hỗ trợ Authorization header.</CardDescription></div><select value={selectedJobId} onChange={(event) => setSelectedJobId(event.target.value)} className="field max-w-xs"><option value="">Chọn job</option>{jobs.map((job) => <option key={job.id} value={job.id}>{job.output_version} · {statusLabels[job.status] ?? job.status}</option>)}</select></div></CardHeader><CardContent>
        {selectedJob ? <div className="space-y-5">
          <div className="flex flex-wrap items-center gap-3"><Badge value={selectedJob.status} /><span className="text-sm">{selectedJob.task.toUpperCase()} · {selectedJob.output_version}</span><span className="text-sm text-text-muted">Worker: {selectedJob.worker_id ?? 'chưa nhận'}</span></div>
          <Progress value={selectedJob.progress_percent} label="Tổng tiến độ" />
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4"><Metric label="Epoch" value={selectedJob.current_epoch?.toFixed(2) ?? '—'} /><Metric label="Train loss" value={selectedJob.train_loss?.toFixed(4) ?? '—'} /><Metric label="Validation loss" value={selectedJob.validation_loss?.toFixed(4) ?? '—'} /><Metric label="Bắt đầu" value={date(selectedJob.started_at)} /></div>
          {selectedJob.status === 'queued' && <div className="rounded-xl border border-border bg-background p-3 text-sm"><div className="mb-2 font-medium">Lệnh nhận đúng job này trên Colab/worker</div><code className="block overflow-x-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-200">python -m app.training_worker --job-id {selectedJob.id}</code></div>}
          {selectedJob.error_message && <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-600">{selectedJob.error_code}: {selectedJob.error_message}</div>}
          <div className="flex flex-wrap gap-2"><Button variant="secondary" size="sm" onClick={() => download(`/training/jobs/${selectedJob.id}/log`, `${selectedJob.output_version}.log`)}><Download size={13} className="mr-1" />Tải log</Button>{!finalStates.has(selectedJob.status) && isSuperadmin && <Button variant="danger" size="sm" isLoading={busy === `cancel:${selectedJob.id}`} onClick={() => act(`cancel:${selectedJob.id}`, () => api.post(`/training/jobs/${selectedJob.id}/cancel`), 'Đã gửi yêu cầu dừng job.')}><Square size={13} className="mr-1" />Dừng an toàn</Button>}</div>
          <div className="overflow-hidden rounded-xl border border-border bg-slate-950 text-slate-200"><div className="flex items-center gap-2 border-b border-slate-800 px-4 py-2 text-xs text-slate-400"><Terminal size={14} />LIVE LOGS</div><div className="max-h-72 space-y-1 overflow-auto p-4 font-mono text-xs">{events.map((event) => <div key={event.id} className={event.level === 'error' ? 'text-red-300' : ''}><span className="mr-3 text-slate-500">{new Date(event.created_at).toLocaleTimeString('vi-VN')}</span>{event.message}</div>)}{!events.length && <div className="text-slate-500">Chưa có sự kiện.</div>}</div></div>
        </div> : <div className="py-10 text-center text-text-muted">Chưa có job huấn luyện.</div>}
      </CardContent></Card>
      <Card><CardHeader><CardTitle>Lịch sử training</CardTitle></CardHeader><CardContent><Table><TableHeader><TableRow><TableHead>Job</TableHead><TableHead>Model</TableHead><TableHead>Phiên bản</TableHead><TableHead>Thời gian</TableHead><TableHead>Kết quả</TableHead></TableRow></TableHeader><TableBody>{jobs.map((job) => <TableRow key={job.id} onClick={() => setSelectedJobId(job.id)} className="cursor-pointer"><TableCell className="font-mono text-xs">{job.id.slice(0, 8)}</TableCell><TableCell className="uppercase">{job.task}</TableCell><TableCell>{job.output_version}</TableCell><TableCell>{date(job.created_at)}</TableCell><TableCell><Badge value={job.status} /></TableCell></TableRow>)}{!jobs.length && <TableRow><TableCell colSpan={5} className="py-8 text-center text-text-muted">Chưa có lịch sử job.</TableCell></TableRow>}</TableBody></Table></CardContent></Card>
    </div>
  </div>;
}

function NumberField({ label, value, step, set }: { label: string; value: number; step: string; set: (value: number) => void }) { return <Field label={label}><input type="number" value={value} step={step} onChange={(event) => set(Number(event.target.value))} className="field" /></Field>; }

function ModelsTab({ artifacts, isSuperadmin, busy, act, setTab }: { artifacts: Artifact[]; isSuperadmin: boolean; busy: string; act: (key: string, action: () => Promise<unknown>, success: string) => Promise<void>; setTab: (tab: Tab) => void }) {
  return <div className="space-y-6"><Card><CardHeader><CardTitle>Model Registry</CardTitle><CardDescription>Artifact hoàn tất training vẫn là Candidate. Validate checksum trước, sau đó stage canary và reload inference có kiểm soát.</CardDescription></CardHeader><CardContent>
    <Table><TableHeader><TableRow><TableHead>Component</TableHead><TableHead>Version</TableHead><TableHead>Metrics</TableHead><TableHead>Artifact</TableHead><TableHead>Deployment</TableHead><TableHead>Thao tác</TableHead></TableRow></TableHeader><TableBody>{artifacts.map((artifact) => <TableRow key={artifact.id}><TableCell className="font-semibold uppercase">{artifact.component}</TableCell><TableCell><div>{artifact.version}</div><div className="text-xs text-text-muted">{artifact.base_model}</div></TableCell><TableCell>{Object.keys(artifact.metrics).length ? Object.entries(artifact.metrics).map(([key, value]) => <div key={key} className="text-xs">{key}: {typeof value === 'number' ? value.toFixed(4) : typeof value === 'string' ? value : `${Object.keys((value as object) ?? {}).length} nhóm`}</div>) : <span className="text-text-muted">Chưa có test metric</span>}</TableCell><TableCell><Badge value={artifact.status} /><div className="mt-1 text-xs text-text-muted">{bytes(artifact.size_bytes)} · {artifact.sha256.slice(0, 8)}…</div><div className="mt-1 max-w-52 truncate text-xs text-text-muted" title={artifact.storage_uri}>{artifact.storage_uri}</div></TableCell><TableCell><Badge value={artifact.deployment_state} />{artifact.requires_runtime_reload && <div className="mt-1 text-xs text-amber-600">Cần reload runtime</div>}</TableCell><TableCell><div className="flex flex-wrap gap-1.5">
      {artifact.status !== 'validated' && <Button size="sm" variant="secondary" isLoading={busy === `artifact:${artifact.id}`} onClick={() => act(`artifact:${artifact.id}`, () => api.post(`/training/models/${artifact.id}/validate`), 'Artifact đã vượt qua kiểm tra checksum và manifest.')}>Kiểm tra</Button>}
      {artifact.status === 'validated' && isSuperadmin && artifact.deployment_state === 'candidate' && <Button size="sm" variant="secondary" onClick={() => act(`canary:${artifact.id}`, () => api.post(`/training/models/${artifact.id}/canary?percent=5`), 'Đã ghi nhận canary 5%. Cần reload inference worker trước khi chuyển traffic.')}>Canary 5%</Button>}
      {artifact.status === 'validated' && isSuperadmin && artifact.deployment_state === 'canary' && <Button size="sm" onClick={() => act(`promote:${artifact.id}`, () => api.post(`/training/models/${artifact.id}/promote`), 'Đã ghi nhận promote. Cần restart/reload runtime và chạy health check.')}>Promote</Button>}
      {isSuperadmin && artifact.deployment_state === 'active' && <Button size="sm" variant="danger" onClick={() => act(`rollback:${artifact.id}`, () => api.post(`/training/models/${artifact.id}/rollback`), 'Đã ghi nhận rollback. Cần restart/reload runtime.')}>Rollback</Button>}
      <Button size="sm" variant="ghost" onClick={() => setTab('playground')}>A/B</Button>
    </div></TableCell></TableRow>)}{!artifacts.length && <TableRow><TableCell colSpan={6} className="py-10 text-center text-text-muted">Chưa có model artifact. Artifact sẽ được đăng ký tự động sau khi worker hoàn thành job.</TableCell></TableRow>}</TableBody></Table>
  </CardContent></Card>
  <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 text-sm text-amber-800 dark:text-amber-200"><ShieldCheck size={18} className="mr-2 inline" /><b>Kích hoạt có kiểm soát:</b> control plane chỉ ghi nhận phiên bản. Runtime hiện tại nạp model khi startup, vì vậy operator phải cập nhật đường dẫn model, restart/reload worker và chạy health check. Giao diện không tuyên bố “hot-swap” khi việc đó chưa xảy ra.</div>
  </div>;
}

function PlaygroundTab({ capability }: { capability?: { available: boolean; reason: string } }) {
  return <div className="grid gap-6 xl:grid-cols-2">
    <PlaygroundCard icon={Languages} title="NLLB A/B Test" fields={<><Field label="Chiều dịch"><select className="field" disabled><option>Việt → Anh</option></select></Field><Field label="Câu nguồn"><textarea className="field min-h-28" disabled placeholder="Chọn candidate runner để bắt đầu…" /></Field></>} />
    <PlaygroundCard icon={Mic2} title="Whisper A/B Test" fields={<><Field label="Audio WAV"><input className="field" type="file" disabled /></Field><Field label="Transcript chuẩn tùy chọn"><input className="field" disabled /></Field></>} />
    <div className="xl:col-span-2 rounded-xl border border-amber-500/20 bg-amber-500/10 p-5 text-sm text-amber-800 dark:text-amber-200"><AlertTriangle size={18} className="mr-2 inline" /><b>Playground đang khóa an toàn:</b> {capability?.reason ?? 'chưa có candidate inference runner'}. Backend không tạo kết quả giả và không nạp đồng thời model thứ hai vào GPU inference hiện tại. Khi triển khai worker A/B riêng, tab này có thể bật mà không thay đổi dataset registry hoặc model registry.</div>
  </div>;
}

function PlaygroundCard({ icon: Icon, title, fields }: { icon: typeof Languages; title: string; fields: React.ReactNode }) {
  return <Card className="opacity-75"><CardHeader><CardTitle className="flex items-center gap-2"><Icon size={19} />{title}</CardTitle><CardDescription>Đánh giá mù Model A / Model B; tên model chỉ hiện sau khi reviewer chọn.</CardDescription></CardHeader><CardContent className="space-y-4">{fields}<Button disabled className="w-full"><GitCompareArrows size={15} className="mr-2" />So sánh</Button></CardContent></Card>;
}
