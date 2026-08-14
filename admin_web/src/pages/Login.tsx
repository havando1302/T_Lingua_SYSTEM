import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { Lock, User } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardContent } from '../components/ui/Card';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // If already logged in, redirect to dashboard
    if (localStorage.getItem('token')) {
      navigate('/');
    }
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
      
      const response = await api.post('/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      
      localStorage.setItem('token', response.data.access_token);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Đăng nhập thất bại. Sai tài khoản hoặc mật khẩu.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-md text-center mb-8">
        <div className="w-16 h-16 rounded-2xl bg-primary mx-auto flex items-center justify-center text-surface font-bold text-3xl mb-6 shadow-xl shadow-primary/20">
          T
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-text">Translator AI</h1>
        <p className="text-text-muted mt-2">Đăng nhập vào bảng điều khiển quản trị</p>
      </div>

      <Card className="w-full max-w-md shadow-2xl">
        <CardContent className="p-8">
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg mb-6 text-sm text-center">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-6">
            <Input
              label="Tên đăng nhập"
              icon={<User size={18} />}
              placeholder="admin"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            
            <Input
              type="password"
              label="Mật khẩu"
              icon={<Lock size={18} />}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <Button type="submit" className="w-full" size="lg" isLoading={loading}>
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
