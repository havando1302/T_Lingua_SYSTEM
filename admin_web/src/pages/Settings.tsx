import { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Save } from 'lucide-react';

const Settings = () => {
  const [settings, setSettings] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState<string | null>(null);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const res = await api.get('/settings');
      setSettings(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleChange = (key: string, value: string) => {
    setSettings(prev => prev.map(s => s.key === key ? { ...s, value } : s));
  };

  const handleSave = async (key: string, value: string) => {
    setSaving(key);
    try {
      await api.put(`/settings/${key}`, { value });
      // Show some toast here ideally
    } catch (err) {
      console.error(err);
      alert('Có lỗi khi lưu cài đặt');
    } finally {
      setSaving(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Cài đặt Hệ thống</h1>
        <p className="text-text-muted mt-2">Định cấu hình các quy tắc và tính năng cốt lõi của công cụ Dịch thuật AI.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {loading ? (
          <p className="text-text-muted">Đang tải cấu hình...</p>
        ) : (
          settings.map((setting) => (
            <Card key={setting.id}>
              <CardHeader>
                <CardTitle className="text-lg">{setting.key}</CardTitle>
                <CardDescription>{setting.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex gap-4">
                  <Input
                    value={setting.value}
                    onChange={(e) => handleChange(setting.key, e.target.value)}
                  />
                  <Button 
                    onClick={() => handleSave(setting.key, setting.value)}
                    isLoading={saving === setting.key}
                  >
                    <Save size={18} className="mr-2" />
                    Lưu lại
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default Settings;
