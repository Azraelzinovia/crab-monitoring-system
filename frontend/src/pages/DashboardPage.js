import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import toast from 'react-hot-toast';
import { Zap, RefreshCw } from 'lucide-react';
import {
  fetchStatistics, fetchCrabs, triggerDetection, getCameraStreamUrl,
} from '../api/client';

// ── Color palette ─────────────────────────────────────────────────────────────
const SPECIES_COLORS = ['#6366f1', '#14b8a6', '#f97316', '#ec4899'];
const HEALTH_COLORS = {
  'Sehat': '#22c55e', 'Kurang Sehat': '#eab308',
  'Sakit': '#ef4444', 'Mati': '#64748b', 'Unknown': '#475569',
};

export default function DashboardPage() {
  const queryClient = useQueryClient();

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['statistics'],
    queryFn: fetchStatistics,
    refetchInterval: 15000,
  });

  const { data: crabsData, isLoading: crabsLoading } = useQuery({
    queryKey: ['crabs', { page: 1, size: 15 }],
    queryFn: () => fetchCrabs({ page: 1, size: 15 }),
    refetchInterval: 10000,
  });

  const detectionMutation = useMutation({
    mutationFn: triggerDetection,
    onSuccess: (result) => {
      toast.success(result.detected
        ? `🦀 Kepiting terdeteksi! ${result.species.species} (${result.species.confidence.toFixed(1)}%)`
        : '🔍 Tidak ada kepiting terdeteksi',
        { duration: 4000 }
      );
      queryClient.invalidateQueries({ queryKey: ['statistics'] });
      queryClient.invalidateQueries({ queryKey: ['crabs'] });
    },
    onError: () => toast.error('Deteksi gagal. Coba lagi.'),
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* ── Action Bar ──────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
        <button
          onClick={() => queryClient.invalidateQueries()}
          style={btnStyle('secondary')}
        >
          <RefreshCw size={14} /> Refresh
        </button>
        <button
          onClick={() => detectionMutation.mutate()}
          disabled={detectionMutation.isPending}
          style={btnStyle('primary')}
        >
          <Zap size={14} />
          {detectionMutation.isPending ? 'Mendeteksi...' : 'Deteksi Sekarang'}
        </button>
      </div>

      {/* ── Stat Cards ──────────────────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14 }}>
        <StatCard
          title="Total Kepiting"
          value={stats?.dashboard?.total_crabs ?? '—'}
          subtitle="Semua data"
          color="accent"
          loading={statsLoading}
          icon="🦀"
        />
        <StatCard
          title="Jantan"
          value={stats?.dashboard?.male_count ?? '—'}
          subtitle="Jenis kelamin"
          color="accent"
          loading={statsLoading}
          icon="♂️"
        />
        <StatCard
          title="Betina"
          value={stats?.dashboard?.female_count ?? '—'}
          subtitle="Jenis kelamin"
          color="teal"
          loading={statsLoading}
          icon="♀️"
        />
        <StatCard
          title="Sehat"
          value={stats?.dashboard?.healthy_count ?? '—'}
          subtitle="Kondisi prima"
          color="green"
          loading={statsLoading}
          icon="💚"
        />
        <StatCard
          title="Sakit / Mati"
          value={stats?.dashboard?.sick_count ?? '—'}
          subtitle="Perlu perhatian"
          color="red"
          loading={statsLoading}
          icon="🔴"
        />
      </div>

      {/* ── Camera Feeds ────────────────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <CameraFeed cameraId={1} label="Kamera 1 — Tampak Atas" />
        <CameraFeed cameraId={2} label="Kamera 2 — Tampak Samping" />
      </div>

      {/* ── Charts ──────────────────────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <WeightChart data={stats?.weight_trend} />
        <SpeciesChart data={stats?.species_distribution} />
      </div>

      {/* ── Health Distribution ─────────────────────────────────────────────── */}
      <HealthDistributionChart data={stats?.health_distribution} />

      {/* ── Detection Table ──────────────────────────────────────────────────── */}
      <DetectionTable crabs={crabsData?.crabs || []} loading={crabsLoading} />
    </div>
  );
}

// ── Stat Card ─────────────────────────────────────────────────────────────────
function StatCard({ title, value, subtitle, color, loading, icon }) {
  return (
    <div className={`stat-card ${color}`}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: 11, color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>
            {title}
          </div>
          {loading ? (
            <div className="skeleton" style={{ width: 60, height: 32 }} />
          ) : (
            <div style={{ fontSize: 28, fontWeight: 800, color: '#f1f5f9', lineHeight: 1 }}>
              {typeof value === 'number' ? value.toLocaleString('id-ID') : value}
            </div>
          )}
          <div style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>{subtitle}</div>
        </div>
        <span style={{ fontSize: 24 }}>{icon}</span>
      </div>
    </div>
  );
}

// ── Camera Feed ───────────────────────────────────────────────────────────────
function CameraFeed({ cameraId, label }) {
  const [error, setError] = useState(false);
  const streamUrl = getCameraStreamUrl(cameraId);

  return (
    <div className="glass-card" style={{ overflow: 'hidden' }}>
      <div className="camera-feed" style={{ height: 280 }}>
        {!error ? (
          <img
            src={streamUrl}
            alt={`Camera ${cameraId}`}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            onError={() => setError(true)}
          />
        ) : (
          <div style={{
            height: '100%', display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            background: '#050a14', color: '#475569', gap: 8,
          }}>
            <span style={{ fontSize: 32 }}>📷</span>
            <div style={{ fontSize: 13 }}>Kamera Tidak Tersedia</div>
            <button onClick={() => setError(false)} style={btnStyle('secondary')}>
              <RefreshCw size={12} /> Retry
            </button>
          </div>
        )}
        <div className="camera-overlay">
          <div className="camera-badge">
            <div className="live-dot" />
            LIVE
          </div>
          <div className="camera-badge" style={{ fontSize: 11 }}>{label}</div>
        </div>
      </div>
    </div>
  );
}

// ── Weight Chart ──────────────────────────────────────────────────────────────
function WeightChart({ data }) {
  return (
    <div className="glass-card" style={{ padding: 20 }}>
      <h3 style={{ fontSize: 14, fontWeight: 700, color: '#f1f5f9', marginBottom: 16 }}>
        📈 Tren Berat Rata-rata (30 Hari)
      </h3>
      {data && data.length > 0 ? (
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="weightGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d.slice(5)} />
            <YAxis tick={{ fontSize: 10 }} unit="g" />
            <Tooltip
              formatter={(v) => [`${v}g`, 'Berat Rata-rata']}
              contentStyle={{ background: '#1e293b', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 8 }}
            />
            <Area type="monotone" dataKey="avg_weight_g" stroke="#6366f1" fill="url(#weightGrad)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      ) : (
        <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
          Belum ada data
        </div>
      )}
    </div>
  );
}

// ── Species Chart ─────────────────────────────────────────────────────────────
function SpeciesChart({ data }) {
  return (
    <div className="glass-card" style={{ padding: 20 }}>
      <h3 style={{ fontSize: 14, fontWeight: 700, color: '#f1f5f9', marginBottom: 16 }}>
        🦀 Distribusi Spesies
      </h3>
      {data && data.length > 0 ? (
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={data} cx="50%" cy="50%" innerRadius={50} outerRadius={80}
              dataKey="count" paddingAngle={3}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={SPECIES_COLORS[i % SPECIES_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(v, n) => [v, n]}
              contentStyle={{ background: '#1e293b', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 8 }}
            />
            <Legend formatter={(v) => <span style={{ fontSize: 11, color: '#94a3b8' }}>{v}</span>} />
          </PieChart>
        </ResponsiveContainer>
      ) : (
        <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
          Belum ada data
        </div>
      )}
    </div>
  );
}

// ── Health Distribution Chart ─────────────────────────────────────────────────
function HealthDistributionChart({ data }) {
  return (
    <div className="glass-card" style={{ padding: 20 }}>
      <h3 style={{ fontSize: 14, fontWeight: 700, color: '#f1f5f9', marginBottom: 16 }}>
        ❤️ Distribusi Kondisi Kesehatan
      </h3>
      {data && data.length > 0 ? (
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={data} layout="vertical" barSize={20}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 10 }} />
            <YAxis type="category" dataKey="health_status" tick={{ fontSize: 11 }} width={100} />
            <Tooltip
              contentStyle={{ background: '#1e293b', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 8 }}
            />
            <Bar dataKey="count" radius={[0, 4, 4, 0]}>
              {data.map((entry, i) => (
                <Cell key={i} fill={HEALTH_COLORS[entry.health_status] || '#6366f1'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <div style={{ height: 160, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
          Belum ada data
        </div>
      )}
    </div>
  );
}

// ── Detection Table ───────────────────────────────────────────────────────────
function DetectionTable({ crabs, loading }) {
  return (
    <div className="glass-card" style={{ overflow: 'hidden' }}>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid rgba(99,102,241,0.1)' }}>
        <h3 style={{ fontSize: 14, fontWeight: 700, color: '#f1f5f9' }}>
          📋 Tabel Deteksi Terbaru
        </h3>
      </div>
      <div style={{ overflowX: 'auto', maxHeight: 420, overflowY: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Waktu</th>
              <th>Spesies</th>
              <th>Jenis Kelamin</th>
              <th>Kesehatan</th>
              <th>Berat</th>
              <th>Panjang</th>
              <th>Lebar</th>
              <th>Conf.</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 9 }).map((_, j) => (
                    <td key={j}><div className="skeleton" style={{ height: 16, width: '80%' }} /></td>
                  ))}
                </tr>
              ))
            ) : crabs.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: 40, color: '#64748b' }}>
                  Belum ada data deteksi
                </td>
              </tr>
            ) : (
              crabs.map((crab) => (
                <tr key={crab.id}>
                  <td style={{ fontFamily: 'monospace', color: '#818cf8' }}>#{crab.id}</td>
                  <td style={{ fontSize: 11, color: '#64748b' }}>
                    {new Date(crab.timestamp).toLocaleString('id-ID')}
                  </td>
                  <td style={{ fontWeight: 600 }}>{crab.species || '—'}</td>
                  <td>
                    <span className={`badge badge-${crab.gender?.toLowerCase() || 'unknown'}`}>
                      {crab.gender === 'Jantan' ? '♂' : crab.gender === 'Betina' ? '♀' : '?'} {crab.gender || '—'}
                    </span>
                  </td>
                  <td>
                    <HealthBadge status={crab.health_status} />
                  </td>
                  <td style={{ fontFamily: 'monospace' }}>{crab.weight_g ? `${crab.weight_g}g` : '—'}</td>
                  <td style={{ fontFamily: 'monospace' }}>{crab.length_cm ? `${crab.length_cm}cm` : '—'}</td>
                  <td style={{ fontFamily: 'monospace' }}>{crab.width_cm ? `${crab.width_cm}cm` : '—'}</td>
                  <td>
                    <ConfidenceBar value={crab.detection_confidence * 100} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function HealthBadge({ status }) {
  const classMap = {
    'Sehat': 'sehat', 'Kurang Sehat': 'kurang-sehat',
    'Sakit': 'sakit', 'Mati': 'mati',
  };
  const emojiMap = {
    'Sehat': '✅', 'Kurang Sehat': '⚠️', 'Sakit': '🔴', 'Mati': '⚫',
  };
  return (
    <span className={`badge badge-${classMap[status] || 'mati'}`}>
      {emojiMap[status] || '?'} {status || '—'}
    </span>
  );
}

function ConfidenceBar({ value }) {
  const color = value >= 80 ? '#22c55e' : value >= 60 ? '#eab308' : '#ef4444';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div className="confidence-bar" style={{ width: 50 }}>
        <div className="confidence-fill" style={{ width: `${value}%`, background: color }} />
      </div>
      <span style={{ fontSize: 10, fontFamily: 'monospace', color: '#94a3b8' }}>
        {value.toFixed(0)}%
      </span>
    </div>
  );
}

// ── Button styles ─────────────────────────────────────────────────────────────
function btnStyle(variant) {
  const base = {
    display: 'inline-flex', alignItems: 'center', gap: 6,
    padding: '8px 16px', borderRadius: 8, fontSize: 13,
    fontWeight: 600, cursor: 'pointer', border: 'none',
    transition: 'all 0.2s',
  };
  if (variant === 'primary') return {
    ...base, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    color: '#fff', boxShadow: '0 4px 15px rgba(99,102,241,0.3)',
  };
  return {
    ...base, background: 'rgba(99,102,241,0.1)', color: '#94a3b8',
    border: '1px solid rgba(99,102,241,0.2)',
  };
}
