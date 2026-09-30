import { useEffect, useState } from 'react';
import api, { apiErrorMessage } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Filter, RotateCcw, Rocket, Save } from 'lucide-react';

interface Setting { id: number; key: string; value: string; description: string; }
interface AuditEntry { id: number; actor_username: string; action: string; resource_type: string; resource_id?: string; created_at: string; }
interface ModelDeployment { component: string; active_model: string; canary_model?: string; canary_percent: number; previous_active_model?: string; version: number; requires_runtime_reload: boolean; }
const settingLabels: Record<string, string> = { max_chars_per_request: 'Số ký tự tối đa mỗi yêu cầu', rate_limit_rpm: 'Số yêu cầu tối đa mỗi phút', enable_cache: 'Dùng bộ nhớ đệm' };

const Settings = () => {
  const [settings, setSettings] = useState<Setting[]>([]);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [models, setModels] = useState<ModelDeployment[]>([]);
  const [modelDrafts, setModelDrafts] = useState<Record<string, { model_id: string; percent: string }>>({});
  const [modelSaving, setModelSaving] = useState<string | null>(null);
  const [auditFilters, setAuditFilters] = useState({ actor: '', action: '', resource_type: '', created_from: '', created_to: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [messages, setMessages] = useState<Record<string, string>>({});

  const fetchSettings = async () => {
    setLoading(true);
    setError('');
    try {
      const settingsResponse = await api.get('/settings');
      setSettings(settingsResponse.data);
      const [auditResponse, modelResponse] = await Promise.all([
        api.get('/audit?limit=20'), api.get('/models/deployments'),
      ]);
      setAudit(auditResponse.data);
      setModels(modelResponse.data);
      setModelDrafts(Object.fromEntries(modelResponse.data.map((model: ModelDeployment) => [
        model.component, { model_id: model.canary_model ?? '', percent: String(model.canary_percent || 10) },
      ])));
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleChange = (key: string, value: string) => {
    setSettings(prev => prev.map(s => s.key === key ? { ...s, value } : s));
    setMessages(previous => ({ ...previous, [key]: 'Có thay đổi chưa lưu.' }));
  };

  const handleSave = async (key: string, value: string) => {
    if (saving) return;
    const maximum = key === 'max_chars_per_request' ? 5000 : 60;
    if (key !== 'enable_cache' && (!/^\d+$/.test(value.trim()) || Number(value) < 1 || Number(value) > maximum)) {
      setError(`${settingLabels[key] ?? key}: nhập số nguyên từ 1 đến ${maximum}.`);
      return;
    }
    setError('');
    setSaving(key);
    try {
      const response = await api.put<Setting>(`/settings/${key}`, { value });
      setSettings(previous => previous.map(setting => setting.key === key ? response.data : setting));
      setMessages(previous => ({ ...previous, [key]: 'Đã lưu thành công.' }));
    } catch (err) {
      setError(apiErrorMessage(err, 'Có lỗi khi lưu cài đặt'));
    } finally {
      setSaving(null);
    }
  };

  const loadAudit = async () => {
    setError('');
    try {
      const params = Object.fromEntries(Object.entries(auditFilters).filter(([, value]) => value));
      const response = await api.get('/audit', { params: { ...params, limit: 100 } });
      setAudit(response.data);
    } catch (err) { setError(apiErrorMessage(err, 'Không thể lọc nhật ký.')); }
  };

  const updateModel = async (component: string, operation: 'canary' | 'promote' | 'rollback') => {
    if (modelSaving) return;
    const draft = modelDrafts[component] ?? { model_id: '', percent: '10' };
    if (operation === 'canary' && (!draft.model_id.trim() || Number(draft.percent) < 1 || Number(draft.percent) > 50)) {
      setError('Model canary phải có mã hợp lệ và tỷ lệ từ 1 đến 50%.'); return;
    }
    setModelSaving(component); setError('');
    try {
      const response = operation === 'canary'
        ? await api.put(`/models/${component}/canary`, { model_id: draft.model_id.trim(), percent: Number(draft.percent) })
        : await api.post(`/models/${component}/${operation}`);
      setModels(previous => previous.map(model => model.component === component ? response.data : model));
      setModelDrafts(previous => ({ ...previous, [component]: { model_id: response.data.canary_model ?? '', percent: String(response.data.canary_percent || 10) } }));
      await loadAudit();
    } catch (err) { setError(apiErrorMessage(err, 'Không thể cập nhật cấu hình model.')); }
    finally { setModelSaving(null); }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Cài đặt Hệ thống</h1>
        <p className="text-text-muted mt-2">Định cấu hình các quy tắc và tính năng cốt lõi của công cụ Dịch thuật AI.</p>
      </div>

      {error && <div role="alert" className="text-red-600">{error} {settings.length === 0 && <Button variant="ghost" onClick={fetchSettings}>Thử lại</Button>}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {loading ? (
          <p className="text-text-muted">Đang tải cấu hình...</p>
        ) : (
          settings.map((setting) => (
            <Card key={setting.id}>
              <CardHeader>
                <CardTitle className="text-lg">{settingLabels[setting.key] ?? setting.key}</CardTitle>
                <CardDescription>{setting.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap items-end gap-4">
                  {setting.key === 'enable_cache' ? <label className="flex-1 text-sm">Dùng bộ nhớ đệm
                    <select className="mt-1 block w-full rounded border border-border bg-surface p-2" value={setting.value} disabled={saving !== null} onChange={(event) => handleChange(setting.key, event.target.value)}>
                      <option value="true">Bật</option><option value="false">Tắt</option>
                    </select>
                  </label> : <Input
                    label={settingLabels[setting.key] ?? setting.key}
                    type="number" min={1} max={setting.key === 'max_chars_per_request' ? 5000 : 60} step={1}
                    disabled={saving !== null}
                    value={setting.value}
                    onChange={(e) => handleChange(setting.key, e.target.value)}
                  />}
                  <Button 
                    onClick={() => handleSave(setting.key, setting.value)}
                    isLoading={saving === setting.key}
                    disabled={saving !== null}
                  >
                    <Save size={18} className="mr-2" />
                    Lưu lại
                  </Button>
                </div>
                <p role="status" className="mt-2 text-sm text-text-muted">{messages[setting.key]}</p>
              </CardContent>
            </Card>
          ))
        )}
      </div>
      <Card>
        <CardHeader><CardTitle>Triển khai model</CardTitle><CardDescription>Cấu hình active/canary có phiên bản và rollback. Thay đổi chỉ có hiệu lực sau quy trình reload runtime có kiểm soát.</CardDescription></CardHeader>
        <CardContent className="space-y-4">
          {models.map(model => <div key={model.component} className="rounded border border-border p-3">
            <div className="mb-2 text-sm"><strong>{model.component.toUpperCase()}</strong> · v{model.version}<br /><span className="text-text-muted">Active: {model.active_model}</span>{model.previous_active_model && <><br /><span className="text-text-muted">Bản trước: {model.previous_active_model}</span></>}</div>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
              <Input label={`Model canary ${model.component}`} value={modelDrafts[model.component]?.model_id ?? ''} onChange={event => setModelDrafts(previous => ({ ...previous, [model.component]: { ...(previous[model.component] ?? { percent: '10' }), model_id: event.target.value } }))} disabled={modelSaving !== null} />
              <Input label="Tỷ lệ canary (%)" type="number" min={1} max={50} value={modelDrafts[model.component]?.percent ?? '10'} onChange={event => setModelDrafts(previous => ({ ...previous, [model.component]: { ...(previous[model.component] ?? { model_id: '' }), percent: event.target.value } }))} disabled={modelSaving !== null} />
              <Button size="sm" onClick={() => updateModel(model.component, 'canary')} isLoading={modelSaving === model.component}><Save size={16} className="mr-1" />Lưu canary</Button>
              <Button size="sm" variant="secondary" onClick={() => updateModel(model.component, 'promote')} disabled={!model.canary_model || modelSaving !== null}><Rocket size={16} className="mr-1" />Promote</Button>
              <Button size="sm" variant="ghost" onClick={() => updateModel(model.component, 'rollback')} disabled={!model.previous_active_model || modelSaving !== null}><RotateCcw size={16} className="mr-1" />Rollback</Button>
            </div>
          </div>)}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>Nhật ký quản trị gần nhất</CardTitle><CardDescription>Ghi nhận hành động quản trị, không lưu secret hoặc nội dung hội thoại.</CardDescription></CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-6 gap-2 mb-4 items-end">
            <Input label="Người thực hiện" value={auditFilters.actor} onChange={event => setAuditFilters(previous => ({ ...previous, actor: event.target.value }))} />
            <Input label="Hành động" value={auditFilters.action} onChange={event => setAuditFilters(previous => ({ ...previous, action: event.target.value }))} />
            <Input label="Loại đối tượng" value={auditFilters.resource_type} onChange={event => setAuditFilters(previous => ({ ...previous, resource_type: event.target.value }))} />
            <Input label="Từ thời điểm" type="datetime-local" value={auditFilters.created_from} onChange={event => setAuditFilters(previous => ({ ...previous, created_from: event.target.value }))} />
            <Input label="Đến thời điểm" type="datetime-local" value={auditFilters.created_to} onChange={event => setAuditFilters(previous => ({ ...previous, created_to: event.target.value }))} />
            <Button size="sm" onClick={loadAudit}><Filter size={16} className="mr-1" />Lọc</Button>
          </div>
          <Table><TableHeader><TableRow><TableHead>Thời gian</TableHead><TableHead>Người thực hiện</TableHead><TableHead>Hành động</TableHead><TableHead>Đối tượng</TableHead></TableRow></TableHeader>
            <TableBody>{audit.length === 0 ? <TableRow><TableCell colSpan={4} className="text-center text-text-muted">Chưa có sự kiện audit.</TableCell></TableRow> : audit.map(entry => <TableRow key={entry.id}>
              <TableCell>{new Date(entry.created_at).toLocaleString('vi-VN')}</TableCell><TableCell>{entry.actor_username}</TableCell><TableCell>{entry.action}</TableCell><TableCell>{entry.resource_type}{entry.resource_id ? ` #${entry.resource_id}` : ''}</TableCell>
            </TableRow>)}</TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default Settings;
