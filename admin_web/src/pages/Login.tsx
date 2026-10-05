import { useState, useEffect } from 'react';
import { useTimedMessage } from '../lib/useTimedMessage';
import { useNavigate } from 'react-router-dom';
import api, { apiConfigurationError, apiErrorMessage } from '../lib/api';
import {
  clearSession, homeFor, isMfaChallenge, setSession, updateSessionUser,
  type AuthUser, type LoginResult, type MfaChallenge,
} from '../lib/auth';
import { Check, Copy, KeyRound, Lock, ShieldCheck, User } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardContent } from '../components/ui/Card';

const Login = () => {
  const [stage, setStage] = useState<'credentials' | 'verify' | 'setup'>('credentials');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [challenge, setChallenge] = useState<MfaChallenge | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useTimedMessage('');
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
      if (stage !== 'credentials') formData.append('otp', otp.trim());
      
      const response = await api.post<LoginResult>('/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      if (isMfaChallenge(response.data)) {
        setChallenge(response.data);
        setStage(response.data.enrollment_required ? 'setup' : 'verify');
        setOtp('');
        return;
      }
      
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

  const resetLogin = () => {
    clearSession();
    setStage('credentials');
    setChallenge(null);
    setPassword('');
    setOtp('');
    setCopied(false);
    setError('');
  };

  const copySecret = async () => {
    if (!challenge?.secret) return;
    try {
      await navigator.clipboard.writeText(challenge.secret);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setError('Không thể sao chép tự động. Hãy chọn và sao chép khóa thủ công.');
    }
  };

  const formattedSecret = challenge?.secret?.match(/.{1,4}/g)?.join(' ') ?? '';

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-md text-center mb-8">
        <div className="w-16 h-16 rounded-2xl bg-primary mx-auto flex items-center justify-center text-white font-bold text-3xl mb-6 shadow-xl shadow-primary/20">
          T
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-text">Translator AI</h1>
        <p className="text-text-muted mt-2">
          {stage === 'credentials' ? 'Đăng nhập vào cổng vận hành Translator AI' : 'Xác minh danh tính bằng MFA'}
        </p>
      </div>

      <Card className="w-full max-w-md shadow-2xl">
        <CardContent className="p-8">
          {(error || apiConfigurationError) && (
            <div role="alert" className="bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg mb-6 text-sm text-center">
              {apiConfigurationError || error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-6">
            {stage === 'credentials' ? (
              <>
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
              </>
            ) : (
              <>
                <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 text-left">
                  <div className="flex items-start gap-3">
                    <ShieldCheck className="mt-0.5 shrink-0 text-primary" size={22} />
                    <div>
                      <h2 className="font-semibold text-text">
                        {stage === 'setup' ? 'Liên kết ứng dụng xác thực' : 'Nhập mã xác thực'}
                      </h2>
                      <p className="mt-1 text-sm text-text-muted">
                        {stage === 'setup'
                          ? 'Tài khoản chưa có MFA. Bạn phải hoàn tất bước này trước khi được đăng nhập.'
                          : `Mở ứng dụng xác thực đã liên kết với tài khoản ${username}.`}
                      </p>
                    </div>
                  </div>
                </div>

                {stage === 'setup' && (
                  <div className="space-y-3 text-left text-sm text-text-muted">
                    <p>1. Thêm tài khoản mới trong Google/Microsoft Authenticator hoặc ứng dụng TOTP tương thích.</p>
                    {challenge?.provisioning_uri && (
                      <a
                        className="inline-flex items-center gap-2 font-medium text-primary hover:underline"
                        href={challenge.provisioning_uri}
                      >
                        <KeyRound size={16} /> Mở trong ứng dụng xác thực
                      </a>
                    )}
                    <p>2. Nếu không mở được liên kết, nhập khóa thiết lập thủ công:</p>
                    <div className="flex items-center gap-2 rounded-lg border border-border bg-background p-3">
                      <code className="min-w-0 flex-1 select-all break-all font-mono text-sm font-semibold tracking-wider text-text">
                        {formattedSecret}
                      </code>
                      <Button type="button" variant="ghost" size="sm" onClick={copySecret} aria-label="Sao chép khóa thiết lập">
                        {copied ? <Check size={16} /> : <Copy size={16} />}
                      </Button>
                    </div>
                    <p>3. Nhập mã 6 chữ số đang hiển thị để xác nhận liên kết.</p>
                  </div>
                )}

                <Input
                  label="Mã xác thực MFA"
                  icon={<KeyRound size={18} />}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  autoComplete="one-time-code"
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  minLength={6}
                  maxLength={6}
                  placeholder="000000"
                  autoFocus
                  required
                />
              </>
            )}
            <Button type="submit" className="w-full" size="lg" isLoading={loading} disabled={!!apiConfigurationError}>
              {stage === 'credentials' ? 'Tiếp tục' : stage === 'setup' ? 'Xác nhận và đăng nhập' : 'Xác minh và đăng nhập'}
            </Button>
            {stage !== 'credentials' && (
              <Button type="button" variant="ghost" className="w-full" onClick={resetLogin}>
                Dùng tài khoản khác
              </Button>
            )}
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
