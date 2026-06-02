import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchCrabs } from '../api/client';

export default function HealthPage() {
  const [filter, setFilter] = useState('all');
  const healthFilter = filter !== 'all' ? filter : undefined;

  const { data, isLoading } = useQuery({
    queryKey: ['crabs', { page: 1, size: 50, health_status: healthFilter }],
    queryFn: () => fetchCrabs({ page: 1, size: 50, health_status: healthFilter }),
    refetchInterval: 15000,
  });

  const crabs = data?.crabs || [];

  const FILTERS = [
    { value: 'all', label: 'Semua', color: '#6366f1' },
    { value: 'Sehat', label: 'Sehat', color: '#22c55e' },
    { value: 'Kurang Sehat', label: 'Kurang Sehat', color: '#eab308' },
    { value: 'Sakit', label: 'Sakit', color: '#ef4444' },
    { value: 'Mati', label: 'Mati', color: '#64748b' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="glass-card" style={{ padding: 20 }}>
        <h2 style={{ fontSize: 16, fontWeight: 700, color: '#f1f5f9' }}>
          Monitoring Kesehatan Kepiting
        </h2>
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {FILTERS.map(f => (
          <button key={f.value} onClick={() => setFilter(f.value)} style={{
            padding: '7px 16px', borderRadius: 20, fontSize: 12, fontWeight: 600,
            cursor: 'pointer',
            border: `1px solid ${filter === f.value ? f.color : 'rgba(255,255,255,0.1)'}`,
            background: filter === f.value ? `${f.color}20` : 'rgba(99,102,241,0.05)',
            color: filter === f.value ? f.color : '#64748b',
          }}>{f.label}</button>
        ))}
      </div>

      {isLoading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14 }}>
          {[...Array(6)].map((_,i) => (
            <div key={i} className="glass-card" style={{ padding: 20 }}>
              <div className="skeleton" style={{ height: 80 }} />
            </div>
          ))}
        </div>
      ) : crabs.length === 0 ? (
        <div className="glass-card" style={{ padding: 60, textAlign: 'center', color: '#64748b' }}>
          Tidak ada data untuk filter ini
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14 }}>
          {crabs.map(crab => <HealthCard key={crab.id} crab={crab} />)}
        </div>
      )}
    </div>
  );
}

const HEALTH_THEME = {
  'Sehat':        { bg: 'rgba(34,197,94,0.08)',  border: 'rgba(34,197,94,0.25)',  text: '#4ade80', emoji: '✅' },
  'Kurang Sehat': { bg: 'rgba(234,179,8,0.08)',  border: 'rgba(234,179,8,0.25)',  text: '#facc15', emoji: '⚠️' },
  'Sakit':        { bg: 'rgba(239,68,68,0.08)',  border: 'rgba(239,68,68,0.25)',  text: '#f87171', emoji: '🔴' },
  'Mati':         { bg: 'rgba(100,116,139,0.08)',border: 'rgba(100,116,139,0.25)',text: '#94a3b8', emoji: '⚫' },
};

function HealthCard({ crab }) {
  const t = HEALTH_THEME[crab.health_status] || HEALTH_THEME['Mati'];
  return (
    <div style={{
      background: t.bg, border: `1px solid ${t.border}`,
      borderRadius: 14, padding: 18,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
        <div>
          <div style={{ fontSize: 11, fontFamily: 'monospace', color: '#64748b' }}>#{crab.id}</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#f1f5f9' }}>{crab.species || 'Unknown'}</div>
        </div>
        <span style={{ fontSize: 22 }}>{t.emoji}</span>
      </div>
      <div style={{ fontSize: 13, fontWeight: 700, color: t.text, marginBottom: 10 }}>
        {crab.health_status} ({crab.health_confidence?.toFixed(1)}%)
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
        {[
          ['Kelamin', crab.gender],
          ['Berat', crab.weight_g ? `${crab.weight_g}g` : '—'],
          ['Capit Kiri', crab.left_claw ? '✅' : '❌'],
          ['Capit Kanan', crab.right_claw ? '✅' : '❌'],
        ].map(([label, value]) => (
          <div key={label} style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 6, padding: '5px 8px' }}>
            <div style={{ fontSize: 9, color: '#64748b' }}>{label}</div>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#cbd5e1' }}>{value}</div>
          </div>
        ))}
      </div>
      <div style={{ fontSize: 10, color: '#475569', marginTop: 10 }}>
        {new Date(crab.timestamp).toLocaleString('id-ID')}
      </div>
    </div>
  );
}
