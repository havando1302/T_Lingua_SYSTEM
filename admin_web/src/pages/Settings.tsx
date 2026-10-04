import { useEffect, useState } from 'react';
import { useTimedMessage } from '../lib/useTimedMessage';
import { Link } from 'react-router-dom';
import api, { apiErrorMessage } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import {
  Save,
  RotateCcw,
  Rocket,
  Filter,
  CheckCircle2,
  Sliders,
  Cpu,
  History,
  Type,
  Zap,
  Database,
  ShieldCheck,
  RefreshCw,
  AlertCircle,
  X,
  Ban,
  Sparkles,
  ExternalLink,
} from 'lucide-react';

interface Setting {
  id: number;
  key: string;
  value: string;
  description: string;
}

interface AuditEntry {
  id: number;
  actor_username: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  created_at: string;
}

interface ModelDeployment {
  component: string;
  active_model: string;
  canary_model?: string;
  canary_percent: number;
  previous_active_model?: string;
  version: number;
  requires_runtime_reload: boolean;
}

interface ModelArtifact {
  id: string;
  component: string;
  version: string;
  storage_uri: string;
  status: string;
  base_model?: string;
}

const SETTING_METADATA: Record<
  string,
  { label: string; icon: typeof Type; unit?: string; max: number; tip: string }
> = {
  max_chars_per_request: {
    label: 'Số ký tự tối đa mỗi yêu cầu',
    icon: Type,
    unit: 'ký tự',
    max: 5000,
    tip: 'Độ dài tối đa cho mỗi đoạn văn bản người dùng gửi dịch một lần.',
  },
  rate_limit_rpm: {
    label: 'Giới hạn tốc độ gọi API',
    icon: Zap,
    unit: 'req/phút',
    max: 60,
    tip: 'Tần suất gửi yêu cầu tối đa cho phép trong mỗi phút để tránh quá tải server.',
  },
  enable_cache: {
    label: 'Bộ nhớ đệm dịch thuật (Cache)',
    icon: Database,
    max: 1,
    tip: 'Tự động lưu và tái sử dụng kết quả dịch các câu lặp lại để giảm tải cho GPU.',
  },
};

const Settings = () => {
  const [settings, setSettings] = useState<Setting[]>([]);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [models, setModels] = useState<ModelDeployment[]>([]);
  const [artifacts, setArtifacts] = useState<ModelArtifact[]>([]);
  const [modelDrafts, setModelDrafts] = useState<Record<string, { model_id: string; percent: string }>>({});
  const [modelSaving, setModelSaving] = useState<string | null>(null);
  const [auditFilters, setAuditFilters] = useState({
    actor: '',
    action: '',
    resource_type: '',
    created_from: '',
    created_to: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useTimedMessage('');
  const [messages, setMessages] = useState<Record<string, string>>({});

  const fetchSettings = async () => {
    setLoading(true);
    setError('');
    try {
      const settingsResponse = await api.get('/settings');
      setSettings(settingsResponse.data);
      const [auditResponse, modelResponse, artifactsResponse] = await Promise.all([
        api.get('/audit?limit=25'),
        api.get('/models/deployments'),
        api.get('/training/models').catch(() => ({ data: [] })),
      ]);
      setAudit(auditResponse.data);
      setModels(modelResponse.data);
      setArtifacts(artifactsResponse.data ?? []);
      setModelDrafts(
        Object.fromEntries(
          modelResponse.data.map((model: ModelDeployment) => [
            model.component,
            { model_id: model.canary_model ?? '', percent: String(model.canary_percent || 10) },
          ])
        )
      );
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
    setSettings((prev) => prev.map((s) => (s.key === key ? { ...s, value } : s)));
    setMessages((previous) => ({ ...previous, [key]: 'Có thay đổi chưa lưu' }));
  };

  const handleSave = async (key: string, value: string) => {
    if (saving) return;
    const meta = SETTING_METADATA[key];
    const maximum = meta?.max ?? (key === 'max_chars_per_request' ? 5000 : 60);

    if (key !== 'enable_cache' && (!/^\d+$/.test(value.trim()) || Number(value) < 1 || Number(value) > maximum)) {
      setError(`${meta?.label ?? key}: Vui lòng nhập số nguyên từ 1 đến ${maximum}.`);
      return;
    }
    setError('');
    setSaving(key);
    try {
      const response = await api.put<Setting>(`/settings/${key}`, { value });
      setSettings((previous) => previous.map((setting) => (setting.key === key ? response.data : setting)));
      setMessages((previous) => ({ ...previous, [key]: 'Đã lưu thành công' }));
      setTimeout(() => {
        setMessages((previous) => {
          if (previous[key] === 'Đã lưu thành công') {
            const next = { ...previous };
            delete next[key];
            return next;
          }
          return previous;
        });
      }, 3500);
    } catch (err) {
      setError(apiErrorMessage(err, 'Có lỗi khi lưu cài đặt'));
    } finally {
      setSaving(null);
    }
  };

  const handleSaveAll = async () => {
    const unsavedKeys = Object.entries(messages)
      .filter(([, msg]) => msg === 'Có thay đổi chưa lưu')
      .map(([k]) => k);
    for (const key of unsavedKeys) {
      const setting = settings.find((s) => s.key === key);
      if (setting) {
        await handleSave(setting.key, setting.value);
      }
    }
  };

  const loadAudit = async () => {
    setError('');
    try {
      const params = Object.fromEntries(Object.entries(auditFilters).filter(([, value]) => value));
      const response = await api.get('/audit', { params: { ...params, limit: 100 } });
      setAudit(response.data);
    } catch (err) {
      setError(apiErrorMessage(err, 'Không thể lọc nhật ký.'));
    }
  };

  const resetAuditFilters = () => {
    setAuditFilters({ actor: '', action: '', resource_type: '', created_from: '', created_to: '' });
    api.get('/audit?limit=25').then((res) => setAudit(res.data)).catch(() => {});
  };

  const updateModel = async (component: string, operation: 'canary' | 'promote' | 'rollback' | 'disable') => {
    if (modelSaving) return;
    let op = operation;
    const draft = modelDrafts[component] ?? { model_id: '', percent: '10' };
    if (op === 'canary' && (!draft.model_id.trim() || Number(draft.percent) === 0)) {
      op = 'disable';
    } else if (op === 'canary' && (Number(draft.percent) < 1 || Number(draft.percent) > 50)) {
      setError('Model canary phải có mã định danh hợp lệ và tỷ lệ lưu lượng từ 1% đến 50%.');
      return;
    }
    if (op === 'disable' && !confirm(`Bạn có chắc muốn hủy bỏ chia lưu lượng Canary của ${component.toUpperCase()} và chuyển 100% lưu lượng về model Active?`)) {
      return;
    }
    if (op === 'promote' && !confirm(`Bạn có chắc muốn quảng bá model canary của ${component.toUpperCase()} lên làm bản chính thức (Active)?`)) {
      return;
    }
    if (op === 'rollback' && !confirm(`Bạn có chắc muốn rollback ${component.toUpperCase()} về phiên bản trước?`)) {
      return;
    }

    setModelSaving(component);
    setError('');
    try {
      const response =
        op === 'canary'
          ? await api.put(`/models/${component}/canary`, { model_id: draft.model_id.trim(), percent: Number(draft.percent) })
          : op === 'disable'
          ? await api.delete(`/models/${component}/canary`)
          : await api.post(`/models/${component}/${op}`);

      setModels((previous) => previous.map((model) => (model.component === component ? response.data : model)));
      setModelDrafts((previous) => ({
        ...previous,
        [component]: {
          model_id: response.data.canary_model ?? '',
          percent: String(response.data.canary_percent || 10),
        },
      }));
      await loadAudit();
    } catch (err) {
      setError(apiErrorMessage(err, 'Không thể cập nhật cấu hình model.'));
    } finally {
      setModelSaving(null);
    }
  };

  const hasUnsaved = Object.values(messages).some((msg) => msg === 'Có thay đổi chưa lưu');

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-border/60 pb-5">
        <div>
          <div className="flex items-center gap-2 text-primary font-semibold mb-1">
            <Sliders size={20} />
            <span className="text-xs uppercase tracking-wider">Hệ thống & Vận hành</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text">Cài đặt Hệ thống</h1>
          <p className="text-text-muted mt-1 text-sm">
            Quản lý tham số dịch thuật, cơ chế lưu cache, triển khai model canary và kiểm tra nhật ký bảo mật.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {hasUnsaved && (
            <Button onClick={handleSaveAll} className="shadow-md shadow-primary/20">
              <Save size={16} className="mr-2" />
              Lưu tất cả thay đổi
            </Button>
          )}
          <Button variant="secondary" onClick={fetchSettings} disabled={loading}>
            <RefreshCw size={15} className={`mr-1.5 ${loading ? 'animate-spin' : ''}`} />
            Làm mới
          </Button>
        </div>
      </div>

      {error && (
        <div role="alert" className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-red-600 dark:text-red-400 flex items-center justify-between gap-3 text-sm">
          <div className="flex items-center gap-2">
            <AlertCircle size={18} className="shrink-0" />
            <span>{error}</span>
          </div>
          <Button variant="ghost" size="sm" onClick={() => setError('')} className="h-7 px-2">
            <X size={15} />
          </Button>
        </div>
      )}

      {/* ── SECTION 1: CẤU HÌNH THAM SỐ HỆ THỐNG ──────────────────────────────────── */}
      <div>
        <div className="flex items-center gap-2 mb-4 text-text font-semibold text-lg">
          <Sliders size={18} className="text-primary" />
          <h2>Tham số cốt lõi công cụ Dịch</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-44 rounded-xl border border-border bg-surface animate-pulse" />
            ))
          ) : (
            settings.map((setting) => {
              const meta = SETTING_METADATA[setting.key] || {
                label: setting.key,
                icon: Sliders,
                max: 5000,
                tip: setting.description,
              };
              const Icon = meta.icon;
              const isCache = setting.key === 'enable_cache';
              const statusMsg = messages[setting.key];
              const isModified = statusMsg === 'Có thay đổi chưa lưu';
              const isSaved = statusMsg === 'Đã lưu thành công';

              return (
                <Card
                  key={setting.id}
                  className={`flex flex-col justify-between transition-all duration-200 border ${
                    isModified ? 'ring-2 ring-amber-500/20 border-amber-500/40' : 'hover:border-primary/40'
                  }`}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="p-2 rounded-lg bg-primary/10 text-primary">
                          <Icon size={18} />
                        </div>
                        <CardTitle className="text-base font-semibold">{meta.label}</CardTitle>
                      </div>

                      {isModified && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                          Chưa lưu
                        </span>
                      )}
                      {isSaved && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 size={12} />
                          Đã lưu
                        </span>
                      )}
                    </div>
                    <CardDescription className="text-xs text-text-muted mt-2 leading-relaxed">
                      {setting.description || meta.tip}
                    </CardDescription>
                  </CardHeader>

                  <CardContent className="pt-2">
                    {isCache ? (
                      <div className="flex items-center justify-between p-3 rounded-lg bg-surface-muted border border-border">
                        <div className="space-y-0.5">
                          <span className="text-sm font-medium text-text">
                            {setting.value === 'true' ? 'Đang bật bộ đệm' : 'Đang tắt bộ đệm'}
                          </span>
                          <p className="text-xs text-text-muted">
                            {setting.value === 'true' ? 'Phản hồi nhanh câu lặp' : 'Luôn gọi inference mới'}
                          </p>
                        </div>
                        <button
                          type="button"
                          role="switch"
                          aria-checked={setting.value === 'true'}
                          disabled={saving !== null}
                          onClick={() => handleChange(setting.key, setting.value === 'true' ? 'false' : 'true')}
                          className={`relative inline-flex h-7 w-12 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary/20 ${
                            setting.value === 'true' ? 'bg-primary' : 'bg-border'
                          }`}
                        >
                          <span
                            aria-hidden="true"
                            className={`pointer-events-none inline-block h-6 w-6 transform rounded-full bg-white shadow-md ring-0 transition duration-200 ease-in-out ${
                              setting.value === 'true' ? 'translate-x-5' : 'translate-x-0'
                            }`}
                          />
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <div className="relative">
                          <Input
                            type="number"
                            min={1}
                            max={meta.max}
                            step={1}
                            disabled={saving !== null}
                            value={setting.value}
                            onChange={(e) => handleChange(setting.key, e.target.value)}
                            className="pr-16 text-base font-semibold"
                          />
                          {meta.unit && (
                            <span className="absolute right-3 top-2.5 text-xs text-text-muted pointer-events-none font-medium">
                              {meta.unit}
                            </span>
                          )}
                        </div>
                        <div className="flex justify-between text-[11px] text-text-muted">
                          <span>Tối thiểu: 1</span>
                          <span>Tối đa: {meta.max.toLocaleString()}</span>
                        </div>
                      </div>
                    )}

                    <div className="mt-4 pt-3 border-t border-border flex justify-end">
                      <Button
                        size="sm"
                        variant={isModified ? 'primary' : 'secondary'}
                        onClick={() => handleSave(setting.key, setting.value)}
                        isLoading={saving === setting.key}
                        disabled={saving !== null || (!isModified && !isSaved)}
                        className="w-full sm:w-auto"
                      >
                        <Save size={14} className="mr-1.5" />
                        Lưu thiết lập
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>
      </div>

      {/* ── SECTION 2: TRIỂN KHAI MODEL & CANARY A/B ────────────────────────────── */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
            <div>
              <div className="flex items-center gap-2 text-primary">
                <Cpu size={22} />
                <CardTitle>Triển khai & Quản lý Model AI</CardTitle>
              </div>
              <CardDescription className="mt-1">
                Quản lý các mô hình Active (Chính thức) và Canary (Thử nghiệm lưu lượng nhỏ). Cần quy trình reload runtime có kiểm soát.
              </CardDescription>
            </div>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-surface-muted border border-border text-text-muted">
              <ShieldCheck size={14} className="text-primary" />
              Bảo vệ kiểm soát phiên bản
            </span>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {models.map((model) => {
            const draft = modelDrafts[model.component] ?? { model_id: '', percent: '10' };
            const isNllb = model.component.toLowerCase() === 'nllb';
            const componentName = isNllb ? 'NLLB-200 (Dịch văn bản)' : 'Whisper (Nhận diện giọng nói STT)';
            const canaryPct = Math.min(50, Math.max(1, Number(draft.percent) || 10));
            const activePct = 100 - (model.canary_model ? model.canary_percent : 0);
            const componentArtifacts = artifacts.filter(
              (art) => art.component.toLowerCase() === model.component.toLowerCase()
            );

            return (
              <div
                key={model.component}
                className="rounded-xl border border-border bg-surface p-5 space-y-5 transition-all hover:border-border/80 shadow-sm"
              >
                {/* Header row */}
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-border/50 pb-3">
                  <div className="flex items-center gap-3">
                    <span className="px-2.5 py-1 rounded-md text-xs font-bold uppercase bg-primary text-white tracking-wide">
                      {model.component}
                    </span>
                    <div>
                      <h3 className="font-semibold text-base text-text">{componentName}</h3>
                      <p className="text-xs text-text-muted">Phiên bản triển khai: v{model.version}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-xs">
                    <span className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-medium bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                      Production Ready
                    </span>
                  </div>
                </div>

                {/* Active & Canary Status Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Current Active */}
                  <div className="p-4 rounded-xl bg-surface-muted border border-border/80 space-y-2">
                    <div className="flex items-center justify-between text-xs text-text-muted">
                      <span className="font-semibold uppercase tracking-wider text-primary">Model Active (Chính thức)</span>
                      <span className="font-mono">{activePct}% Lưu lượng</span>
                    </div>
                    <div className="font-mono text-sm font-semibold text-text break-all bg-surface p-2.5 rounded-lg border border-border">
                      {model.active_model}
                    </div>
                    {model.previous_active_model && (
                      <p className="text-xs text-text-muted flex items-center gap-1">
                        <span>Bản sao lưu trước:</span>
                        <span className="font-mono font-medium text-text">{model.previous_active_model}</span>
                      </p>
                    )}
                  </div>

                  {/* Current Canary status */}
                  <div className="p-4 rounded-xl bg-surface-muted border border-border/80 space-y-2">
                    <div className="flex items-center justify-between text-xs text-text-muted">
                      <span className="font-semibold uppercase tracking-wider text-amber-600 dark:text-amber-400">
                        Model Canary (Thử nghiệm A/B)
                      </span>
                      <span className="font-mono">
                        {model.canary_model ? `${model.canary_percent}% Lưu lượng` : 'Chưa kích hoạt'}
                      </span>
                    </div>
                    <div className="font-mono text-sm font-semibold text-text break-all bg-surface p-2.5 rounded-lg border border-border">
                      {model.canary_model || (
                        <span className="text-text-muted font-normal italic">Chưa cấu hình model canary</span>
                      )}
                    </div>
                    <p className="text-xs text-text-muted">
                      {model.canary_model
                        ? `Đang phân tách ${model.canary_percent}% traffic để đánh giá chất lượng`
                        : 'Nhập model ID bên dưới để kích hoạt canary split'}
                    </p>
                  </div>
                </div>

                {/* Visual Traffic Split Bar */}
                {model.canary_model && (
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs text-text-muted font-medium">
                      <span>Lưu lượng Active: {100 - model.canary_percent}%</span>
                      <span>Lưu lượng Canary: {model.canary_percent}%</span>
                    </div>
                    <div className="h-2.5 w-full rounded-full bg-border overflow-hidden flex">
                      <div
                        style={{ width: `${100 - model.canary_percent}%` }}
                        className="bg-primary h-full transition-all duration-300"
                        title="Active Traffic"
                      />
                      <div
                        style={{ width: `${model.canary_percent}%` }}
                        className="bg-amber-500 h-full transition-all duration-300"
                        title="Canary Traffic"
                      />
                    </div>
                  </div>
                )}

                {/* Inputs & Actions */}
                <div className="pt-3 border-t border-border flex flex-col gap-3">
                  {/* Gợi ý / Chọn nhanh từ Huấn luyện AI */}
                  {componentArtifacts.length > 0 ? (
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 p-2.5 rounded-lg bg-primary/5 border border-primary/20 text-xs">
                      <div className="flex items-center gap-2">
                        <Sparkles size={15} className="text-primary shrink-0" />
                        <span className="font-semibold text-text">Model từ Huấn luyện AI ({componentArtifacts.length} bản):</span>
                      </div>
                      <div className="flex items-center gap-2 w-full sm:w-auto">
                        <select
                          className="flex-1 sm:flex-initial h-8 rounded-md border border-border bg-surface px-2.5 text-xs text-text focus:outline-none focus:ring-1 focus:ring-primary"
                          value={componentArtifacts.some((a) => a.storage_uri === draft.model_id) ? draft.model_id : ''}
                          onChange={(e) => {
                            if (e.target.value) {
                              setModelDrafts((previous) => ({
                                ...previous,
                                [model.component]: {
                                  ...(previous[model.component] ?? { percent: '10' }),
                                  model_id: e.target.value,
                                },
                              }));
                            }
                          }}
                          disabled={modelSaving !== null}
                        >
                          <option value="">-- Chọn nhanh model từ kho huấn luyện --</option>
                          {componentArtifacts.map((art) => (
                            <option key={art.id} value={art.storage_uri}>
                              {art.version} [{art.status === 'validated' ? '✓ Đã kiểm tra' : art.status}] ({art.storage_uri})
                            </option>
                          ))}
                        </select>
                        <Link
                          to="/admin/training"
                          className="text-primary hover:underline flex items-center gap-1 font-medium whitespace-nowrap"
                          title="Mở Trung tâm Huấn luyện AI"
                        >
                          Chi tiết <ExternalLink size={12} />
                        </Link>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between gap-2 text-xs text-text-muted px-1">
                      <span className="flex items-center gap-1.5">
                        <Cpu size={13} className="text-text-muted" />
                        Chưa có model artifact nào từ Huấn luyện AI cho {model.component}.
                      </span>
                      <Link to="/admin/training" className="text-primary hover:underline flex items-center gap-1">
                        Huấn luyện model mới <ExternalLink size={12} />
                      </Link>
                    </div>
                  )}

                  <div className="flex flex-col md:flex-row gap-3 items-end">
                    <div className="flex-1 w-full">
                      <Input
                        label="Mã model Canary (hoặc chọn từ danh sách trên)"
                        placeholder={
                          componentArtifacts.length > 0
                            ? "Chọn từ dropdown trên hoặc nhập model HF/đường dẫn khác..."
                            : "VD: facebook/nllb-200-distilled-1.3B hoặc đường dẫn checkpoint"
                        }
                        list={`datalist-artifacts-${model.component}`}
                        value={draft.model_id}
                        onChange={(event) =>
                          setModelDrafts((previous) => ({
                            ...previous,
                            [model.component]: {
                              ...(previous[model.component] ?? { percent: '10' }),
                              model_id: event.target.value,
                            },
                          }))
                        }
                        disabled={modelSaving !== null}
                      />
                      {componentArtifacts.length > 0 && (
                        <datalist id={`datalist-artifacts-${model.component}`}>
                          {componentArtifacts.map((art) => (
                            <option key={art.id} value={art.storage_uri}>
                              {art.version} ({art.status === 'validated' ? 'Đã kiểm tra' : art.status})
                            </option>
                          ))}
                        </datalist>
                      )}
                    </div>

                    <div className="w-full md:w-44">
                      <Input
                        label="Tỷ lệ chia (%)"
                        type="number"
                        min={1}
                        max={50}
                        value={draft.percent}
                        onChange={(event) =>
                          setModelDrafts((previous) => ({
                            ...previous,
                            [model.component]: {
                              ...(previous[model.component] ?? { model_id: '' }),
                              percent: event.target.value,
                            },
                          }))
                        }
                        disabled={modelSaving !== null}
                      />
                    </div>

                  <div className="flex flex-wrap gap-2 w-full md:w-auto">
                    <Button
                      size="md"
                      onClick={() => updateModel(model.component, 'canary')}
                      isLoading={modelSaving === model.component}
                      disabled={modelSaving !== null}
                    >
                      <Save size={15} className="mr-1.5" />
                      Lưu Canary ({canaryPct}%)
                    </Button>

                    <Button
                      size="md"
                      variant="secondary"
                      onClick={() => updateModel(model.component, 'promote')}
                      disabled={!model.canary_model || modelSaving !== null}
                      title="Quảng bá model canary lên làm model Active chính thức"
                    >
                      <Rocket size={15} className="mr-1.5 text-primary" />
                      Promote
                    </Button>

                    {model.canary_model && (
                      <Button
                        size="md"
                        variant="ghost"
                        onClick={() => updateModel(model.component, 'disable')}
                        disabled={modelSaving !== null}
                        title="Hủy bỏ lưu lượng canary và đưa 100% về Active"
                        className="text-amber-600 dark:text-amber-400 hover:bg-amber-500/10"
                      >
                        <Ban size={15} className="mr-1.5" />
                        Hủy chia Canary
                      </Button>
                    )}

                    <Button
                      size="md"
                      variant="ghost"
                      onClick={() => updateModel(model.component, 'rollback')}
                      disabled={!model.previous_active_model || modelSaving !== null}
                      title="Khôi phục lại phiên bản model trước đó"
                      className="text-red-500 hover:bg-red-500/10"
                    >
                      <RotateCcw size={15} className="mr-1.5" />
                      Rollback
                    </Button>
                  </div>
                </div>
              </div>

                {/* Function descriptions for Promote / Rollback / Canary */}
                <div className="pt-2 flex flex-wrap items-center gap-x-6 gap-y-1.5 text-xs text-text-muted border-t border-border/40">
                  <span className="flex items-center gap-1.5">
                    <Save size={13} className="text-primary shrink-0" />
                    <strong>Lưu Canary:</strong> Thử nghiệm lưu lượng nhỏ (1-50%)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Rocket size={13} className="text-primary shrink-0" />
                    <strong>Promote:</strong> Thăng cấp Canary thành Active chính thức
                  </span>
                  {model.canary_model && (
                    <span className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400">
                      <Ban size={13} className="shrink-0" />
                      <strong>Hủy chia Canary:</strong> Dừng thử nghiệm, trả 100% về Active
                    </span>
                  )}
                  <span className="flex items-center gap-1.5">
                    <RotateCcw size={13} className="text-red-500 shrink-0" />
                    <strong>Rollback:</strong> Khôi phục model phiên bản trước khi có sự cố
                  </span>
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>

      {/* ── SECTION 3: NHẬT KÝ QUẢN TRỊ (AUDIT LOGS) ───────────────────────────── */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
            <div>
              <div className="flex items-center gap-2 text-primary">
                <History size={22} />
                <CardTitle>Nhật ký Quản trị & Bảo mật (Audit Trail)</CardTitle>
              </div>
              <CardDescription className="mt-1">
                Ghi nhận các tác vụ cấu hình hệ thống, thay đổi API key, model deployment và đánh giá QA (không lưu secret).
              </CardDescription>
            </div>
            <span className="text-xs text-text-muted">Lưu vết an toàn</span>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Filter Bar */}
          <div className="p-4 rounded-xl bg-surface-muted border border-border space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold text-text">
              <span className="flex items-center gap-1.5">
                <Filter size={14} className="text-primary" />
                Bộ lọc tìm kiếm nhật ký
              </span>
              {(auditFilters.actor || auditFilters.action || auditFilters.resource_type || auditFilters.created_from || auditFilters.created_to) && (
                <button
                  type="button"
                  onClick={resetAuditFilters}
                  className="text-primary hover:underline font-normal text-xs"
                >
                  Xóa bộ lọc
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
              <Input
                label="Người thực hiện"
                placeholder="VD: extension-root"
                value={auditFilters.actor}
                onChange={(event) =>
                  setAuditFilters((previous) => ({ ...previous, actor: event.target.value }))
                }
              />
              <Input
                label="Hành động"
                placeholder="VD: model.promote"
                value={auditFilters.action}
                onChange={(event) =>
                  setAuditFilters((previous) => ({ ...previous, action: event.target.value }))
                }
              />
              <Input
                label="Loại đối tượng"
                placeholder="VD: model, settings"
                value={auditFilters.resource_type}
                onChange={(event) =>
                  setAuditFilters((previous) => ({ ...previous, resource_type: event.target.value }))
                }
              />
              <Input
                label="Từ thời điểm"
                type="datetime-local"
                value={auditFilters.created_from}
                onChange={(event) =>
                  setAuditFilters((previous) => ({ ...previous, created_from: event.target.value }))
                }
              />
              <Input
                label="Đến thời điểm"
                type="datetime-local"
                value={auditFilters.created_to}
                onChange={(event) =>
                  setAuditFilters((previous) => ({ ...previous, created_to: event.target.value }))
                }
              />
            </div>

            <div className="flex justify-end pt-1">
              <Button size="sm" onClick={loadAudit}>
                <Filter size={14} className="mr-1.5" />
                Áp dụng bộ lọc
              </Button>
            </div>
          </div>

          {/* Audit Table */}
          <div className="rounded-xl border border-border overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-48">Thời gian</TableHead>
                  <TableHead className="w-48">Quản trị viên</TableHead>
                  <TableHead>Hành động</TableHead>
                  <TableHead>Đối tượng tác động</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {audit.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="h-28 text-center text-text-muted">
                      Chưa ghi nhận sự kiện audit nào phù hợp.
                    </TableCell>
                  </TableRow>
                ) : (
                  audit.map((entry) => {
                    const isModel = entry.action.startsWith('model.');
                    const isUser = entry.action.startsWith('user.');
                    const isSettings = entry.action.startsWith('settings.') || entry.action.startsWith('setting.');
                    const isQuality = entry.action.startsWith('quality.');

                    const badgeColor = isModel
                      ? 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20'
                      : isUser
                      ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20'
                      : isQuality
                      ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
                      : isSettings
                      ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20'
                      : 'bg-surface-muted text-text-muted border-border';

                    return (
                      <TableRow key={entry.id} className="hover:bg-surface-muted/40 transition-colors">
                        <TableCell className="font-mono text-xs text-text-muted whitespace-nowrap">
                          {new Date(entry.created_at).toLocaleString('vi-VN', {
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                          })}
                        </TableCell>
                        <TableCell>
                          <span className="font-semibold text-sm text-text flex items-center gap-1.5">
                            <span className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-bold">
                              {entry.actor_username ? entry.actor_username[0].toUpperCase() : 'A'}
                            </span>
                            {entry.actor_username}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-mono font-medium border ${badgeColor}`}>
                            {entry.action}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="text-xs font-medium text-text">
                            {entry.resource_type}
                            {entry.resource_id ? (
                              <span className="ml-1 text-text-muted font-mono text-[11px]">
                                #{entry.resource_id}
                              </span>
                            ) : null}
                          </span>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Settings;
