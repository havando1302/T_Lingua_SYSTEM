import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, BookOpen, LogOut, Settings, Key, BarChart3, History, Menu, X, AlertCircle } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { useState } from 'react';

const Sidebar = () => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const navItems = [
    { icon: LayoutDashboard, label: 'Bảng điều khiển', path: '/' },
    { icon: BarChart3, label: 'Thống kê', path: '/analytics' },
    { icon: History, label: 'Lịch sử', path: '/history' },
    { icon: BookOpen, label: 'Từ điển', path: '/dictionary' },
    { icon: AlertCircle, label: 'Cải thiện QA', path: '/qa' },
    { icon: Users, label: 'Nhân sự', path: '/users' },
    { icon: Key, label: 'Mã kết nối (API)', path: '/apikeys' },
    { icon: Settings, label: 'Cài đặt', path: '/settings' },
  ];

  return (
    <>
      <button 
        className="md:hidden fixed top-4 left-4 z-50 p-2 bg-surface border border-border rounded-md text-text"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      <div className={`fixed inset-y-0 left-0 z-40 w-64 bg-surface border-r border-border flex flex-col transition-transform duration-300 md:relative md:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-surface font-bold text-lg">
              T
            </div>
            <span className="text-xl font-bold text-text">Translator AI</span>
          </div>
          <ThemeToggle />
        </div>

        <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setIsOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  isActive
                    ? 'bg-primary text-surface font-medium shadow-md shadow-primary/20'
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
            className="flex items-center gap-3 px-4 py-3 w-full rounded-xl text-red-500 hover:bg-red-500/10 transition-colors"
          >
            <LogOut size={20} />
            Đăng xuất
          </button>
        </div>
      </div>
      
      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
};

export default Sidebar;
