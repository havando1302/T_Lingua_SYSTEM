import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './components/ThemeProvider';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Dictionary from './pages/Dictionary';
import QA from './pages/QA';
import Analytics from './pages/Analytics';
import History from './pages/History';
import ApiKeys from './pages/ApiKeys';
import Settings from './pages/Settings';
import Users from './pages/Users';
import Sidebar from './components/Sidebar';

// Protected Route Wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return (
    <div className="flex h-screen bg-background text-text font-sans overflow-hidden transition-colors duration-200">
      <Sidebar />
      <div className="flex-1 overflow-y-auto bg-background p-4 md:p-8">
        {children}
      </div>
    </div>
  );
};

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="admin-ui-theme">
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
          <Route path="/dictionary" element={<ProtectedRoute><Dictionary /></ProtectedRoute>} />
          <Route path="/qa" element={<ProtectedRoute><QA /></ProtectedRoute>} />
          <Route path="/users" element={<ProtectedRoute><Users /></ProtectedRoute>} />
          <Route path="/apikeys" element={<ProtectedRoute><ApiKeys /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
