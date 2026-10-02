import React, { lazy, Suspense, useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, Link } from 'react-router-dom';
import { ThemeProvider } from './components/ThemeProvider';
import Login from './pages/Login';
import Sidebar from './components/Sidebar';
import { homeFor, useAuthUser, type Role } from './lib/auth';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Dictionary = lazy(() => import('./pages/Dictionary'));
const QA = lazy(() => import('./pages/QA'));
const Analytics = lazy(() => import('./pages/Analytics'));
const History = lazy(() => import('./pages/History'));
const ApiKeys = lazy(() => import('./pages/ApiKeys'));
const Settings = lazy(() => import('./pages/Settings'));
const Users = lazy(() => import('./pages/Users'));
const TrainingCenter = lazy(() => import('./pages/TrainingCenter'));
const Account = lazy(() => import('./pages/Account'));

// Protected Route Wrapper
const ProtectedRoute = ({ children, roles }: { children: React.ReactNode; roles?: Role[] }) => {
  const user = useAuthUser();
  const location = useLocation();
  const [notice, setNotice] = useState('');
  useEffect(() => {
    const onApiError = (event: Event) => setNotice((event as CustomEvent<string>).detail);
    window.addEventListener('admin:api-error', onApiError);
    return () => window.removeEventListener('admin:api-error', onApiError);
  }, []);
  useEffect(() => { setNotice(''); }, [location.pathname]);
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return (
    <div className="flex h-screen bg-background text-text font-sans overflow-hidden transition-colors duration-200">
      <Sidebar />
      <main id="main-content" className="min-w-0 flex-1 overflow-y-auto bg-background p-4 pt-20 md:p-8">
        {notice && <div role="alert" className="mb-6 rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-red-600 dark:text-red-400">
          {notice}
          <button className="ml-4 underline" onClick={() => setNotice('')}>Đóng</button>
        </div>}
        {roles && !roles.includes(user.role) ? (
          <div className="space-y-4">
            <h1 className="text-2xl font-bold">Không có quyền truy cập</h1>
            <p>Tài khoản của bạn không được phép xem trang này.</p>
            <Link className="text-primary underline" to={homeFor(user)}>Về trang của bạn</Link>
          </div>
        ) : <Suspense fallback={<p role="status">Đang tải trang…</p>}>{children}</Suspense>}
      </main>
    </div>
  );
};

const adminRoles: Role[] = ['admin', 'superadmin'];
const superadminRoles: Role[] = ['superadmin'];

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="admin-ui-theme">
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route path="/account" element={<ProtectedRoute><Account /></ProtectedRoute>} />
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute roles={adminRoles}><History /></ProtectedRoute>} />
          <Route path="/dictionary" element={<ProtectedRoute><Dictionary /></ProtectedRoute>} />
          <Route path="/qa" element={<ProtectedRoute><QA /></ProtectedRoute>} />
          <Route path="/training-center" element={<ProtectedRoute roles={adminRoles}><TrainingCenter /></ProtectedRoute>} />
          <Route path="/users" element={<ProtectedRoute roles={superadminRoles}><Users /></ProtectedRoute>} />
          <Route path="/apikeys" element={<ProtectedRoute roles={superadminRoles}><ApiKeys /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute roles={superadminRoles}><Settings /></ProtectedRoute>} />
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
