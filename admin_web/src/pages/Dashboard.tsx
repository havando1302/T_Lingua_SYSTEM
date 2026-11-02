import { useEffect, useState } from 'react';
import { useTimedMessage } from '../lib/useTimedMessage';
import api, { apiErrorMessage } from '../lib/api';
import { Button } from '../components/ui/Button';
import { Activity, Users, Zap, AlertCircle, HardDrive, Cpu, MemoryStick, Mic, Languages, Volume2, Sparkles } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { useAuthUser } from '../lib/auth';

interface DashboardMetrics {
  total_translations: number;
  flagged_translations: number;
  avg_latency: number;
  unique_clients: number;
  started_at: string;
  sample_limit: number;
}

interface TimeSeriesMetric {
  date: string;
  requests: number;
  avg_latency: number;
}

interface SystemStatus {
  cpu_usage: number;
  ram_usage: number;
  ram_total: number;
  disk_usage: number;
  disk_total: number;
  gpu?: {
    cuda_available: boolean;
    device_name?: string;
    allocated_gb?: number;
    reserved_gb?: number;
    total_gb?: number;
  } | null;
  inference_runtime: {
    device?: string;
    whisper_device?: string;
    whisper_backend?: string;
    whisper_model_id?: string;
    whisper_compute_type?: string;
    whisper_cpu_fallback?: boolean;
    nllb_model_id?: string;
    nllb_device?: string;
    nllb_dtype?: string;
    tts_model_eng?: string;
    tts_model_vie?: string;
    tts_device?: string;
    tts_dtype?: string;
    deepfilter_model_id?: string;
    deepfilter_enabled?: boolean;
    denoise_device?: string;
    model_load_seconds?: number;
  } | null;
}

function formatWhisperName(modelId?: string): string {
  if (!modelId) return 'Whisper Large-v3-Turbo';
  const lower = modelId.toLowerCase();
  if (lower.includes('turbo')) return 'Whisper Large-v3-Turbo';
  if (lower.includes('large-v3')) return 'Whisper Large-v3';
  if (lower.includes('large-v2')) return 'Whisper Large-v2';
  if (lower.includes('large')) return 'Whisper Large';
  if (lower.includes('medium')) return 'Whisper Medium';
  if (lower.includes('small')) return 'Whisper Small';
  if (lower.includes('base')) return 'Whisper Base';
  if (lower.includes('tiny')) return 'Whisper Tiny';
  const parts = modelId.split('/');
  return parts[parts.length - 1];
}

function formatNllbName(modelId?: string): string {
  if (!modelId) return 'NLLB-200 (1.3B)';
  const lower = modelId.toLowerCase();
  if (lower.includes('1.3b')) return 'NLLB-200 (1.3B Distilled)';
  if (lower.includes('600m')) return 'NLLB-200 (600M Distilled)';
  if (lower.includes('3.3b')) return 'NLLB-200 (3.3B)';
  const parts = modelId.split('/');
  return parts[parts.length - 1];
}

function finiteNumber(value: unknown): number {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function normalizeDashboardMetrics(value: unknown): DashboardMetrics {
  const data = value && typeof value === 'object' ? value as Record<string, unknown> : {};
  return {
    total_translations: Math.max(0, Math.trunc(finiteNumber(data.total_translations))),
    flagged_translations: Math.max(0, Math.trunc(finiteNumber(data.flagged_translations))),
    avg_latency: Math.max(0, finiteNumber(data.avg_latency)),
    unique_clients: Math.max(0, Math.trunc(finiteNumber(data.unique_clients))),
    started_at: typeof data.started_at === 'string' ? data.started_at : '',
    sample_limit: Math.max(0, Math.trunc(finiteNumber(data.sample_limit))),
  };
}

function normalizeTimeSeries(value: unknown): TimeSeriesMetric[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item) => {
    if (!item || typeof item !== 'object') return [];
    const row = item as Record<string, unknown>;
    if (typeof row.date !== 'string') return [];
    return [{
      date: row.date,
      requests: Math.max(0, Math.trunc(finiteNumber(row.requests))),
      avg_latency: Math.max(0, finiteNumber(row.avg_latency)),
    }];
  });
}

function normalizeSystemStatus(value: unknown): SystemStatus {
  const data = value && typeof value === 'object' ? value as Record<string, unknown> : {};
  const runtime = data.inference_runtime && typeof data.inference_runtime === 'object'
    ? data.inference_runtime as Record<string, unknown>
    : null;
  const gpu = data.gpu && typeof data.gpu === 'object'
    ? data.gpu as Record<string, unknown>
    : null;
  const optionalText = (field: unknown) => typeof field === 'string' && field.trim() ? field : undefined;
  return {
    cpu_usage: Math.min(100, Math.max(0, finiteNumber(data.cpu_usage))),
    ram_usage: Math.min(100, Math.max(0, finiteNumber(data.ram_usage))),
    ram_total: Math.max(0, finiteNumber(data.ram_total)),
    disk_usage: Math.min(100, Math.max(0, finiteNumber(data.disk_usage))),
    disk_total: Math.max(0, finiteNumber(data.disk_total)),
    gpu: gpu ? {
      cuda_available: gpu.cuda_available === true,
      device_name: optionalText(gpu.device_name),
      allocated_gb: finiteNumber(gpu.allocated_gb),
      reserved_gb: finiteNumber(gpu.reserved_gb),
      total_gb: finiteNumber(gpu.total_gb),
    } : null,
    inference_runtime: runtime ? {
      device: optionalText(runtime.device) || 'cpu',
      whisper_device: optionalText(runtime.whisper_device),
      whisper_backend: optionalText(runtime.whisper_backend) || 'transformers',
      whisper_model_id: optionalText(runtime.whisper_model_id) || 'openai/whisper-large-v3-turbo',
      whisper_compute_type: optionalText(runtime.whisper_compute_type) || 'float16',
      whisper_cpu_fallback: runtime.whisper_cpu_fallback === true,
      nllb_model_id: optionalText(runtime.nllb_model_id) || 'facebook/nllb-200-distilled-1.3B',
      nllb_device: optionalText(runtime.nllb_device) || optionalText(runtime.device) || 'cuda',
      nllb_dtype: optionalText(runtime.nllb_dtype) || 'float16',
      tts_model_eng: optionalText(runtime.tts_model_eng) || 'facebook/mms-tts-eng',
      tts_model_vie: optionalText(runtime.tts_model_vie) || 'facebook/mms-tts-vie',
      tts_device: optionalText(runtime.tts_device) || optionalText(runtime.device) || 'cuda',
      tts_dtype: optionalText(runtime.tts_dtype) || 'float32',
      deepfilter_model_id: optionalText(runtime.deepfilter_model_id) || 'DeepFilterNet3',
      deepfilter_enabled: runtime.deepfilter_enabled !== false,
      denoise_device: optionalText(runtime.denoise_device) || optionalText(runtime.device) || 'cuda',
      model_load_seconds: Math.max(0, finiteNumber(runtime.model_load_seconds)),
    } : null,
  };
}

let cachedDashboard: {
  metrics: DashboardMetrics;
  sysStatus: SystemStatus;
  timeSeries: TimeSeriesMetric[];
  updatedAt: Date | null;
} | null = null;

const Dashboard = () => {
  const user = useAuthUser();
  const canViewSystemStatus = Boolean(user);
  const [metrics, setMetrics] = useState<DashboardMetrics>(() => cachedDashboard?.metrics || {
    total_translations: 0,
    flagged_translations: 0,
    avg_latency: 0.0,
    unique_clients: 0,
    started_at: '',
    sample_limit: 1000
  });

  const [sysStatus, setSysStatus] = useState<SystemStatus>(() => cachedDashboard?.sysStatus || {
    cpu_usage: 0,
    ram_usage: 0,
    ram_total: 0,
    disk_usage: 0,
    disk_total: 0,
    inference_runtime: null
  });

  const [timeSeries, setTimeSeries] = useState<TimeSeriesMetric[]>(() => cachedDashboard?.timeSeries || []);
  const [timeRange, setTimeRange] = useState<'all' | 'today'>('all');
  const [loading, setLoading] = useState(() => !cachedDashboard);

  const [error, setError] = useTimedMessage('');
  const [systemError, setSystemError] = useState('');
  const [updatedAt, setUpdatedAt] = useState<Date | null>(() => cachedDashboard?.updatedAt || null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let pending = false;
    const fetchData = async () => {
      if (pending) return;
      pending = true;
      setLoading(true);
      try {
        const params = new URLSearchParams({
          time_range: timeRange,
          tz_offset_minutes: String(new Date().getTimezoneOffset()),
        });
        const query = `?${params.toString()}`;
        const requests = [
          api.get(`/metrics/dashboard${query}`, { signal: controller.signal }),
          api.get(`/metrics/timeseries${query}`, { signal: controller.signal }),
          canViewSystemStatus ? api.get('/system/status', { signal: controller.signal }) : Promise.resolve(null),
        ] as const;
        const [metricsResult, seriesResult, systemResult] = await Promise.allSettled(requests);
        if (controller.signal.aborted) return;
        if (metricsResult.status === 'rejected') throw metricsResult.reason;
        if (seriesResult.status === 'rejected') throw seriesResult.reason;
        setError('');
        const now = new Date();
        const nextMetrics = normalizeDashboardMetrics(metricsResult.value.data);
        const nextSeries = normalizeTimeSeries(seriesResult.value.data);
        let nextSys = sysStatus;
        setUpdatedAt(now);
        setMetrics(nextMetrics);
        setTimeSeries(nextSeries);
        if (systemResult.status === 'fulfilled' && systemResult.value) {
          nextSys = normalizeSystemStatus(systemResult.value.data);
          setSysStatus(nextSys);
          setSystemError('');
        } else if (systemResult.status === 'rejected') {
          setSystemError(apiErrorMessage(systemResult.reason));
        }
        cachedDashboard = {
          metrics: nextMetrics,
          sysStatus: nextSys,
          timeSeries: nextSeries,
          updatedAt: now,
        };
      } catch (err) {
        if (!controller.signal.aborted) setError(apiErrorMessage(err));
      } finally {
        pending = false;
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => { controller.abort(); clearInterval(interval); };
  }, [reload, canViewSystemStatus, timeRange, setError]);

  if (!updatedAt) return <div className="space-y-4">
    <h1 className="text-3xl font-bold">Bảng điều khiển</h1>
    <p role={error ? 'alert' : 'status'}>{error || (loading ? 'Đang tải số liệu…' : 'Chưa tải được số liệu.')}</p>
    {error && <Button onClick={() => setReload(value => value + 1)}>Thử lại</Button>}
  </div>;

  const statCards = [
    { title: 'Tổng lượt dịch', value: metrics.total_translations, icon: Activity, color: 'text-blue-500', bg: 'bg-blue-500/10' },
    { title: 'Khách hàng đã phục vụ', value: metrics.unique_clients, icon: Users, color: 'text-green-500', bg: 'bg-green-500/10' },
    { title: 'Độ trễ phản hồi TB (s)', value: metrics.avg_latency.toFixed(3), icon: Zap, color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
    { title: 'Bản dịch đang bị báo lỗi', value: metrics.flagged_translations, icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-500/10' },
  ];

  const sysCards = [
    { title: 'Sử dụng CPU', value: `${sysStatus.cpu_usage}%`, icon: Cpu },
    { title: 'Sử dụng RAM', value: `${sysStatus.ram_usage}% (${sysStatus.ram_total}GB)`, icon: MemoryStick },
    { title: 'Sử dụng Ổ cứng', value: `${sysStatus.disk_usage}% (${sysStatus.disk_total}GB)`, icon: HardDrive },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Bảng điều khiển</h1>
          <p className="text-xs text-text-muted mt-1">
            Cập nhật: {updatedAt.toLocaleTimeString('vi-VN')} {timeRange === 'today' ? '· Hôm nay' : '· Toàn thời gian'}
            {loading && ' · Đang cập nhật…'}
          </p>
        </div>
        <div className="flex items-center gap-1 bg-surface p-1 rounded-lg border border-border">
          <button
            type="button"
            onClick={() => setTimeRange('all')}
            aria-pressed={timeRange === 'all'}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${timeRange === 'all' ? 'bg-primary text-white shadow-sm' : 'text-text-muted hover:text-text'}`}
          >
            Toàn thời gian
          </button>
          <button
            type="button"
            onClick={() => setTimeRange('today')}
            aria-pressed={timeRange === 'today'}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${timeRange === 'today' ? 'bg-primary text-white shadow-sm' : 'text-text-muted hover:text-text'}`}
          >
            Hôm nay
          </button>
        </div>
      </div>
      {error && <div role="alert" className="rounded-lg bg-amber-500/10 p-3 text-amber-700">{error} Đang hiển thị số liệu lần trước.
        <Button variant="ghost" onClick={() => setReload(value => value + 1)}>Thử lại</Button>
      </div>}
      {systemError && canViewSystemStatus && <div role="status" className="rounded-lg bg-amber-500/10 p-3 text-amber-700">
        Không tải được tài nguyên hệ thống. Các số liệu dịch thuật vẫn được cập nhật bình thường.
      </div>}


      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, i) => (
          <Card key={i}>
            <CardContent className="p-6 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-muted mb-1">{stat.title}</p>
                <h3 className="text-2xl font-bold">{stat.value}</h3>
              </div>
              <div className={`p-3 rounded-full ${stat.bg} ${stat.color}`}>
                <stat.icon size={24} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className={`grid grid-cols-1 gap-6 ${canViewSystemStatus ? 'lg:grid-cols-3' : ''}`}>
        <Card className={canViewSystemStatus ? 'lg:col-span-2' : ''}>
          <CardHeader>
            <CardTitle>Lưu lượng dịch thực tế</CardTitle>
            <CardDescription>Số lượng yêu cầu dịch thuật được xử lý bởi AI theo ngày.</CardDescription>
          </CardHeader>
          <CardContent>
            {timeSeries.length === 0 ? <div className="flex h-[300px] items-center justify-center px-4 text-center text-sm text-text-muted">
              Chưa có dữ liệu dịch thuật trong phạm vi đã chọn.
            </div> : <div className="h-[300px] w-full mt-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timeSeries}>
                  <defs>
                    <linearGradient id="colorReq" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text)', borderRadius: '0.5rem' }} 
                    itemStyle={{ color: 'var(--text)' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="requests"
                    name="Yêu cầu"
                    stroke="var(--primary)"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorReq)"
                    dot={{ r: 5, fill: 'var(--primary)', stroke: '#ffffff', strokeWidth: 2 }}
                    activeDot={{ r: 7 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>}
          </CardContent>
        </Card>

        {canViewSystemStatus && <Card>
          <CardHeader>
            <CardTitle>Tài nguyên hệ thống</CardTitle>
            <CardDescription>Tình trạng phần cứng máy chủ realtime</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 mt-4">
            {sysCards.map((sys, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/10 text-primary rounded-lg">
                    <sys.icon size={20} />
                  </div>
                  <span className="font-medium text-text">{sys.title}</span>
                </div>
                <span className="text-text-muted">{sys.value}</span>
              </div>
            ))}
          </CardContent>
        </Card>}
      </div>

      {/* KHU VỰC: CÁC MÔ HÌNH AI ĐANG VẬN HÀNH THEO THỜI GIAN THỰC */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <CardTitle className="flex items-center gap-2.5 text-xl font-bold">
                <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
                  <Cpu size={20} />
                </div>
                Mô hình AI đang vận hành theo thời gian thực
              </CardTitle>
              <CardDescription className="mt-1">
                Các phiên bản mô hình AI (STT, MT, TTS, Denoise) đang được tải vào bộ nhớ và xử lý trực tiếp trên hệ thống T-Lingua.
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                {sysStatus.inference_runtime?.device === 'cuda'
                  ? `GPU ${sysStatus.gpu?.device_name || 'Tesla T4'} · CUDA Active`
                  : 'CPU Computing Mode'}
              </span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* CARD 1: STT - Whisper */}
            <div className="p-4 rounded-xl border border-border bg-surface/50 hover:border-primary/40 transition-all flex flex-col justify-between space-y-3">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-500">
                      <Mic size={18} />
                    </div>
                    <span className="text-xs font-bold uppercase tracking-wider text-text-muted">
                      Nhận dạng giọng nói (STT)
                    </span>
                  </div>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 text-emerald-600">
                    Sẵn sàng
                  </span>
                </div>
                <h4 className="font-semibold text-text text-base truncate" title={sysStatus.inference_runtime?.whisper_model_id || 'whisper-large-v3-turbo'}>
                  {formatWhisperName(sysStatus.inference_runtime?.whisper_model_id)}
                </h4>
                <p className="text-xs text-text-muted font-mono mt-0.5 truncate" title={sysStatus.inference_runtime?.whisper_model_id || 'openai/whisper-large-v3-turbo'}>
                  {sysStatus.inference_runtime?.whisper_model_id || 'openai/whisper-large-v3-turbo'}
                </p>
              </div>
              <div className="space-y-2 pt-2 border-t border-border/60">
                <div className="flex flex-wrap gap-1.5">
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
                    {sysStatus.inference_runtime?.whisper_device?.toUpperCase() || (sysStatus.inference_runtime?.device === 'cuda' ? 'CUDA (GPU)' : 'CPU')}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-primary/10 text-primary">
                    {sysStatus.inference_runtime?.whisper_compute_type || 'float16'}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-surface text-text-muted border border-border">
                    {sysStatus.inference_runtime?.whisper_backend === 'transformers' ? 'Transformers' : 'CTranslate2'}
                  </span>
                </div>
                {sysStatus.inference_runtime?.whisper_cpu_fallback && (
                  <p className="text-[11px] text-amber-500 font-medium">⚠️ Đang dùng CPU dự phòng</p>
                )}
                <p className="text-[11px] text-text-muted leading-tight">
                  Chuyển đổi luồng giọng nói 16kHz song ngữ thành văn bản chuẩn xác
                </p>
              </div>
            </div>

            {/* CARD 2: MT - NLLB */}
            <div className="p-4 rounded-xl border border-border bg-surface/50 hover:border-primary/40 transition-all flex flex-col justify-between space-y-3">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-blue-500/10 text-blue-500">
                      <Languages size={18} />
                    </div>
                    <span className="text-xs font-bold uppercase tracking-wider text-text-muted">
                      Dịch thuật ngữ cảnh (MT)
                    </span>
                  </div>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 text-emerald-600">
                    Sẵn sàng
                  </span>
                </div>
                <h4 className="font-semibold text-text text-base truncate" title={sysStatus.inference_runtime?.nllb_model_id || 'facebook/nllb-200-distilled-1.3B'}>
                  {formatNllbName(sysStatus.inference_runtime?.nllb_model_id)}
                </h4>
                <p className="text-xs text-text-muted font-mono mt-0.5 truncate" title={sysStatus.inference_runtime?.nllb_model_id || 'facebook/nllb-200-distilled-1.3B'}>
                  {sysStatus.inference_runtime?.nllb_model_id || 'facebook/nllb-200-distilled-1.3B'}
                </p>
              </div>
              <div className="space-y-2 pt-2 border-t border-border/60">
                <div className="flex flex-wrap gap-1.5">
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400">
                    Meta NLLB-200
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-primary/10 text-primary">
                    VIE ⇄ ENG
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-surface text-text-muted border border-border">
                    {sysStatus.inference_runtime?.nllb_device?.toUpperCase() || (sysStatus.inference_runtime?.device === 'cuda' ? 'CUDA' : 'CPU')}
                  </span>
                </div>
                <p className="text-[11px] text-text-muted leading-tight">
                  Mô hình dịch dịch thuật ngữ cảnh kết hợp bộ nhớ từ vựng Glossary
                </p>
              </div>
            </div>

            {/* CARD 3: TTS - VITS */}
            <div className="p-4 rounded-xl border border-border bg-surface/50 hover:border-primary/40 transition-all flex flex-col justify-between space-y-3">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-amber-500/10 text-amber-500">
                      <Volume2 size={18} />
                    </div>
                    <span className="text-xs font-bold uppercase tracking-wider text-text-muted">
                      Đọc phát âm (TTS)
                    </span>
                  </div>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 text-emerald-600">
                    Sẵn sàng
                  </span>
                </div>
                <h4 className="font-semibold text-text text-base truncate" title="Meta VITS MMS (Vie & Eng)">
                  Meta MMS-TTS (VITS)
                </h4>
                <p className="text-xs text-text-muted font-mono mt-0.5 truncate" title="facebook/mms-tts-vie & facebook/mms-tts-eng">
                  mms-tts-vie · mms-tts-eng
                </p>
              </div>
              <div className="space-y-2 pt-2 border-t border-border/60">
                <div className="flex flex-wrap gap-1.5">
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400">
                    VITS Architecture
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-primary/10 text-primary">
                    Song ngữ
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-surface text-text-muted border border-border">
                    22.05 kHz
                  </span>
                </div>
                <p className="text-[11px] text-text-muted leading-tight">
                  Tổng hợp giọng nói tự nhiên, mượt mà theo ngữ điệu câu dịch
                </p>
              </div>
            </div>

            {/* CARD 4: Filter & VAD */}
            <div className="p-4 rounded-xl border border-border bg-surface/50 hover:border-primary/40 transition-all flex flex-col justify-between space-y-3">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500">
                      <Sparkles size={18} />
                    </div>
                    <span className="text-xs font-bold uppercase tracking-wider text-text-muted">
                      Lọc ồn & VAD (Audio)
                    </span>
                  </div>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 text-emerald-600">
                    {sysStatus.inference_runtime?.deepfilter_enabled !== false ? 'Kích hoạt' : 'Tắt'}
                  </span>
                </div>
                <h4 className="font-semibold text-text text-base truncate" title={sysStatus.inference_runtime?.deepfilter_model_id || 'DeepFilterNet3'}>
                  {sysStatus.inference_runtime?.deepfilter_model_id || 'DeepFilterNet3'}
                </h4>
                <p className="text-xs text-text-muted font-mono mt-0.5 truncate" title="WebRTC VAD + DeepFilterNet3">
                  DeepFilterNet3 · WebRTC VAD
                </p>
              </div>
              <div className="space-y-2 pt-2 border-t border-border/60">
                <div className="flex flex-wrap gap-1.5">
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                    Khử tạp âm
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-primary/10 text-primary">
                    Realtime
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-surface text-text-muted border border-border">
                    {sysStatus.inference_runtime?.denoise_device?.toUpperCase() || (sysStatus.inference_runtime?.device === 'cuda' ? 'CUDA' : 'CPU')}
                  </span>
                </div>
                <p className="text-[11px] text-text-muted leading-tight">
                  Tách lọc tiếng ồn môi trường và phát hiện chính xác giọng nói người
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
