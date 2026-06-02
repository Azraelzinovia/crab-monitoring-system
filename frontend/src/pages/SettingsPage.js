import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchSystemHealth, fetchSystemResources } from '../api/client';

export default function SettingsPage() {
  const { data: health } = useQuery({ queryKey: ['systemHealth'], queryFn: fetchSystemHealth, refetchInterval: 15000 });
  const { data: resources } = useQuery({ queryKey: ['systemResources'], queryFn: fetchSystemResources, refetchInterval: 5000 });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="glass-card" style={{ padding: 20 }}>
        <h2 style={{ fontSize: 16, fontWeight: 700, color: '#f1f5f9' }}>⚙️ Pengaturan & Status Sistem</h2>
      </div>

      {/* Resource gauges */}
      {resources && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14 }}>
          <ResourceCard label="CPU" percent={resources.cpu?.percent} cores={resources.cpu?.cores} temp={resources.cpu?.temperature_c} />
          <ResourceCard label="RAM" percent={resources.memory?.percent} used={resources.memory?.used_gb} total={resources.memory?.total_gb} unit="GB" />
          <ResourceCard label="Disk" percent={resources.disk?.percent} used={resources.disk?.used_gb} total={resources.disk?.total_gb} unit="GB" />
        </div>
      )}

      {/* System info */}
      {health && (
        <div className="glass-card" style={{ padding: 20 }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: '#f1f5f9', marginBottom: 14 }}>Status Komponen</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 10 }}>
            <StatusRow label="Database" value={health.database} />
            <StatusRow label="Uptime" value={`${Math.floor((health.uptime_seconds || 0) / 60)} menit`} />
            {health.ai_models && Object.entries(health.ai_models).map(([k, v]) => (
              <StatusRow key={k} label={k.replace(/_/g, ' ')} value={v} />
            ))}
          </div>
        </div>
      )}

      {/* API info */}
      <div className="glass-card" style={{ padding: 20 }}>
        <h3 style={{ fontSize: 14, fontWeight: 700, color: '#f1f5f9', marginBottom: 14 }}>🔗 Endpoint API</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {[
            ['GET', '/api/v1/crabs', 'List semua kepiting'],
            ['GET', '/api/v1/crabs/{id}', 'Detail kepiting'],
            ['POST', '/api/v1/detect', 'Jalankan deteksi AI'],
            ['GET', '/api/v1/statistics', 'Statistik dashboard'],
            ['GET', '/api/v1/stream/cam1', 'MJPEG stream kamera 1'],
            ['GET', '/api/v1/stream/cam2', 'MJPEG stream kamera 2'],
            ['GET', '/api/v1/health', 'System health check'],
            ['GET', '/docs', 'Swagger API Documentation'],
          ].map(([method, path, desc]) => (
            <div key={path} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '8px 12px', borderRadius: 8,
              background: 'rgba(99,102,241,0.06)',
              border: '1px solid rgba(99,102,241,0.1)',
            }}>
              <span style={{
                fontSize: 10, fontWeight: 800, padding: '2px 6px', borderRadius: 4,
                background: method === 'GET' ? 'rgba(34,197,94,0.15)' : 'rgba(99,102,241,0.2)',
                color: method === 'GET' ? '#4ade80' : '#a5b4fc',
                fontFamily: 'monospace',
              }}>{method}</span>
              <code style={{ fontSize: 12, color: '#e2e8f0', flex: 1 }}>{path}</code>
              <span style={{ fontSize: 11, color: '#64748b' }}>{desc}</span>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 14 }}>
          <a href="/docs" target="_blank" rel="noopener noreferrer" style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '8px 16px', borderRadius: 8, fontSize: 13, fontWeight: 600,
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            color: '#fff', textDecoration: 'none',
          }}>
            📖 Buka Swagger UI
          </a>
        </div>
      </div>
    </div>
  );
}

function ResourceCard({ label, percent, cores, temp, used, total, unit }) {
  const color = percent > 85 ? '#ef4444' : percent > 60 ? '#eab308' : '#22c55e';
  return (
    <div className="glass-card" style={{ padding: 20 }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: '#94a3b8', marginBottom: 12 }}>{label}</div>
      <div style={{ position: 'relative', marginBottom: 12 }}>
        <svg viewBox="0 0 100 50" style={{ width: '100%' }}>
          <path d="M 10 45 A 40 40 0 0 1 90 45" stroke="rgba(255,255,255,0.08)" strokeWidth="8" fill="none" />
          <path
            d="M 10 45 A 40 40 0 0 1 90 45"
            stroke={color} strokeWidth="8" fill="none"
            strokeDasharray={`${(percent || 0) * 1.26} 126`}
            strokeLinecap="round"
            style={{ transition: 'stroke-dasharray 0.5s' }}
          />
        </svg>
        <div style={{ position: 'absolute', bottom: 0, width: '100%', textAlign: 'center' }}>
          <div style={{ fontSize: 22, fontWeight: 800, color }}>{percent?.toFixed(0) || 0}%</div>
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {used != null && <div style={{ fontSize: 11, color: '#64748b' }}>{used?.toFixed(1)} / {total?.toFixed(1)} {unit}</div>}
        {cores && <div style={{ fontSize: 11, color: '#64748b' }}>{cores} cores</div>}
        {temp && <div style={{ fontSize: 11, color: '#f97316' }}>🌡️ {temp}°C</div>}
      </div>
    </div>
  );
}

function StatusRow({ label, value }) {
  const isOk = value === 'connected' || value === 'loaded' || value === 'healthy';
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '8px 12px', borderRadius: 8, background: 'rgba(99,102,241,0.04)',
      border: '1px solid rgba(99,102,241,0.08)',
    }}>
      <span style={{ fontSize: 12, color: '#94a3b8', textTransform: 'capitalize' }}>{label}</span>
      <span style={{
        fontSize: 12, fontWeight: 700,
        color: isOk ? '#4ade80' : value === 'mock' ? '#818cf8' : '#f97316',
      }}>
        {isOk ? '✅ ' : value === 'mock' ? '🔧 ' : '⚠️ '}{value}
      </span>
    </div>
  );
}
