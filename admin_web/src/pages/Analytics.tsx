import { useEffect, useState, useMemo, type ReactNode } from 'react';
import { useTimedMessage } from '../lib/useTimedMessage';
import api, { apiErrorMessage } from '../lib/api';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, LineChart, Line, Legend } from 'recharts';
import { Activity, Gauge, Clock, Zap, Calendar, Filter, RotateCcw, ArrowRight, Languages, ShieldCheck, CircleAlert, Database, TimerReset } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';

interface LanguageMetric {
  name: string;
  value: number;
}

interface TimeSeriesMetric {
  date: string;
  requests: number;
  avg_latency: number;
}

interface LatencyPercentile {
  p50: number;
  p90: number;
  p99: number;
  avg: number;
  min: number;
  max: number;
  count: number;
  missing_count: number;
  availability_pct: number;
  slo_ms: number;
  breach_count: number;
  breach_rate: number;
}

interface StageTimeSeriesMetric {
  date: string;
  requests: number;
  stt_p90: number;
  translate_p90: number;
  tts_first_chunk_p90: number;
  end_to_end_p90: number;
}

interface SlowTurnMetric {
  turn_id: string;
  created_at: string;
  source_lang: string;
  target_lang: string;
  status: string;
  bottleneck: string | null;
  queue_wait_ms: number;
  stt_ms: number;
  translate_ms: number;
  tts_first_chunk_ms: number;
  tts_total_ms: number;
  end_to_end_ms: number;
}

interface PipelineMetrics {
  active_turns: number;
  total_completed: number;
  total_success: number;
  total_errors: number;
  total_cancelled: number;
  success_rate: number;
  error_rate: number;
  throughput_turns_per_sec: number;
  scope?: 'since_process_start' | 'persisted';
  stage_metrics_available?: boolean;
  latencies_ms: {
    queue_wait: LatencyPercentile;
    stt: LatencyPercentile;
    translate: LatencyPercentile;
    tts_first_chunk: LatencyPercentile;
    tts_total: LatencyPercentile;
    end_to_end: LatencyPercentile;
  };
  bottleneck: string | null;
  error_breakdown: Array<{ stage: string; count: number }>;
  stage_timeseries: StageTimeSeriesMetric[];
  slowest_turns: SlowTurnMetric[];
}

type TimeFilterPreset = 'all' | 'today' | '7d' | 'week' | '30d' | 'month' | 'custom';

function getLocalTodayStr(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function finiteNumber(value: unknown): number {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
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

function normalizeLanguages(value: unknown): LanguageMetric[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item) => {
    if (!item || typeof item !== 'object') return [];
    const row = item as Record<string, unknown>;
    const count = Math.max(0, Math.trunc(finiteNumber(row.value)));
    if (typeof row.name !== 'string' || !row.name.trim() || count === 0) return [];
    return [{ name: row.name, value: count }];
  });
}

function normalizeLatency(value: unknown): LatencyPercentile {
  const data = value && typeof value === 'object' ? value as Record<string, unknown> : {};
  return {
    p50: Math.max(0, finiteNumber(data.p50)),
    p90: Math.max(0, finiteNumber(data.p90)),
    p99: Math.max(0, finiteNumber(data.p99)),
    avg: Math.max(0, finiteNumber(data.avg)),
    min: Math.max(0, finiteNumber(data.min)),
    max: Math.max(0, finiteNumber(data.max)),
    count: Math.max(0, Math.trunc(finiteNumber(data.count))),
    missing_count: Math.max(0, Math.trunc(finiteNumber(data.missing_count))),
    availability_pct: Math.min(100, Math.max(0, finiteNumber(data.availability_pct))),
    slo_ms: Math.max(0, finiteNumber(data.slo_ms)),
    breach_count: Math.max(0, Math.trunc(finiteNumber(data.breach_count))),
    breach_rate: Math.min(100, Math.max(0, finiteNumber(data.breach_rate))),
  };
}

function normalizeStageTimeSeries(value: unknown): StageTimeSeriesMetric[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item) => {
    if (!item || typeof item !== 'object') return [];
    const row = item as Record<string, unknown>;
    if (typeof row.date !== 'string') return [];
    return [{
      date: row.date,
      requests: Math.max(0, Math.trunc(finiteNumber(row.requests))),
      stt_p90: Math.max(0, finiteNumber(row.stt_p90)),
      translate_p90: Math.max(0, finiteNumber(row.translate_p90)),
      tts_first_chunk_p90: Math.max(0, finiteNumber(row.tts_first_chunk_p90)),
      end_to_end_p90: Math.max(0, finiteNumber(row.end_to_end_p90)),
    }];
  });
}

function normalizeSlowTurns(value: unknown): SlowTurnMetric[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item) => {
    if (!item || typeof item !== 'object') return [];
    const row = item as Record<string, unknown>;
    if (typeof row.turn_id !== 'string' || typeof row.created_at !== 'string') return [];
    return [{
      turn_id: row.turn_id,
      created_at: row.created_at,
      source_lang: typeof row.source_lang === 'string' ? row.source_lang : '—',
      target_lang: typeof row.target_lang === 'string' ? row.target_lang : '—',
      status: typeof row.status === 'string' ? row.status : 'unknown',
      bottleneck: typeof row.bottleneck === 'string' ? row.bottleneck : null,
      queue_wait_ms: Math.max(0, finiteNumber(row.queue_wait_ms)),
      stt_ms: Math.max(0, finiteNumber(row.stt_ms)),
      translate_ms: Math.max(0, finiteNumber(row.translate_ms)),
      tts_first_chunk_ms: Math.max(0, finiteNumber(row.tts_first_chunk_ms)),
      tts_total_ms: Math.max(0, finiteNumber(row.tts_total_ms)),
      end_to_end_ms: Math.max(0, finiteNumber(row.end_to_end_ms)),
    }];
  });
}

function normalizePipeline(value: unknown): PipelineMetrics | null {
  if (!value || typeof value !== 'object') return null;
  const data = value as Record<string, unknown>;
  const latencies = data.latencies_ms && typeof data.latencies_ms === 'object'
    ? data.latencies_ms as Record<string, unknown> : {};
  return {
    active_turns: Math.max(0, Math.trunc(finiteNumber(data.active_turns))),
    total_completed: Math.max(0, Math.trunc(finiteNumber(data.total_completed))),
    total_success: Math.max(0, Math.trunc(finiteNumber(data.total_success ?? data.total_completed))),
    total_errors: Math.max(0, Math.trunc(finiteNumber(data.total_errors))),
    total_cancelled: Math.max(0, Math.trunc(finiteNumber(data.total_cancelled))),
    success_rate: Math.min(100, Math.max(0, finiteNumber(data.success_rate))),
    error_rate: Math.min(100, Math.max(0, finiteNumber(data.error_rate))),
    throughput_turns_per_sec: Math.max(0, finiteNumber(data.throughput_turns_per_sec)),
    scope: data.scope === 'since_process_start' ? 'since_process_start' : 'persisted',
    stage_metrics_available: data.stage_metrics_available === true,
    latencies_ms: {
      queue_wait: normalizeLatency(latencies.queue_wait),
      stt: normalizeLatency(latencies.stt),
      translate: normalizeLatency(latencies.translate),
      tts_first_chunk: normalizeLatency(latencies.tts_first_chunk),
      tts_total: normalizeLatency(latencies.tts_total),
      end_to_end: normalizeLatency(latencies.end_to_end),
    },
    bottleneck: typeof data.bottleneck === 'string' ? data.bottleneck : null,
    error_breakdown: Array.isArray(data.error_breakdown) ? data.error_breakdown.flatMap((item) => {
      if (!item || typeof item !== 'object') return [];
      const row = item as Record<string, unknown>;
      if (typeof row.stage !== 'string') return [];
      return [{ stage: row.stage, count: Math.max(0, Math.trunc(finiteNumber(row.count))) }];
    }) : [],
    stage_timeseries: normalizeStageTimeSeries(data.stage_timeseries),
    slowest_turns: normalizeSlowTurns(data.slowest_turns),
  };
}

const STAGE_LABELS: Record<string, string> = {
  queue_wait: 'Chờ hàng đợi', stt: 'Nhận dạng STT', translate: 'Dịch NLLB',
  tts_first_chunk: 'TTS chunk đầu', tts_total: 'TTS toàn bộ', end_to_end: 'Toàn trình',
  unknown: 'Không xác định',
};

function formatMs(value: number): string {
  if (!value) return '—';
  return value >= 1000 ? `${(value / 1000).toFixed(2)} s` : `${Math.round(value)} ms`;
}

function LatencyCard({ title, metric, icon, color }: {
  title: string; metric: LatencyPercentile; icon: ReactNode; color: string;
}) {
  const hasData = metric.count > 0 || metric.p50 > 0;
  const withinSlo = hasData && metric.slo_ms > 0 && metric.p90 <= metric.slo_ms;
  return (
    <Card className="overflow-hidden">
      <CardHeader className="p-4 pb-2 flex-row items-start justify-between space-y-0">
        <div>
          <p className="text-sm font-semibold">{title}</p>
          <p className="mt-1 text-[11px] text-text-muted">P50 · P90 · P99</p>
        </div>
        <span className={`rounded-lg p-2 ${color}`}>{icon}</span>
      </CardHeader>
      <CardContent className="p-4 pt-2">
        <div className="flex items-end justify-between gap-2">
          <span className="text-2xl font-bold tracking-tight">{hasData ? formatMs(metric.p50) : '—'}</span>
          {hasData && metric.slo_ms > 0 && (
            <span className={`rounded-full px-2 py-1 text-[10px] font-semibold ${withinSlo ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300' : 'bg-red-500/10 text-red-700 dark:text-red-300'}`}>
              {withinSlo ? 'Đạt SLA' : 'Vượt SLA'}
            </span>
          )}
        </div>
        {hasData ? (
          <>
            <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
              <div><p className="text-text-muted">P90</p><p className="font-semibold">{formatMs(metric.p90)}</p></div>
              <div><p className="text-text-muted">P99</p><p className="font-semibold">{formatMs(metric.p99)}</p></div>
              <div><p className="text-text-muted">Trung bình</p><p className="font-semibold">{formatMs(metric.avg)}</p></div>
            </div>
            <div className="mt-3 flex items-center justify-between border-t border-border pt-2 text-[11px] text-text-muted">
              <span>{metric.count || '—'} mẫu · phủ {metric.availability_pct || 100}%</span>
              <span>{formatMs(metric.min)} – {formatMs(metric.max)}</span>
            </div>
            {metric.slo_ms > 0 && <p className="mt-1 text-[11px] text-text-muted">Ngưỡng {formatMs(metric.slo_ms)} · vi phạm {metric.breach_rate}%</p>}
          </>
        ) : <p className="mt-3 text-xs text-text-muted">Chưa có dữ liệu stage trong phạm vi này.</p>}
      </CardContent>
    </Card>
  );
}

const Analytics = () => {
  const [timeSeries, setTimeSeries] = useState<TimeSeriesMetric[]>([]);
  const [languageData, setLanguageData] = useState<LanguageMetric[]>([]);
  const [pipelineMetrics, setPipelineMetrics] = useState<PipelineMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  // Time range filters
  const [timeRange, setTimeRange] = useState<TimeFilterPreset>('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [customApplied, setCustomApplied] = useState<{ start: string; end: string } | null>(null);
  const [customError, setCustomError] = useState('');

  const [error, setError] = useTimedMessage('');
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const [reload, setReload] = useState(0);

  const applyCustomRange = () => {
    if (!startDate && !endDate) {
      setCustomError('Vui lòng chọn ít nhất một mốc ngày.');
      return;
    }
    if (startDate && endDate && startDate > endDate) {
      setCustomError('Ngày bắt đầu phải trước hoặc bằng ngày kết thúc.');
      return;
    }
    setCustomError('');
    setCustomApplied({ start: startDate, end: endDate });
  };

  useEffect(() => {
    const controller = new AbortController();
    let pending = false;
    const fetchData = async () => {
      if (pending) return;
      pending = true;
      setLoading(true);
      try {
        const params = new URLSearchParams();
        params.set('tz_offset_minutes', String(new Date().getTimezoneOffset()));
        if (timeRange === 'today') {
          const today = getLocalTodayStr();
          params.append('start_date', today);
          params.append('end_date', today);
          params.append('time_range', 'today');
        } else if (timeRange === 'custom') {
          if (customApplied?.start) params.append('start_date', customApplied.start);
          if (customApplied?.end) params.append('end_date', customApplied.end);
        } else {
          params.append('time_range', timeRange);
        }
        const queryString = params.toString() ? `?${params.toString()}` : '';

        const [tsRes, langRes, pipeRes] = await Promise.all([
          api.get(`/metrics/timeseries${queryString}`, { signal: controller.signal }),
          api.get(`/metrics/languages${queryString}`, { signal: controller.signal }),
          api.get(`/metrics/pipeline${queryString}`, { signal: controller.signal })
        ]);
        if (controller.signal.aborted) return;
        setError('');
        setUpdatedAt(new Date());
        setTimeSeries(normalizeTimeSeries(tsRes.data));
        setLanguageData(normalizeLanguages(langRes.data));
        setPipelineMetrics(normalizePipeline(pipeRes.data));
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
  }, [reload, timeRange, customApplied, setError]);

  // Derived metrics summary in the active filter range
  const totalRequests = useMemo(() => timeSeries.reduce((acc, cur) => acc + (cur.requests || 0), 0), [timeSeries]);
  const totalLangRequests = useMemo(() => languageData.reduce((acc, cur) => acc + (cur.value || 0), 0), [languageData]);
  const avgPeriodLatency = useMemo(() => {
    const valid = timeSeries.filter(t => t.requests > 0 && t.avg_latency > 0);
    if (valid.length === 0) return 0;
    const sum = valid.reduce((acc, cur) => acc + cur.avg_latency * cur.requests, 0);
    const total = valid.reduce((acc, cur) => acc + cur.requests, 0);
    return total > 0 ? (sum / total) : 0;
  }, [timeSeries]);

  const rangeLabel = useMemo(() => {
    switch (timeRange) {
      case 'today': return `Hôm nay (${getLocalTodayStr().split('-').reverse().join('/')})`;
      case '7d': return '7 ngày qua';
      case 'week': return 'Tuần này';
      case '30d': return '30 ngày qua';
      case 'month': return 'Tháng này';
      case 'custom':
        if (customApplied?.start && customApplied?.end) {
          const s = customApplied.start.split('-').reverse().join('/');
          const e = customApplied.end.split('-').reverse().join('/');
          return s === e ? `Ngày ${s}` : `Từ ${s} đến ${e}`;
        }
        if (customApplied?.start) return `Từ ${customApplied.start.split('-').reverse().join('/')}`;
        if (customApplied?.end) return `Đến ${customApplied.end.split('-').reverse().join('/')}`;
        return 'Tùy chỉnh khoảng ngày';
      default: return 'Tất cả thời gian';
    }
  }, [timeRange, customApplied]);

  if (!updatedAt) return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">Thống kê nâng cao</h1>
      <p role={error ? 'alert' : 'status'}>{error || (loading ? 'Đang tải số liệu…' : 'Chưa tải được số liệu.')}</p>
      {error && <Button onClick={() => setReload(value => value + 1)}>Thử lại</Button>}
    </div>
  );

  const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
  const stageMetricsAvailable = pipelineMetrics?.stage_metrics_available === true;

  return (
    <div className="space-y-6">
      {/* Title & Filter Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Thống kê nâng cao</h1>
          <p className="text-xs text-text-muted mt-1">Dữ liệu thực tế được lưu trữ vĩnh viễn và đồng bộ liên tục</p>
        </div>

        <Button variant="ghost" size="sm" onClick={() => setReload(v => v + 1)} disabled={loading} className="self-start md:self-auto text-xs">
          <RotateCcw className="w-3.5 h-3.5 mr-1" />
          {loading ? 'Đang cập nhật…' : 'Làm mới'}
        </Button>
      </div>

      {error && (
        <div role="alert" className="rounded-lg bg-amber-500/10 p-3 text-amber-700 flex items-center justify-between">
          <span>{error} Đang hiển thị số liệu lần trước.</span>
          <Button variant="ghost" size="sm" onClick={() => setReload(value => value + 1)}>Thử lại</Button>
        </div>
      )}

      {/* FILTER CONTROLS BAR */}
      <Card className="border border-border/70 shadow-sm">
        <CardContent className="p-4 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-primary" />
              <span className="text-sm font-semibold text-text">Lọc thống kê:</span>
              <div className="flex flex-wrap items-center gap-1 bg-surface p-1 rounded-lg border border-border">
                <button
                  type="button"
                  onClick={() => { setTimeRange('all'); setCustomApplied(null); }}
                  aria-pressed={timeRange === 'all'}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${timeRange === 'all' ? 'bg-primary text-white shadow-sm' : 'text-text-muted hover:text-text'}`}
                >
                  Tất cả
                </button>
                <button
                  type="button"
                  onClick={() => { setTimeRange('today'); setCustomApplied(null); }}
                  aria-pressed={timeRange === 'today'}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${timeRange === 'today' ? 'bg-primary text-white shadow-sm' : 'text-text-muted hover:text-text'}`}
                >
                  Hôm nay
                </button>
                <button
                  type="button"
                  onClick={() => { setTimeRange('7d'); setCustomApplied(null); }}
                  aria-pressed={timeRange === '7d'}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${timeRange === '7d' ? 'bg-primary text-white shadow-sm' : 'text-text-muted hover:text-text'}`}
                >
                  7 ngày qua
                </button>
                <button
                  type="button"
                  onClick={() => { setTimeRange('week'); setCustomApplied(null); }}
                  aria-pressed={timeRange === 'week'}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${timeRange === 'week' ? 'bg-primary text-white shadow-sm' : 'text-text-muted hover:text-text'}`}
                >
                  Tuần này
                </button>
                <button
                  type="button"
                  onClick={() => { setTimeRange('30d'); setCustomApplied(null); }}
                  aria-pressed={timeRange === '30d'}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${timeRange === '30d' ? 'bg-primary text-white shadow-sm' : 'text-text-muted hover:text-text'}`}
                >
                  30 ngày qua
                </button>
                <button
                  type="button"
                  onClick={() => { setTimeRange('month'); setCustomApplied(null); }}
                  aria-pressed={timeRange === 'month'}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${timeRange === 'month' ? 'bg-primary text-white shadow-sm' : 'text-text-muted hover:text-text'}`}
                >
                  Tháng này
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const today = getLocalTodayStr();
                    const s = startDate || today;
                    const e = endDate || today;
                    setStartDate(s);
                    setEndDate(e);
                    setCustomError('');
                    setCustomApplied({ start: s, end: e });
                    setTimeRange('custom');
                  }}
                  aria-pressed={timeRange === 'custom'}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${timeRange === 'custom' ? 'bg-primary text-white shadow-sm' : 'text-text-muted hover:text-text'}`}
                >
                  Tùy chỉnh ngày
                </button>
              </div>
            </div>

            {/* Range summary badge */}
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="bg-primary/10 text-primary font-medium px-2.5 py-1 rounded-md border border-primary/20">
                Phạm vi: {rangeLabel}
              </span>
              <span className="text-text-muted">
                Cập nhật lúc: {updatedAt.toLocaleTimeString('vi-VN')}
                {loading && ' · Đang cập nhật…'}
              </span>
            </div>
          </div>

          {/* CUSTOM DATE PICKER */}
          {timeRange === 'custom' && (
            <div className="flex flex-wrap items-center gap-3 pt-3 border-t border-border">
              <div className="flex items-center gap-2 text-xs text-text-muted">
                <span className="font-medium text-text">Từ ngày:</span>
                <input
                  type="date"
                  value={startDate}
                  aria-invalid={Boolean(customError)}
                  onChange={(e) => {
                    setStartDate(e.target.value);
                    setCustomError('');
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') applyCustomRange();
                  }}
                  className="h-8 rounded-md border border-border bg-background px-2.5 text-xs text-text focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div className="flex items-center gap-2 text-xs text-text-muted">
                <span className="font-medium text-text">Đến ngày:</span>
                <input
                  type="date"
                  value={endDate}
                  aria-invalid={Boolean(customError)}
                  onChange={(e) => {
                    setEndDate(e.target.value);
                    setCustomError('');
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') applyCustomRange();
                  }}
                  className="h-8 rounded-md border border-border bg-background px-2.5 text-xs text-text focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <Button
                size="sm"
                className="h-8 text-xs px-3"
                onClick={applyCustomRange}
                disabled={!startDate && !endDate}
              >
                <Filter className="w-3.5 h-3.5 mr-1" />
                Áp dụng bộ lọc
              </Button>
              <Button
                variant="secondary"
                size="sm"
                className="h-8 text-xs px-2.5"
                onClick={() => {
                  const today = getLocalTodayStr();
                  setStartDate(today);
                  setEndDate(today);
                  setCustomError('');
                  setCustomApplied({ start: today, end: today });
                }}
              >
                Hôm nay ({getLocalTodayStr().split('-').reverse().join('/')})
              </Button>
              {customApplied && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 text-xs text-text-muted hover:text-text"
                  onClick={() => {
                    setStartDate('');
                    setEndDate('');
                    setCustomError('');
                    setCustomApplied(null);
                    setTimeRange('all');
                  }}
                >
                  Đặt lại
                </Button>
              )}
              {customError && <p role="alert" className="w-full text-xs text-red-600 dark:text-red-400">{customError}</p>}
            </div>
          )}

          {/* Quick period summary metrics */}
          <div className="flex flex-wrap items-center gap-3 pt-2 text-xs text-text-muted">
            <span className="inline-flex items-center gap-1.5 bg-background px-3 py-1 rounded-md border border-border">
              <Activity className="w-3.5 h-3.5 text-blue-500" />
              Tổng lượt dịch: <strong className="text-text">{totalRequests}</strong>
            </span>
            <span className="inline-flex items-center gap-1.5 bg-background px-3 py-1 rounded-md border border-border">
              <Zap className="w-3.5 h-3.5 text-amber-500" />
              Độ trễ trung bình: <strong className="text-text">{avgPeriodLatency.toFixed(3)}s</strong>
            </span>
            <span className="inline-flex items-center gap-1.5 bg-background px-3 py-1 rounded-md border border-border">
              <Clock className="w-3.5 h-3.5 text-emerald-500" />
              Số cặp ngôn ngữ: <strong className="text-text">{languageData.length}</strong>
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Real-time & Baseline Pipeline Latency Metrics */}
      {pipelineMetrics && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
            <Card><CardContent className="p-4"><p className="text-xs text-text-muted">Tổng pipeline</p><p className="mt-1 text-2xl font-bold">{pipelineMetrics.total_completed}</p><p className="mt-1 text-[11px] text-text-muted">{pipelineMetrics.active_turns} đang xử lý</p></CardContent></Card>
            <Card><CardContent className="p-4"><p className="text-xs text-text-muted">Tỷ lệ thành công</p><p className="mt-1 text-2xl font-bold text-emerald-600">{pipelineMetrics.success_rate || (pipelineMetrics.total_completed > 0 && pipelineMetrics.total_errors === 0 ? 100 : 0)}%</p><p className="mt-1 text-[11px] text-text-muted">{pipelineMetrics.total_success} lượt thành công</p></CardContent></Card>
            <Card><CardContent className="p-4"><p className="text-xs text-text-muted">Tỷ lệ lỗi</p><p className={`mt-1 text-2xl font-bold ${pipelineMetrics.error_rate > 2 ? 'text-red-600' : ''}`}>{pipelineMetrics.error_rate}%</p><p className="mt-1 text-[11px] text-text-muted">{pipelineMetrics.total_errors} lỗi ghi nhận</p></CardContent></Card>
            <Card><CardContent className="p-4"><p className="text-xs text-text-muted">Thông lượng</p><p className="mt-1 text-2xl font-bold">{(pipelineMetrics.throughput_turns_per_sec * 60).toFixed(1)}</p><p className="mt-1 text-[11px] text-text-muted">lượt/phút</p></CardContent></Card>
            <Card className="col-span-2 lg:col-span-1"><CardContent className="p-4"><p className="text-xs text-text-muted">Nút thắt hiện tại</p><p className="mt-1 text-lg font-bold text-amber-600">{pipelineMetrics.bottleneck ? STAGE_LABELS[pipelineMetrics.bottleneck] : 'Chưa xác định'}</p><p className="mt-1 text-[11px] text-text-muted">Theo độ trễ trung bình</p></CardContent></Card>
          </div>

          {!stageMetricsAvailable && (
            <p role="status" className="rounded-lg border border-blue-500/20 bg-blue-500/10 px-3 py-2 text-xs text-blue-700 dark:text-blue-300">
              Bắt đầu từ phiên bản này, số liệu STT, NLLB và TTS được lưu bền vững. Dữ liệu cũ chỉ có độ trễ toàn trình; hệ thống không suy diễn số liệu riêng cho từng stage.
            </p>
          )}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            <LatencyCard title="Độ trễ toàn trình (P50 / P90 / P99)" metric={pipelineMetrics.latencies_ms.end_to_end} icon={<Gauge className="h-4 w-4" />} color="bg-blue-500/10 text-blue-600" />
            <LatencyCard title="Chờ hàng đợi" metric={pipelineMetrics.latencies_ms.queue_wait} icon={<TimerReset className="h-4 w-4" />} color="bg-cyan-500/10 text-cyan-600" />
            <LatencyCard title="Nhận dạng STT" metric={pipelineMetrics.latencies_ms.stt} icon={<Clock className="h-4 w-4" />} color="bg-emerald-500/10 text-emerald-600" />
            <LatencyCard title="Dịch thuật NLLB" metric={pipelineMetrics.latencies_ms.translate} icon={<Languages className="h-4 w-4" />} color="bg-amber-500/10 text-amber-600" />
            <LatencyCard title="TTS chunk đầu tiên" metric={pipelineMetrics.latencies_ms.tts_first_chunk} icon={<Zap className="h-4 w-4" />} color="bg-purple-500/10 text-purple-600" />
            <LatencyCard title="TTS toàn bộ" metric={pipelineMetrics.latencies_ms.tts_total} icon={<Activity className="h-4 w-4" />} color="bg-pink-500/10 text-pink-600" />
          </div>
        </div>
      )}

      {pipelineMetrics && pipelineMetrics.stage_timeseries.length > 0 && (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
          <Card className="xl:col-span-2">
            <CardHeader>
              <CardTitle>Xu hướng P90 theo từng stage</CardTitle>
              <CardDescription>Phát hiện stage suy giảm theo ngày; đơn vị mili giây</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[320px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={pipelineMetrics.stage_timeseries}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)', borderRadius: '0.5rem' }} />
                    <Legend />
                    <Line type="monotone" dataKey="stt_p90" name="STT P90" stroke="#10b981" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="translate_p90" name="NLLB P90" stroke="#f59e0b" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="tts_first_chunk_p90" name="TTS chunk đầu P90" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="end_to_end_p90" name="Toàn trình P90" stroke="#3b82f6" strokeWidth={2.5} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Sức khỏe vận hành</CardTitle><CardDescription>SLA, lỗi và độ phủ telemetry</CardDescription></CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between rounded-lg bg-emerald-500/10 p-3"><span className="flex items-center gap-2 text-sm"><ShieldCheck className="h-4 w-4 text-emerald-600" />Thành công</span><strong>{pipelineMetrics.total_success}</strong></div>
              <div className="flex items-center justify-between rounded-lg bg-red-500/10 p-3"><span className="flex items-center gap-2 text-sm"><CircleAlert className="h-4 w-4 text-red-600" />Lỗi</span><strong>{pipelineMetrics.total_errors}</strong></div>
              <div className="flex items-center justify-between rounded-lg bg-blue-500/10 p-3"><span className="flex items-center gap-2 text-sm"><Database className="h-4 w-4 text-blue-600" />Độ phủ STT</span><strong>{pipelineMetrics.latencies_ms.stt.availability_pct}%</strong></div>
              {pipelineMetrics.error_breakdown.length > 0 ? pipelineMetrics.error_breakdown.map(item => (
                <div key={item.stage} className="flex items-center justify-between border-t border-border pt-2 text-xs text-text-muted"><span>Lỗi {STAGE_LABELS[item.stage] || item.stage}</span><strong className="text-text">{item.count}</strong></div>
              )) : <p className="text-xs text-text-muted">Không có lỗi trong phạm vi đang chọn.</p>}
            </CardContent>
          </Card>
        </div>
      )}

      {pipelineMetrics && pipelineMetrics.slowest_turns.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Top request chậm nhất</CardTitle><CardDescription>Trace không chứa nội dung hội thoại; dùng để khoanh vùng bottleneck</CardDescription></CardHeader>
          <CardContent>
            <Table>
              <TableHeader><TableRow><TableHead>Thời điểm</TableHead><TableHead>Trace</TableHead><TableHead>Ngôn ngữ</TableHead><TableHead>Bottleneck</TableHead><TableHead className="text-right">STT</TableHead><TableHead className="text-right">NLLB</TableHead><TableHead className="text-right">TTS đầu</TableHead><TableHead className="text-right">Toàn trình</TableHead></TableRow></TableHeader>
              <TableBody>{pipelineMetrics.slowest_turns.map(turn => (
                <TableRow key={turn.turn_id}>
                  <TableCell className="whitespace-nowrap text-xs">{new Date(turn.created_at).toLocaleString('vi-VN')}</TableCell>
                  <TableCell className="font-mono text-xs" title={turn.turn_id}>{turn.turn_id.slice(0, 10)}…</TableCell>
                  <TableCell className="whitespace-nowrap text-xs">{turn.source_lang} → {turn.target_lang}</TableCell>
                  <TableCell><span className="rounded-full bg-amber-500/10 px-2 py-1 text-xs text-amber-700 dark:text-amber-300">{turn.bottleneck ? STAGE_LABELS[turn.bottleneck] : '—'}</span></TableCell>
                  <TableCell className="text-right text-xs">{formatMs(turn.stt_ms)}</TableCell>
                  <TableCell className="text-right text-xs">{formatMs(turn.translate_ms)}</TableCell>
                  <TableCell className="text-right text-xs">{formatMs(turn.tts_first_chunk_ms)}</TableCell>
                  <TableCell className="text-right font-semibold">{formatMs(turn.end_to_end_ms)}</TableCell>
                </TableRow>
              ))}</TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* CHARTS SECTION */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Lưu lượng dịch ({rangeLabel})</CardTitle>
            <CardDescription>Số lượng yêu cầu dịch thuật được xử lý theo ngày</CardDescription>
          </CardHeader>
          <CardContent>
            {timeSeries.length === 1 && (
              <div className="mb-3 px-3 py-1.5 rounded-md bg-blue-500/10 border border-blue-500/20 text-xs flex items-center justify-between">
                <span className="text-blue-600 dark:text-blue-400 font-semibold">
                  Ngày {timeSeries[0].date.split('-').reverse().join('/')}: {timeSeries[0].requests} bản dịch
                </span>
                <span className="text-text-muted">
                  Độ trễ TB: {timeSeries[0].avg_latency}s
                </span>
              </div>
            )}
            {timeSeries.length === 0 ? (
              <div className="h-[300px] flex items-center justify-center text-text-muted text-sm text-center px-4">
                {loading ? "Đang tải dữ liệu..." : "Chưa có dữ liệu bản dịch trong khoảng thời gian này. Vui lòng chọn 'Tất cả' hoặc đổi khoảng ngày."}
              </div>
            ) : (
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={timeSeries}>
                    <defs>
                      <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.35}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text)', borderRadius: '0.5rem' }} 
                    />
                    <Area
                      type="monotone"
                      dataKey="requests"
                      name="Yêu cầu"
                      stroke="#3b82f6"
                      strokeWidth={2.5}
                      fillOpacity={1}
                      fill="url(#colorVolume)"
                      dot={{ r: 5, fill: '#3b82f6', stroke: '#ffffff', strokeWidth: 2 }}
                      activeDot={{ r: 7 }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Độ trễ trung bình (s) ({rangeLabel})</CardTitle>
            <CardDescription>Thời gian phản hồi trung bình của máy chủ theo ngày</CardDescription>
          </CardHeader>
          <CardContent>
            {timeSeries.length === 1 && (
              <div className="mb-3 px-3 py-1.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-xs flex items-center justify-between">
                <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
                  Ngày {timeSeries[0].date.split('-').reverse().join('/')}: {timeSeries[0].avg_latency}s
                </span>
                <span className="text-text-muted">
                  Số yêu cầu: {timeSeries[0].requests}
                </span>
              </div>
            )}
            {timeSeries.length === 0 ? (
              <div className="h-[300px] flex items-center justify-center text-text-muted text-sm text-center px-4">
                {loading ? "Đang tải dữ liệu..." : "Chưa có dữ liệu độ trễ trong khoảng thời gian này."}
              </div>
            ) : (
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={timeSeries} barSize={timeSeries.length === 1 ? 60 : undefined}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text)', borderRadius: '0.5rem' }} 
                      cursor={{fill: 'var(--border)'}}
                    />
                    <Bar dataKey="avg_latency" name="Độ trễ (s)" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Languages className="w-5 h-5 text-primary" />
                  Cặp ngôn ngữ thực tế ({rangeLabel})
                </CardTitle>
                <CardDescription>Tỉ lệ và số lượng các cặp ngôn ngữ đã xử lý trong hệ thống</CardDescription>
              </div>
              {languageData.length > 0 && (
                <span className="text-xs bg-surface px-3 py-1 rounded-md border border-border text-text-muted self-start sm:self-auto font-medium">
                  Tổng cộng: <strong className="text-primary font-bold">{totalLangRequests}</strong> bản dịch
                </span>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {languageData.length === 0 ? (
              <div className="h-[260px] flex items-center justify-center text-text-muted text-sm">
                {loading ? "Đang tải dữ liệu..." : "Chưa có dữ liệu cặp ngôn ngữ nào trong khoảng thời gian này."}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center py-2">
                {/* Donut Chart with Center Total Stat */}
                <div className="md:col-span-5 flex flex-col items-center justify-center">
                  <div className="h-[240px] w-full max-w-[240px] relative flex items-center justify-center">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={languageData}
                          cx="50%"
                          cy="50%"
                          innerRadius={68}
                          outerRadius={96}
                          paddingAngle={languageData.length > 1 ? 4 : 0}
                          dataKey="value"
                          stroke="var(--surface)"
                          strokeWidth={3}
                        >
                          {languageData.map((_, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text)', borderRadius: '0.5rem', fontSize: '12px' }}
                          formatter={(value: any, name: any) => {
                            const val = Number(value) || 0;
                            const pct = totalLangRequests > 0 ? ((val / totalLangRequests) * 100).toFixed(1) : 0;
                            return [`${val} lượt (${pct}%)`, name];
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    {/* Donut Hole Center Stat */}
                    <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none select-none text-center">
                      <span className="text-3xl font-extrabold text-text tracking-tight">
                        {totalLangRequests}
                      </span>
                      <span className="text-[11px] font-medium text-text-muted uppercase tracking-wider">
                        Bản dịch
                      </span>
                    </div>
                  </div>
                  <span className="text-xs text-text-muted mt-2 font-medium">
                    {languageData.length} cặp ngôn ngữ ghi nhận
                  </span>
                </div>

                {/* Detailed Breakdown List with Progress Bars */}
                <div className="md:col-span-7 space-y-3">
                  <div className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
                    Phân bố chi tiết theo cặp ngôn ngữ
                  </div>
                  <div className="space-y-2.5">
                    {languageData.map((item, index) => {
                      const color = COLORS[index % COLORS.length];
                      const pct = totalLangRequests > 0 ? (item.value / totalLangRequests) * 100 : 0;
                      const parts = item.name.split(' -> ');
                      const sourceName = parts[0] || item.name;
                      const targetName = parts[1] || '';

                      return (
                        <div
                          key={index}
                          className="p-3 rounded-lg border border-border/70 bg-surface/50 hover:bg-surface transition-colors space-y-2"
                        >
                          <div className="flex items-center justify-between text-xs">
                            <div className="flex items-center gap-2 font-medium text-text">
                              <span
                                className="w-2.5 h-2.5 rounded-full shrink-0"
                                style={{ backgroundColor: color }}
                              />
                              {targetName ? (
                                <span className="inline-flex items-center gap-1.5">
                                  <span className="px-1.5 py-0.5 rounded bg-background border border-border font-semibold text-[11px]">
                                    {sourceName}
                                  </span>
                                  <ArrowRight className="w-3 h-3 text-text-muted" />
                                  <span className="px-1.5 py-0.5 rounded bg-background border border-border font-semibold text-[11px]">
                                    {targetName}
                                  </span>
                                </span>
                              ) : (
                                <span>{item.name}</span>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-text">
                                {item.value} <span className="font-normal text-text-muted text-[11px]">lượt</span>
                              </span>
                              <span
                                className="px-2 py-0.5 rounded-full text-[11px] font-bold"
                                style={{
                                  backgroundColor: `${color}20`,
                                  color: color,
                                }}
                              >
                                {pct.toFixed(0)}%
                              </span>
                            </div>
                          </div>

                          {/* Progress fill bar */}
                          <div className="w-full bg-border/40 h-2 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-500 ease-out"
                              style={{
                                width: `${pct}%`,
                                backgroundColor: color,
                              }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Analytics;
