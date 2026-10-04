import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, UserCircle, BookOpen, LogOut, Settings, Key, BarChart3, History, Menu, X, AlertCircle, BrainCircuit } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { useEffect, useRef, useState } from 'react';
import { logout } from '../lib/api';
import { useAuthUser } from '../lib/auth';

const Sidebar = () => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const user = useAuthUser();
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const sidebarRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
        menuButtonRef.current?.focus();
      }
      if (event.key === 'Tab' && window.matchMedia('(max-width: 767px)').matches) {
        const controls = [menuButtonRef.current, ...Array.from(sidebarRef.current?.querySelectorAll<HTMLElement>('a, button:not(:disabled)') ?? [])].filter(Boolean) as HTMLElement[];
        const first = controls[0];
        const last = controls[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isOpen]);

  const handleLogout = async () => {
    setLoggingOut(true);
    try {
      await logout();
    } catch {
      // The local session is cleared even if the server is unreachable.
    } finally {
      navigate('/login', { replace: true });
    }
  };

  const navItems = [
    { icon: LayoutDashboard, label: 'Bảng điều khiển', path: '/' },
    { icon: BarChart3, label: 'Thống kê', path: '/analytics' },
    ...(user?.role !== 'employee' ? [
      { icon: History, label: 'Lịch sử', path: '/history' },
    ] : []),
    { icon: BookOpen, label: 'Từ điển', path: '/dictionary' },
    { icon: AlertCircle, label: 'Cải thiện QA', path: '/qa' },
    ...(user?.role !== 'employee' ? [
      { icon: BrainCircuit, label: 'Huấn luyện AI', path: '/training-center' },
    ] : []),
    ...(user?.role === 'superadmin' ? [
      { icon: Users, label: 'Nhân sự', path: '/users' },
      { icon: Key, label: 'Mã kết nối (API)', path: '/apikeys' },
      { icon: Settings, label: 'Cài đặt', path: '/settings' },
    ] : []),
    { icon: UserCircle, label: 'Hồ sơ cá nhân', path: '/account' },
  ];

  return (
    <>
      <button 
        ref={menuButtonRef}
        type="button"
        aria-label={isOpen ? 'Đóng menu điều hướng' : 'Mở menu điều hướng'}
        aria-expanded={isOpen}
        aria-controls="admin-sidebar"
        className="md:hidden fixed top-4 left-4 z-50 p-2 bg-surface border border-border rounded-md text-text"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      <div id="admin-sidebar" ref={sidebarRef} className={`fixed inset-y-0 left-0 z-40 w-64 shrink-0 bg-surface border-r border-border flex flex-col transition-transform duration-300 md:relative md:translate-x-0 md:visible ${isOpen ? 'translate-x-0 visible' : '-translate-x-full invisible'}`}>
        <div className="p-6 pt-20 md:pt-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-white font-bold text-lg">
              T
            </div>
            <span className="text-xl font-bold text-text">T-Lingua</span>
          </div>
          <ThemeToggle />
        </div>

        <nav aria-label="Điều hướng quản trị" className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              onClick={() => setIsOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  isActive
                    ? 'bg-primary text-white font-medium shadow-md shadow-primary/20'
                    : 'text-text-muted hover:bg-background hover:text-text'
                }`
              }
            >
              <item.icon size={20} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-border">
          <button
            onClick={handleLogout}
            disabled={loggingOut}
            className="flex items-center gap-3 px-4 py-3 w-full rounded-xl text-red-500 hover:bg-red-500/10 transition-colors"
          >
            <LogOut size={20} />
            {loggingOut ? 'Đang đăng xuất…' : 'Đăng xuất'}
          </button>
        </div>
      </div>
      
      {/* Overlay for mobile */}
      {isOpen && (
        <div aria-hidden="true"
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
};

export default Sidebar;
