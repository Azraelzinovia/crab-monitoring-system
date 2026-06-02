import React from 'react';
import { Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, Activity, Database, Heart, Settings, Cpu } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { fetchSystemHealth } from './api/client';

import DashboardPage from './pages/DashboardPage';
import DetectionPage from './pages/DetectionPage';
import SpeciesPage   from './pages/SpeciesPage';
import HealthPage    from './pages/HealthPage';
import SettingsPage  from './pages/SettingsPage';

const NAV_ITEMS = [
  { to: '/',          label: 'Dashboard',       icon: LayoutDashboard },
  { to: '/detection', label: 'Deteksi',         icon: Activity },
  { to: '/species',   label: 'Database Spesies',icon: Database },
  { to: '/health',    label: 'Kesehatan',       icon: Heart },
  { to: '/settings',  label: 'Pengaturan',      icon: Settings },
];

export default function App() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main style={{ flex: 1, marginLeft: 240, minHeight: '100vh' }}>
        <TopBar />
        <div style={{ padding: '24px' }}>
          <Routes>
            <Route path="/"          element={<DashboardPage />} />
            <Route path="/detection" element={<DetectionPage />} />
            <Route path="/species"   element={<SpeciesPage />} />
            <Route path="/health"    element={<HealthPage />} />
            <Route path="/settings"  element={<SettingsPage />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

function Sidebar() {
  return (
    <aside style={{
      width: 240, minHeight: '100vh',
      background: 'linear-gradient(180deg, #0d1117 0%, #0a0f1e 100%)',
      borderRight: '1px solid rgba(99,102,241,0.1)',
      display: 'flex', flexDirection: 'column',
      padding: '20px 12px',
      position: 'fixed', top: 0, left: 0, bottom: 0, zIndex: 100,
    }}>
      {/* Logo */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '12px 10px', marginBottom: 24,
        borderBottom: '1px solid rgba(99,102,241,0.1)', paddingBottom: 20,
      }}>
        <div style={{
          width: 36, height: 36, borderRadius: 10,
          background: 'linear-gradient(135deg, #6366f1, #06b6d4)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ fontSize: 18 }}>🦀</span>
        </div>
        <div>
          <div style={{ fontWeight: 800, fontSize: 15, color: '#f1f5f9' }}>CrabMonitor</div>
          <div style={{ fontSize: 11, color: '#64748b' }}>AI System v1.0</div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 4 }}>
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to} to={to} end={to === '/'}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          >
            <Icon size={18} />{label}
          </NavLink>
        ))}
      </nav>

      <SystemStatusBadge />
    </aside>
  );
}

function TopBar() {
  const location = useLocation();
  const titles = {
    '/':'/Dashboard', '/detection':'Deteksi Real-time',
    '/species':'Database Spesies', '/health':'Kesehatan', '/settings':'Pengaturan',
  };
  const [time, setTime] = React.useState(new Date());
  React.useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  return (
    <div style={{
      padding: '16px 24px',
      borderBottom: '1px solid rgba(99,102,241,0.08)',
      background: 'rgba(10,15,30,0.95)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      position: 'sticky', top: 0, zIndex: 50,
    }}>
      <h1 style={{ fontSize: 18, fontWeight: 700, color: '#f1f5f9' }}>
        {titles[location.pathname] || 'CrabMonitor'}
      </h1>
      <div style={{
        fontFamily: 'monospace', fontSize: 13, color: '#64748b',
        background: 'rgba(99,102,241,0.08)', padding: '6px 12px',
        borderRadius: 8, border: '1px solid rgba(99,102,241,0.15)',
      }}>
        {time.toLocaleString('id-ID')}
      </div>
    </div>
  );
}

function SystemStatusBadge() {
  const { data } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: fetchSystemHealth,
    refetchInterval: 30000,
  });
  const status = data?.status || 'checking';
  const color = status === 'healthy' ? '#22c55e' : '#f97316';

  return (
    <div style={{ paddingTop: 16, borderTop: '1px solid rgba(99,102,241,0.1)' }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, padding: '10px',
        background: 'rgba(99,102,241,0.05)', borderRadius: 10,
        border: '1px solid rgba(99,102,241,0.1)',
      }}>
        <div style={{
          width: 8, height: 8, borderRadius: '50%',
          background: color, boxShadow: `0 0 8px ${color}`,
        }} />
        <div>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#94a3b8' }}>System</div>
          <div style={{ fontSize: 12, fontWeight: 700, color, textTransform: 'capitalize' }}>{status}</div>
        </div>
        <Cpu size={14} style={{ marginLeft: 'auto', color: '#64748b' }} />
      </div>
    </div>
  );
}
