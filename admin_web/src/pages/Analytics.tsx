import { useEffect, useState } from 'react';
import api, { apiErrorMessage } from '../lib/api';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { Activity, Gauge, Clock, Zap } from 'lucide-react';

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

const Analytics = () => {
  const [timeSeries, setTimeSeries] = useState<any[]>([]);
  const [languageData, setLanguageData] = useState<LanguageMetric[]>([]);
  const [pipelineMetrics, setPipelineMetrics] = useState<PipelineMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  const [error, setError] = useState('');
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let pending = false;
    const fetchData = async () => {
      if (pending) return;
      pending = true;
      try {
        const [tsRes, langRes, pipeRes] = await Promise.all([
          api.get('/metrics/timeseries', { signal: controller.signal }),
          api.get('/metrics/languages', { signal: controller.signal }),
          api.get('/metrics/pipeline', { signal: controller.signal })
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
  }, [reload]);

  if (!updatedAt) return <div className="space-y-4">
    <h1 className="text-3xl font-bold">Thống kê nâng cao</h1>
    <p role={error ? 'alert' : 'status'}>{error || (loading ? 'Đang tải số liệu…' : 'Chưa tải được số liệu.')}</p>
    {error && <Button onClick={() => setReload(value => value + 1)}>Thử lại</Button>}
  </div>;

  const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Thống kê nâng cao</h1>
      </div>
      <p className="text-xs text-text-muted">Cập nhật: {updatedAt.toLocaleTimeString('vi-VN')}</p>
      {error && <div role="alert" className="rounded-lg bg-amber-500/10 p-3 text-amber-700">{error} Đang hiển thị số liệu lần trước.
        <Button variant="ghost" onClick={() => setReload(value => value + 1)}>Thử lại</Button>
      </div>}
      {/* Real-time Pipeline Latency Metrics (Phase 5) */}
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
                Thông lượng: {pipelineMetrics.throughput_turns_per_sec} lượt/s
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Lưu lượng dịch (7 ngày qua)</CardTitle>
            <CardDescription>Số lượng yêu cầu dịch thuật được xử lý mỗi ngày</CardDescription>
          </CardHeader>
          <CardContent>
            {timeSeries.length === 0 ? (
              <div className="h-[300px] flex items-center justify-center text-text-muted">
                {loading ? "Đang tải dữ liệu..." : "Chưa có dữ liệu lưu lượng trong phiên máy chủ này"}
              </div>
            ) : (
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={timeSeries}>
                    <defs>
                      <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text)', borderRadius: '0.5rem' }} 
                    />
                    <Area type="monotone" dataKey="requests" name="Yêu cầu" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorVolume)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Độ trễ trung bình (s)</CardTitle>
            <CardDescription>Thời gian phản hồi trung bình của máy chủ theo ngày</CardDescription>
          </CardHeader>
          <CardContent>
            {timeSeries.length === 0 ? (
              <div className="h-[300px] flex items-center justify-center text-text-muted">
                {loading ? "Đang tải dữ liệu..." : "Chưa có dữ liệu độ trễ trong 7 ngày qua"}
              </div>
            ) : (
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={timeSeries}>
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
            <CardTitle>Cặp ngôn ngữ thực tế</CardTitle>
            <CardDescription>Tỉ lệ cặp ngôn ngữ đã xử lý từ lần khởi động máy chủ</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            {languageData.length === 0 ? (
              <div className="h-[260px] flex items-center justify-center text-text-muted">
                {loading ? "Đang tải dữ liệu..." : "Chưa có dữ liệu cặp ngôn ngữ nào được ghi nhận"}
              </div>
            ) : (
              <div className="h-[300px] w-full max-w-md">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={languageData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      fill="#8884d8"
                      paddingAngle={5}
                      dataKey="value"
                      label={({ name, percent }: any) => `${name} (${(((percent as number) || 0) * 100).toFixed(0)}%)`}
                    >
                      {languageData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text)', borderRadius: '0.5rem' }} 
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Analytics;
