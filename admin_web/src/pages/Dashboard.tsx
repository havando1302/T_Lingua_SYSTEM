import { useEffect, useState } from 'react';
import api, { apiErrorMessage } from '../lib/api';
import { Button } from '../components/ui/Button';
import { Activity, Users, Zap, AlertCircle, HardDrive, Cpu, MemoryStick } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';

const Dashboard = () => {
  const [metrics, setMetrics] = useState({
    total_translations: 0,
    flagged_translations: 0,
    avg_latency: 0.0,
    unique_clients: 0,
    started_at: '',
    sample_limit: 1000
  });

  const [sysStatus, setSysStatus] = useState({
    cpu_usage: 0,
    ram_usage: 0,
    ram_total: 0,
    disk_usage: 0,
    disk_total: 0,
    inference_runtime: null as { device?: string; whisper_device?: string; whisper_model_id?: string; whisper_compute_type?: string; whisper_cpu_fallback?: boolean; model_load_seconds?: number } | null
  });

  const [timeSeries, setTimeSeries] = useState<any[]>([]);
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
        const [metricsRes, sysRes, tsRes] = await Promise.all([
          api.get('/metrics/dashboard', { signal: controller.signal }),
          api.get('/system/status', { signal: controller.signal }),
          api.get('/metrics/timeseries', { signal: controller.signal })
        ]);
        if (controller.signal.aborted) return;
        setError('');
        setUpdatedAt(new Date());
        setMetrics(metricsRes.data);
        setSysStatus(sysRes.data);
        setTimeSeries(tsRes.data);
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
    <h1 className="text-3xl font-bold">Bảng điều khiển</h1>
    <p role={error ? 'alert' : 'status'}>{error || (loading ? 'Đang tải số liệu…' : 'Chưa tải được số liệu.')}</p>
    {error && <Button onClick={() => setReload(value => value + 1)}>Thử lại</Button>}
  </div>;

  const statCards = [
    { title: 'Tổng lượt dịch', value: metrics.total_translations, icon: Activity, color: 'text-blue-500', bg: 'bg-blue-500/10' },
    { title: 'Khách trong mẫu gần đây', value: metrics.unique_clients, icon: Users, color: 'text-green-500', bg: 'bg-green-500/10' },
    { title: 'Độ trễ TB mẫu gần đây (s)', value: metrics.avg_latency.toFixed(3), icon: Zap, color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
    { title: 'Bản dịch đang bị báo lỗi', value: metrics.flagged_translations, icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-500/10' },
  ];

  const sysCards = [
    { title: 'Sử dụng CPU', value: `${sysStatus.cpu_usage}%`, icon: Cpu },
    { title: 'Sử dụng RAM', value: `${sysStatus.ram_usage}% (${sysStatus.ram_total}GB)`, icon: MemoryStick },
    { title: 'Sử dụng Ổ cứng', value: `${sysStatus.disk_usage}% (${sysStatus.disk_total}GB)`, icon: HardDrive },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Bảng điều khiển</h1>
      </div>
      <p className="text-xs text-text-muted">Cập nhật: {updatedAt.toLocaleTimeString('vi-VN')}</p>
      {error && <div role="alert" className="rounded-lg bg-amber-500/10 p-3 text-amber-700">{error} Đang hiển thị số liệu lần trước.
        <Button variant="ghost" onClick={() => setReload(value => value + 1)}>Thử lại</Button>
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Lưu lượng dịch (7 ngày qua)</CardTitle>
            <CardDescription>Số lượng yêu cầu dịch thuật được xử lý bởi AI mỗi ngày.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full mt-4">
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
                  <Area type="monotone" dataKey="requests" name="Yêu cầu" stroke="var(--primary)" strokeWidth={2} fillOpacity={1} fill="url(#colorReq)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
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
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
