import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { apiConfigurationError, apiErrorMessage } from '../lib/api';
import { clearSession, homeFor, setSession, updateSessionUser, type AuthUser, type LoginResponse } from '../lib/auth';
import { Lock, User } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardContent } from '../components/ui/Card';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Set dark mode for login page if system preference is dark
    const root = window.document.documentElement;
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (isDark) root.classList.add('dark');
  }, [navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      if (otp.trim()) formData.append('otp', otp.trim());
      
      const response = await api.post<LoginResponse>('/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      
      setSession(response.data);
      const profile = await api.get<AuthUser>('/me');
      updateSessionUser(profile.data);
      setPassword('');
      setOtp('');
      navigate(homeFor(profile.data), { replace: true });
    } catch (err: unknown) {
      clearSession();
      setError(apiErrorMessage(err, 'Đăng nhập thất bại. Vui lòng kiểm tra thông tin và mã xác thực.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-md text-center mb-8">
        <div className="w-16 h-16 rounded-2xl bg-primary mx-auto flex items-center justify-center text-white font-bold text-3xl mb-6 shadow-xl shadow-primary/20">
          T
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-text">Translator AI</h1>
        <p className="text-text-muted mt-2">Đăng nhập vào cổng vận hành Translator AI</p>
      </div>

      <Card className="w-full max-w-md shadow-2xl">
        <CardContent className="p-8">
          {(error || apiConfigurationError) && (
            <div role="alert" className="bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg mb-6 text-sm text-center">
              {apiConfigurationError || error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-6">
            <Input
              label="Tên đăng nhập"
              icon={<User size={18} />}
              placeholder="admin"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
            
            <Input
              type="password"
              label="Mật khẩu"
              icon={<Lock size={18} />}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
            <Input
              label="Mã xác thực MFA (nếu được yêu cầu)"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              autoComplete="one-time-code"
              inputMode="numeric"
              pattern="[0-9]{6}"
              maxLength={6}
              placeholder="6 chữ số từ ứng dụng xác thực"
            />
            <Button type="submit" className="w-full" size="lg" isLoading={loading} disabled={!!apiConfigurationError}>
              Đăng nhập
            </Button>
          </form>
        </CardContent>
      </Card>
      
      <p className="mt-8 text-sm text-text-muted">
        &copy; {new Date().getFullYear()} Translator AI. Đã đăng ký bản quyền.
      </p>
    </div>
  );
};

export default Login;
