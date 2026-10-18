import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  UserCircle,
  BookOpen,
  LogOut,
  Settings,
  Key,
  BarChart3,
  History,
  Menu,
  X,
  AlertCircle,
  BrainCircuit,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { useCallback, useEffect, useRef, useState } from 'react';
import { logout } from '../lib/api';
import { useAuthUser } from '../lib/auth';

const Sidebar = () => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(() => {
    try {
      return localStorage.getItem('admin_sidebar_collapsed') === 'true';
    } catch {
      return false;
    }
  });
  const [loggingOut, setLoggingOut] = useState(false);
  const user = useAuthUser();
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const sidebarRef = useRef<HTMLDivElement>(null);

  const toggleCollapse = useCallback(() => {
    setIsCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem('admin_sidebar_collapsed', String(next));
      } catch {
        // Storage access may fail in private mode
      }
      return next;
    });
  }, []);

  // Keyboard shortcut: Ctrl+B or Cmd+B to toggle sidebar collapse
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'b') {
        event.preventDefault();
        toggleCollapse();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleCollapse]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
        menuButtonRef.current?.focus();
      }
      if (event.key === 'Tab' && window.matchMedia('(max-width: 767px)').matches) {
        const controls = [
          menuButtonRef.current,
          ...Array.from(sidebarRef.current?.querySelectorAll<HTMLElement>('a, button:not(:disabled)') ?? []),
        ].filter(Boolean) as HTMLElement[];
        const first = controls[0];
        const last = controls[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        }
        if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
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
    ...(user?.role !== 'employee'
      ? [{ icon: History, label: 'Lịch sử', path: '/history' }]
      : []),
    { icon: BookOpen, label: 'Từ điển', path: '/dictionary' },
    { icon: AlertCircle, label: 'Cải thiện QA', path: '/qa' },
    ...(user?.role !== 'employee'
      ? [{ icon: BrainCircuit, label: 'Huấn luyện AI', path: '/training-center' }]
      : []),
    ...(user?.role === 'superadmin'
      ? [
          { icon: Users, label: 'Nhân sự', path: '/users' },
          { icon: Key, label: 'Mã kết nối (API)', path: '/apikeys' },
          { icon: Settings, label: 'Cài đặt', path: '/settings' },
        ]
      : []),
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
        className="md:hidden fixed top-4 left-4 z-50 p-2 bg-surface border border-border rounded-md text-text shadow-sm"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      <div
        id="admin-sidebar"
        ref={sidebarRef}
        className={`fixed inset-y-0 left-0 z-40 shrink-0 bg-surface border-r border-border flex flex-col transition-[width,transform] duration-300 ease-in-out md:relative md:translate-x-0 md:visible ${
          isOpen ? 'translate-x-0 visible' : '-translate-x-full invisible'
        } ${isCollapsed ? 'w-64 md:w-20' : 'w-64'}`}
      >
        {/* Header */}
        <div
          className={`pt-20 md:pt-4 pb-4 border-b border-border/50 flex ${
            isCollapsed
              ? 'px-2 flex-col items-center gap-3'
              : 'px-5 items-center justify-between'
          }`}
        >
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center text-white font-bold text-lg shadow-sm shadow-primary/25 shrink-0">
              T
            </div>
            {!isCollapsed && (
              <span className="text-xl font-bold text-text tracking-tight truncate">
                T-Lingua
              </span>
            )}
          </div>

          <div className={`flex items-center ${isCollapsed ? 'flex-col gap-2' : 'gap-1'} shrink-0`}>
            <ThemeToggle />
            <button
              type="button"
              onClick={toggleCollapse}
              aria-label={isCollapsed ? 'Mở rộng menu điều hướng' : 'Thu gọn menu điều hướng'}
              title={isCollapsed ? 'Mở rộng menu (Ctrl+B)' : 'Thu gọn menu (Ctrl+B)'}
              className="hidden md:inline-flex items-center justify-center w-8 h-8 rounded-lg text-text-muted hover:text-text hover:bg-background transition-colors"
            >
              {isCollapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
            </button>
          </div>
        </div>

        {/* Navigation links */}
        <nav
          aria-label="Điều hướng quản trị"
          className={`flex-1 py-4 space-y-1.5 overflow-y-auto overflow-x-hidden ${
            isCollapsed ? 'px-2' : 'px-3'
          }`}
        >
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              onClick={() => setIsOpen(false)}
              title={isCollapsed ? item.label : undefined}
              className={({ isActive }) =>
                `flex items-center rounded-xl transition-all whitespace-nowrap ${
                  isCollapsed ? 'justify-center w-10 h-10 mx-auto' : 'gap-3 px-3.5 py-2.5'
                } ${
                  isActive
                    ? 'bg-primary text-white font-medium shadow-md shadow-primary/20'
                    : 'text-text-muted hover:bg-background hover:text-text'
                }`
              }
            >
              <item.icon size={20} className="shrink-0" />
              {!isCollapsed && <span className="truncate">{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Logout bottom */}
        <div className={`border-t border-border/50 ${isCollapsed ? 'p-2 flex justify-center' : 'p-3'}`}>
          <button
            onClick={handleLogout}
            disabled={loggingOut}
            title={isCollapsed ? (loggingOut ? 'Đang đăng xuất…' : 'Đăng xuất') : undefined}
            className={`flex items-center rounded-xl text-red-500 hover:bg-red-500/10 transition-colors whitespace-nowrap ${
              isCollapsed ? 'justify-center w-10 h-10' : 'gap-3 px-3.5 py-2.5 w-full'
            }`}
          >
            <LogOut size={20} className="shrink-0" />
            {!isCollapsed && (
              <span className="truncate">{loggingOut ? 'Đang đăng xuất…' : 'Đăng xuất'}</span>
            )}
          </button>
        </div>
      </div>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          aria-hidden="true"
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
};

export default Sidebar;
