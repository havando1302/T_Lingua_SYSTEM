import { useCallback, useEffect, useState } from 'react';
import { useTimedMessage } from '../lib/useTimedMessage';
import { Link } from 'react-router-dom';
import api, { apiErrorMessage, locallyHandledRequest } from '../lib/api';
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
  description: string | null;
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

const COMPONENT_METADATA: Record<string, { name: string; purpose: string }> = {
  whisper: { name: 'Whisper', purpose: 'Nhận diện giọng nói (STT)' },
  nllb: { name: 'NLLB-200', purpose: 'Dịch văn bản' },
  tts_eng: { name: 'MMS TTS English', purpose: 'Tổng hợp giọng nói tiếng Anh' },
  tts_vie: { name: 'MMS TTS Vietnamese', purpose: 'Tổng hợp giọng nói tiếng Việt' },
};

const AUDIT_ACTION_LABELS: Record<string, string> = {
  'setting.update': 'Cập nhật thiết lập',
  'model.canary.configure': 'Cấu hình Canary',
  'model.canary.disable': 'Dừng Canary',
  'model.canary.promote': 'Đưa Canary thành Active',
  'model.rollback': 'Khôi phục model trước',
  'user.create': 'Tạo tài khoản',
  'user.update': 'Cập nhật tài khoản',
  'user.disable': 'Vô hiệu hóa tài khoản',
  'user.sessions_revoke': 'Thu hồi phiên tài khoản',
  'mfa.enroll': 'Liên kết MFA',
};

const EMPTY_AUDIT_FILTERS = {
  actor: '', action: '', resource_type: '', created_from: '', created_to: '',
};

const Settings = () => {
  const [settings, setSettings] = useState<Setting[]>([]);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [models, setModels] = useState<ModelDeployment[]>([]);
  const [artifacts, setArtifacts] = useState<ModelArtifact[]>([]);
  const [modelDrafts, setModelDrafts] = useState<Record<string, { model_id: string; percent: string }>>({});
  const [modelSaving, setModelSaving] = useState<string | null>(null);
  const [auditFilters, setAuditFilters] = useState(EMPTY_AUDIT_FILTERS);
  const [auditLoading, setAuditLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [savedValues, setSavedValues] = useState<Record<string, string>>({});
  const [error, setError] = useTimedMessage('');
  const [notice, setNotice] = useTimedMessage('', 5000);
  const [messages, setMessages] = useState<Record<string, string>>({});

  const dirtySettings = settings.filter((setting) => savedValues[setting.key] !== setting.value);
  const hasUnsaved = dirtySettings.length > 0;

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    setError('');
    const [settingsResult, auditResult, modelResult, artifactsResult] = await Promise.allSettled([
      api.get<Setting[]>('/settings', locallyHandledRequest),
      api.get<AuditEntry[]>('/audit?limit=25', locallyHandledRequest),
      api.get<ModelDeployment[]>('/models/deployments', locallyHandledRequest),
      api.get<ModelArtifact[]>('/training/models', locallyHandledRequest),
    ]);
    const failedSections: string[] = [];

    if (settingsResult.status === 'fulfilled') {
      setSettings(settingsResult.value.data);
      setSavedValues(Object.fromEntries(settingsResult.value.data.map((setting) => [setting.key, setting.value])));
      setMessages({});
    } else {
      failedSections.push('tham số hệ thống');
    }
    if (auditResult.status === 'fulfilled') {
      setAudit(auditResult.value.data);
    } else {
      failedSections.push('nhật ký quản trị');
    }
    if (modelResult.status === 'fulfilled') {
      const deployments = modelResult.value.data;
      setModels(deployments);
      setModelDrafts(
        Object.fromEntries(
          deployments.map((model) => [
            model.component,
            { model_id: model.canary_model ?? '', percent: String(model.canary_percent || 10) },
          ])
        )
      );
    } else {
      failedSections.push('triển khai model');
    }
    if (artifactsResult.status === 'fulfilled') {
      setArtifacts(artifactsResult.value.data ?? []);
    } else {
      setArtifacts([]);
      failedSections.push('kho model huấn luyện');
    }

    if (failedSections.length) {
      setError(`Không tải được ${failedSections.join(', ')}. Các phần còn lại vẫn có thể sử dụng.`);
    }
    setLoading(false);
  }, [setError]);

  useEffect(() => {
    void fetchSettings();
  }, [fetchSettings]);

  useEffect(() => {
    if (!hasUnsaved) return undefined;
    const warnBeforeLeaving = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', warnBeforeLeaving);
    return () => window.removeEventListener('beforeunload', warnBeforeLeaving);
  }, [hasUnsaved]);

  const handleRefresh = () => {
    if (hasUnsaved && !window.confirm('Làm mới sẽ bỏ các thay đổi chưa lưu. Bạn có muốn tiếp tục?')) return;
    void fetchSettings();
  };

  const validateSetting = (key: string, value: string) => {
    const meta = SETTING_METADATA[key];
    if (key === 'enable_cache') {
      return value === 'true' || value === 'false' ? '' : 'Trạng thái bộ đệm không hợp lệ.';
    }
    const maximum = meta?.max ?? 5000;
    if (!/^\d+$/.test(value.trim()) || Number(value) < 1 || Number(value) > maximum) {
      return `${meta?.label ?? key}: Vui lòng nhập số nguyên từ 1 đến ${maximum}.`;
    }
    return '';
  };

  const markSettingSaved = (key: string) => {
    setMessages((previous) => ({ ...previous, [key]: 'Đã lưu thành công' }));
    window.setTimeout(() => {
      setMessages((previous) => {
        if (previous[key] !== 'Đã lưu thành công') return previous;
        const next = { ...previous };
        delete next[key];
        return next;
      });
    }, 3500);
  };

  const handleChange = (key: string, value: string) => {
    setSettings((prev) => prev.map((s) => (s.key === key ? { ...s, value } : s)));
    setMessages((previous) => {
      if (!previous[key]) return previous;
      const next = { ...previous };
      delete next[key];
      return next;
    });
  };

  const handleSave = async (key: string, value: string) => {
    if (saving) return;
    const validationError = validateSetting(key, value);
    if (validationError) return setError(validationError);
    setError('');
    setSaving(key);
    try {
      const response = await api.put<Setting>(`/settings/${key}`, { value }, locallyHandledRequest);
      setSettings((previous) => previous.map((setting) => (setting.key === key ? response.data : setting)));
      setSavedValues((previous) => ({ ...previous, [key]: response.data.value }));
      markSettingSaved(key);
      setNotice(`Đã lưu “${SETTING_METADATA[key]?.label ?? key}”.`);
    } catch (err) {
      setError(apiErrorMessage(err, 'Có lỗi khi lưu cài đặt'));
    } finally {
      setSaving(null);
    }
  };

  const handleSaveAll = async () => {
    if (saving || dirtySettings.length === 0) return;
    const invalid = dirtySettings.map((setting) => validateSetting(setting.key, setting.value)).find(Boolean);
    if (invalid) return setError(invalid);

    setSaving('__all__');
    setError('');
    let savedCount = 0;
    const failed: string[] = [];
    for (const setting of dirtySettings) {
      try {
        const response = await api.put<Setting>(
          `/settings/${setting.key}`,
          { value: setting.value },
          locallyHandledRequest
        );
        setSettings((previous) => previous.map((item) => (item.key === setting.key ? response.data : item)));
        setSavedValues((previous) => ({ ...previous, [setting.key]: response.data.value }));
        markSettingSaved(setting.key);
        savedCount += 1;
      } catch (err) {
        failed.push(`${SETTING_METADATA[setting.key]?.label ?? setting.key}: ${apiErrorMessage(err)}`);
      }
    }
    setSaving(null);
    if (savedCount) setNotice(`Đã lưu ${savedCount}/${dirtySettings.length} thiết lập.`);
    if (failed.length) setError(`Một số thiết lập chưa lưu được. ${failed.join(' ')}`);
  };

  const loadAudit = async () => {
    if (auditLoading) return;
    if (auditFilters.created_from && auditFilters.created_to
        && new Date(auditFilters.created_from) > new Date(auditFilters.created_to)) {
      setError('Thời điểm bắt đầu phải trước thời điểm kết thúc.');
      return;
    }
    setError('');
    setAuditLoading(true);
    try {
      const params = Object.fromEntries(
        Object.entries(auditFilters)
          .filter(([, value]) => value)
          .map(([key, value]) => [
            key,
            key === 'created_from' || key === 'created_to' ? new Date(value).toISOString() : value.trim(),
          ])
      );
      const response = await api.get<AuditEntry[]>('/audit', {
        ...locallyHandledRequest,
        params: { ...params, limit: 100 },
      });
      setAudit(response.data);
    } catch (err) {
      setError(apiErrorMessage(err, 'Không thể lọc nhật ký.'));
    } finally {
      setAuditLoading(false);
    }
  };

  const resetAuditFilters = async () => {
    if (auditLoading) return;
    setAuditFilters(EMPTY_AUDIT_FILTERS);
    setAuditLoading(true);
    setError('');
    try {
      const response = await api.get<AuditEntry[]>('/audit?limit=25', locallyHandledRequest);
      setAudit(response.data);
    } catch (err) {
      setError(apiErrorMessage(err, 'Không thể tải lại nhật ký.'));
    } finally {
      setAuditLoading(false);
    }
  };

  const updateModel = async (component: string, operation: 'canary' | 'promote' | 'rollback' | 'disable') => {
    if (modelSaving) return;
    const draft = modelDrafts[component] ?? { model_id: '', percent: '10' };
    const deployment = models.find((model) => model.component === component);
    if (operation === 'canary') {
      const modelId = draft.model_id.trim();
      if (!modelId) return setError('Vui lòng nhập mã model Canary. Dùng nút “Hủy chia Canary” để dừng thử nghiệm.');
      if (modelId.includes('..') || modelId.includes('\\')) return setError('Mã model Canary không được chứa “..” hoặc dấu gạch chéo ngược.');
      if (!/^\d+$/.test(draft.percent) || Number(draft.percent) < 1 || Number(draft.percent) > 50) {
        return setError('Tỷ lệ Canary phải là số nguyên từ 1% đến 50%.');
      }
      if (modelId === deployment?.active_model) return setError('Model Canary phải khác model Active hiện tại.');
      if (!window.confirm(`Áp dụng model Canary “${modelId}” cho ${component.toUpperCase()} với ${draft.percent}% lưu lượng? Sau khi lưu cần reload runtime và kiểm tra health check.`)) return;
    }
    if (operation === 'disable' && !window.confirm(`Bạn có chắc muốn hủy chia Canary của ${component.toUpperCase()} và chuyển 100% lưu lượng về model Active?`)) {
      return;
    }
    if (operation === 'promote' && !window.confirm(`Bạn có chắc muốn đưa model Canary của ${component.toUpperCase()} lên làm bản chính thức (Active)? Sau thao tác cần reload runtime và kiểm tra health check.`)) {
      return;
    }
    if (operation === 'rollback' && !window.confirm(`Bạn có chắc muốn khôi phục ${component.toUpperCase()} về phiên bản trước? Sau thao tác cần reload runtime và kiểm tra health check.`)) {
      return;
    }

    setModelSaving(component);
    setError('');
    try {
      const response =
        operation === 'canary'
          ? await api.put(`/models/${component}/canary`, { model_id: draft.model_id.trim(), percent: Number(draft.percent) }, locallyHandledRequest)
          : operation === 'disable'
          ? await api.delete(`/models/${component}/canary`, locallyHandledRequest)
          : await api.post(`/models/${component}/${operation}`, undefined, locallyHandledRequest);

      setModels((previous) => previous.map((model) => (model.component === component ? response.data : model)));
      setModelDrafts((previous) => ({
        ...previous,
        [component]: {
          model_id: response.data.canary_model ?? '',
          percent: String(response.data.canary_percent || 10),
        },
      }));
      const operationLabels = {
        canary: 'Đã lưu cấu hình Canary',
        disable: 'Đã dừng chia Canary',
        promote: 'Đã đưa Canary thành model Active',
        rollback: 'Đã khôi phục model trước',
      };
      setNotice(`${operationLabels[operation]}. Cần reload runtime và kiểm tra health check để áp dụng an toàn.`);
      await loadAudit();
    } catch (err) {
      setError(apiErrorMessage(err, 'Không thể cập nhật cấu hình model.'));
    } finally {
      setModelSaving(null);
    }
  };

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
            <Button
              onClick={handleSaveAll}
              isLoading={saving === '__all__'}
              disabled={saving !== null}
              className="shadow-md shadow-primary/20"
            >
              <Save size={16} className="mr-2" />
              Lưu tất cả ({dirtySettings.length})
            </Button>
          )}
          <Button variant="secondary" onClick={handleRefresh} disabled={loading || saving !== null || modelSaving !== null}>
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

      {notice && (
        <div role="status" className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-emerald-700 dark:text-emerald-400 flex items-center gap-2 text-sm">
          <CheckCircle2 size={18} className="shrink-0" />
          <span>{notice}</span>
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
          ) : settings.length === 0 ? (
            <div className="md:col-span-3 rounded-xl border border-dashed border-border p-8 text-center text-sm text-text-muted">
              Chưa có tham số hệ thống nào được cấu hình.
            </div>
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
              const isModified = savedValues[setting.key] !== setting.value;
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
                        disabled={saving !== null || !isModified}
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
                Quản lý model Active và Canary ở control-plane. Mỗi thay đổi cần reload inference runtime và kiểm tra health check trước khi phục vụ người dùng.
              </CardDescription>
            </div>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-surface-muted border border-border text-text-muted">
              <ShieldCheck size={14} className="text-primary" />
              Bảo vệ kiểm soát phiên bản
            </span>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {loading ? (
            Array.from({ length: 2 }).map((_, index) => (
              <div key={index} className="h-72 rounded-xl border border-border bg-surface animate-pulse" />
            ))
          ) : models.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border p-8 text-center text-sm text-text-muted">
              Không tải được hoặc chưa có cấu hình triển khai model.
            </div>
          ) : models.map((model) => {
            const draft = modelDrafts[model.component] ?? { model_id: '', percent: '10' };
            const componentMeta = COMPONENT_METADATA[model.component.toLowerCase()] ?? {
              name: model.component.toUpperCase(),
              purpose: 'Model hệ thống',
            };
            const componentName = `${componentMeta.name} (${componentMeta.purpose})`;
            const canaryPct = Math.min(50, Math.max(1, Number(draft.percent) || 10));
            const activePct = 100 - (model.canary_model ? model.canary_percent : 0);
            const candidateModelId = draft.model_id.trim();
            const canaryPercentIsValid = /^\d+$/.test(draft.percent)
              && Number(draft.percent) >= 1
              && Number(draft.percent) <= 50;
            const canaryModelIdIsValid = Boolean(candidateModelId)
              && candidateModelId !== model.active_model
              && !candidateModelId.includes('..')
              && !candidateModelId.includes('\\');
            const canaryDraftIsValid = canaryModelIdIsValid && canaryPercentIsValid;
            const canaryDraftChanged = candidateModelId !== (model.canary_model ?? '')
              || Number(draft.percent) !== (model.canary_percent || 10);
            const canaryDraftError = !candidateModelId
              ? ''
              : candidateModelId === model.active_model
              ? 'Model Canary phải khác model Active hiện tại.'
              : candidateModelId.includes('..') || candidateModelId.includes('\\')
              ? 'Mã model không được chứa “..” hoặc dấu gạch chéo ngược.'
              : !canaryPercentIsValid
              ? 'Tỷ lệ Canary phải là số nguyên từ 1% đến 50%.'
              : '';
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
                    <span className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400 font-medium bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-500/20">
                      <AlertCircle size={13} />
                      Cần reload runtime khi thay đổi
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
                          to="/training-center"
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
                      <Link to="/training-center" className="text-primary hover:underline flex items-center gap-1">
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
                        aria-invalid={Boolean(canaryDraftError && !canaryModelIdIsValid)}
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
                        step={1}
                        value={draft.percent}
                        aria-invalid={Boolean(canaryDraftError && !canaryPercentIsValid)}
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
                      disabled={modelSaving !== null || !canaryDraftIsValid || !canaryDraftChanged}
                    >
                      <Save size={15} className="mr-1.5" />
                      Áp dụng Canary ({canaryPct}%)
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
                {canaryDraftError && (
                  <p role="alert" className="text-xs text-red-600 dark:text-red-400 flex items-center gap-1.5">
                    <AlertCircle size={13} className="shrink-0" />
                    {canaryDraftError}
                  </p>
                )}
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
                  disabled={auditLoading}
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
                disabled={auditLoading}
                onChange={(event) =>
                  setAuditFilters((previous) => ({ ...previous, actor: event.target.value }))
                }
              />
              <Input
                label="Hành động"
                placeholder="VD: model.promote"
                value={auditFilters.action}
                disabled={auditLoading}
                onChange={(event) =>
                  setAuditFilters((previous) => ({ ...previous, action: event.target.value }))
                }
              />
              <Input
                label="Loại đối tượng"
                placeholder="VD: model, settings"
                value={auditFilters.resource_type}
                disabled={auditLoading}
                onChange={(event) =>
                  setAuditFilters((previous) => ({ ...previous, resource_type: event.target.value }))
                }
              />
              <Input
                label="Từ thời điểm"
                type="datetime-local"
                value={auditFilters.created_from}
                disabled={auditLoading}
                onChange={(event) =>
                  setAuditFilters((previous) => ({ ...previous, created_from: event.target.value }))
                }
              />
              <Input
                label="Đến thời điểm"
                type="datetime-local"
                value={auditFilters.created_to}
                disabled={auditLoading}
                onChange={(event) =>
                  setAuditFilters((previous) => ({ ...previous, created_to: event.target.value }))
                }
              />
            </div>

            <div className="flex justify-end pt-1">
              <Button size="sm" onClick={loadAudit} isLoading={auditLoading}>
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
                {auditLoading ? (
                  <TableRow>
                    <TableCell colSpan={4} className="h-28 text-center text-text-muted">
                      Đang tải nhật ký…
                    </TableCell>
                  </TableRow>
                ) : audit.length === 0 ? (
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
                          <span
                            title={entry.action}
                            className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${badgeColor}`}
                          >
                            {AUDIT_ACTION_LABELS[entry.action] ?? entry.action}
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
