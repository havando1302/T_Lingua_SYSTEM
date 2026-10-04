import { useEffect, useState, useMemo } from 'react';
import { useTimedMessage } from '../lib/useTimedMessage';
import api, { apiErrorMessage } from '../lib/api';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { Activity, Gauge, Clock, Zap, Calendar, Filter, RotateCcw, ArrowRight, Languages } from 'lucide-react';

interface LanguageMetric {
  name: string;
  value: number;
}

interface LatencyPercentile {
  p50: number;
  p90: number;
  p99: number;
  avg: number;
}

interface PipelineMetrics {
  active_turns: number;
  total_completed: number;
  total_errors: number;
  throughput_turns_per_sec: number;
  latencies_ms: {
    queue_wait: LatencyPercentile;
    stt: LatencyPercentile;
    translate: LatencyPercentile;
    tts_first_chunk: LatencyPercentile;
    tts_total: LatencyPercentile;
    end_to_end: LatencyPercentile;
  };
}

type TimeFilterPreset = 'all' | 'today' | '7d' | 'week' | '30d' | 'month' | 'custom';

function getLocalTodayStr(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

const Analytics = () => {
  const [timeSeries, setTimeSeries] = useState<any[]>([]);
  const [languageData, setLanguageData] = useState<LanguageMetric[]>([]);
  const [pipelineMetrics, setPipelineMetrics] = useState<PipelineMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  // Time range filters
  const [timeRange, setTimeRange] = useState<TimeFilterPreset>('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [customApplied, setCustomApplied] = useState<{ start: string; end: string } | null>(null);

  const [error, setError] = useTimedMessage('');
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let pending = false;
    const fetchData = async () => {
      if (pending) return;
      pending = true;
      try {
        const params = new URLSearchParams();
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
        setTimeSeries(tsRes.data || []);
        setLanguageData(langRes.data || []);
        setPipelineMetrics(pipeRes.data || null);
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
  }, [reload, timeRange, customApplied]);

  // Derived metrics summary in the active filter range
  const totalRequests = useMemo(() => timeSeries.reduce((acc, cur) => acc + (cur.requests || 0), 0), [timeSeries]);
  const totalLangRequests = useMemo(() => languageData.reduce((acc, cur) => acc + (cur.value || 0), 0), [languageData]);
  const avgPeriodLatency = useMemo(() => {
    const valid = timeSeries.filter(t => t.requests > 0 && t.avg_latency > 0);
    if (valid.length === 0) {
      if (pipelineMetrics?.latencies_ms?.end_to_end?.avg) {
        return pipelineMetrics.latencies_ms.end_to_end.avg / 1000;
      }
      return 0;
    }
    const sum = valid.reduce((acc, cur) => acc + cur.avg_latency * cur.requests, 0);
    const total = valid.reduce((acc, cur) => acc + cur.requests, 0);
    return total > 0 ? (sum / total) : 0;
  }, [timeSeries, pipelineMetrics]);

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

  return (
    <div className="space-y-6">
      {/* Title & Filter Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Thống kê nâng cao</h1>
          <p className="text-xs text-text-muted mt-1">Dữ liệu thực tế được lưu trữ vĩnh viễn và đồng bộ liên tục</p>
        </div>

        <Button variant="ghost" size="sm" onClick={() => setReload(v => v + 1)} className="self-start md:self-auto text-xs">
          <RotateCcw className="w-3.5 h-3.5 mr-1" />
          Làm mới
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
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${timeRange === 'all' ? 'bg-primary text-white shadow-sm' : 'text-text-muted hover:text-text'}`}
                >
                  Tất cả
                </button>
                <button
                  type="button"
                  onClick={() => { setTimeRange('today'); setCustomApplied(null); }}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${timeRange === 'today' ? 'bg-primary text-white shadow-sm' : 'text-text-muted hover:text-text'}`}
                >
                  Hôm nay
                </button>
                <button
                  type="button"
                  onClick={() => { setTimeRange('7d'); setCustomApplied(null); }}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${timeRange === '7d' ? 'bg-primary text-white shadow-sm' : 'text-text-muted hover:text-text'}`}
                >
                  7 ngày qua
                </button>
                <button
                  type="button"
                  onClick={() => { setTimeRange('week'); setCustomApplied(null); }}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${timeRange === 'week' ? 'bg-primary text-white shadow-sm' : 'text-text-muted hover:text-text'}`}
                >
                  Tuần này
                </button>
                <button
                  type="button"
                  onClick={() => { setTimeRange('30d'); setCustomApplied(null); }}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${timeRange === '30d' ? 'bg-primary text-white shadow-sm' : 'text-text-muted hover:text-text'}`}
                >
                  30 ngày qua
                </button>
                <button
                  type="button"
                  onClick={() => { setTimeRange('month'); setCustomApplied(null); }}
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
                    setCustomApplied({ start: s, end: e });
                    setTimeRange('custom');
                  }}
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
                  onChange={(e) => {
                    const val = e.target.value;
                    setStartDate(val);
                    if (val && endDate) {
                      setCustomApplied({ start: val, end: endDate });
                    }
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') setCustomApplied({ start: startDate, end: endDate });
                  }}
                  className="h-8 rounded-md border border-border bg-background px-2.5 text-xs text-text focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div className="flex items-center gap-2 text-xs text-text-muted">
                <span className="font-medium text-text">Đến ngày:</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => {
                    const val = e.target.value;
                    setEndDate(val);
                    if (startDate && val) {
                      setCustomApplied({ start: startDate, end: val });
                    }
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') setCustomApplied({ start: startDate, end: endDate });
                  }}
                  className="h-8 rounded-md border border-border bg-background px-2.5 text-xs text-text focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <Button
                size="sm"
                className="h-8 text-xs px-3"
                onClick={() => setCustomApplied({ start: startDate, end: endDate })}
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
                    setCustomApplied(null);
                  }}
                >
                  Đặt lại
                </Button>
              )}
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
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="py-3 px-4 flex flex-row items-center justify-between">
              <span className="text-sm font-medium text-text-muted">Độ trễ toàn trình (P50 / P90 / P99)</span>
              <Gauge className="w-4 h-4 text-blue-500" />
            </CardHeader>
            <CardContent className="py-2 px-4">
              <div className="text-2xl font-bold">
                {pipelineMetrics.latencies_ms.end_to_end.p50} ms
              </div>
              <p className="text-xs text-text-muted mt-1">
                P90: {pipelineMetrics.latencies_ms.end_to_end.p90} ms | P99: {pipelineMetrics.latencies_ms.end_to_end.p99} ms
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="py-3 px-4 flex flex-row items-center justify-between">
              <span className="text-sm font-medium text-text-muted">Độ trễ nhận dạng STT</span>
              <Clock className="w-4 h-4 text-emerald-500" />
            </CardHeader>
            <CardContent className="py-2 px-4">
              <div className="text-2xl font-bold">
                {pipelineMetrics.latencies_ms.stt.p50} ms
              </div>
              <p className="text-xs text-text-muted mt-1">
                P90: {pipelineMetrics.latencies_ms.stt.p90} ms | TB: {pipelineMetrics.latencies_ms.stt.avg} ms
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="py-3 px-4 flex flex-row items-center justify-between">
              <span className="text-sm font-medium text-text-muted">Độ trễ dịch thuật NLLB</span>
              <Zap className="w-4 h-4 text-amber-500" />
            </CardHeader>
            <CardContent className="py-2 px-4">
              <div className="text-2xl font-bold">
                {pipelineMetrics.latencies_ms.translate.p50} ms
              </div>
              <p className="text-xs text-text-muted mt-1">
                P90: {pipelineMetrics.latencies_ms.translate.p90} ms | TB: {pipelineMetrics.latencies_ms.translate.avg} ms
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="py-3 px-4 flex flex-row items-center justify-between">
              <span className="text-sm font-medium text-text-muted">TTS Chunk đầu tiên</span>
              <Activity className="w-4 h-4 text-purple-500" />
            </CardHeader>
            <CardContent className="py-2 px-4">
              <div className="text-2xl font-bold">
                {pipelineMetrics.latencies_ms.tts_first_chunk.p50} ms
              </div>
              <p className="text-xs text-text-muted mt-1">
                Tổng lượt hoàn thành: {pipelineMetrics.total_completed}
              </p>
            </CardContent>
          </Card>
        </div>
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
