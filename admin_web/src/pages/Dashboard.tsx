import { useEffect, useState } from 'react';
import { useTimedMessage } from '../lib/useTimedMessage';
import api, { apiErrorMessage } from '../lib/api';
import { Button } from '../components/ui/Button';
import { Activity, Users, Zap, AlertCircle, HardDrive, Cpu, MemoryStick } from 'lucide-react';
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
  inference_runtime: {
    device?: string;
    whisper_device?: string;
    whisper_model_id?: string;
    whisper_compute_type?: string;
    whisper_cpu_fallback?: boolean;
    model_load_seconds?: number;
  } | null;
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
  const optionalText = (field: unknown) => typeof field === 'string' && field.trim() ? field : undefined;
  return {
    cpu_usage: Math.min(100, Math.max(0, finiteNumber(data.cpu_usage))),
    ram_usage: Math.min(100, Math.max(0, finiteNumber(data.ram_usage))),
    ram_total: Math.max(0, finiteNumber(data.ram_total)),
    disk_usage: Math.min(100, Math.max(0, finiteNumber(data.disk_usage))),
    disk_total: Math.max(0, finiteNumber(data.disk_total)),
    inference_runtime: runtime ? {
      device: optionalText(runtime.device),
      whisper_device: optionalText(runtime.whisper_device),
      whisper_model_id: optionalText(runtime.whisper_model_id),
      whisper_compute_type: optionalText(runtime.whisper_compute_type),
      whisper_cpu_fallback: runtime.whisper_cpu_fallback === true,
      model_load_seconds: Math.max(0, finiteNumber(runtime.model_load_seconds)),
    } : null,
  };
}

const Dashboard = () => {
  const user = useAuthUser();
  const canViewSystemStatus = user?.role !== 'employee';
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    total_translations: 0,
    flagged_translations: 0,
    avg_latency: 0.0,
    unique_clients: 0,
    started_at: '',
    sample_limit: 1000
  });

  const [sysStatus, setSysStatus] = useState<SystemStatus>({
    cpu_usage: 0,
    ram_usage: 0,
    ram_total: 0,
    disk_usage: 0,
    disk_total: 0,
    inference_runtime: null
  });

  const [timeSeries, setTimeSeries] = useState<TimeSeriesMetric[]>([]);
  const [timeRange, setTimeRange] = useState<'all' | 'today'>('all');
  const [loading, setLoading] = useState(true);

  const [error, setError] = useTimedMessage('');
  const [systemError, setSystemError] = useState('');
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
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
        setUpdatedAt(new Date());
        setMetrics(normalizeDashboardMetrics(metricsResult.value.data));
        setTimeSeries(normalizeTimeSeries(seriesResult.value.data));
        if (systemResult.status === 'fulfilled' && systemResult.value) {
          setSysStatus(normalizeSystemStatus(systemResult.value.data));
          setSystemError('');
        } else if (systemResult.status === 'rejected') {
          setSystemError(apiErrorMessage(systemResult.reason));
        }
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
            {sysStatus.inference_runtime && <p className="text-sm text-text-muted">
              Nhận dạng giọng nói: {sysStatus.inference_runtime.whisper_model_id || 'Chưa xác định'} · {sysStatus.inference_runtime.whisper_device || sysStatus.inference_runtime.device || 'Chưa xác định'} · {sysStatus.inference_runtime.whisper_compute_type || ''}
              {sysStatus.inference_runtime.whisper_cpu_fallback && ' · Đang dùng CPU dự phòng'}
            </p>}
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
    </div>
  );
};

export default Dashboard;
