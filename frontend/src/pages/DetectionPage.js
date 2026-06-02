import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { Zap, Camera, Clock } from 'lucide-react';
import { triggerDetection, fetchDetectionStatus, getCameraStreamUrl, getSnapshotUrl } from '../api/client';

export default function DetectionPage() {
  const [lastResult, setLastResult] = useState(null);
  const [autoDetect, setAutoDetect] = useState(false);
  const queryClient = useQueryClient();

  const { data: status } = useQuery({
    queryKey: ['detectStatus'],
    queryFn: fetchDetectionStatus,
    refetchInterval: 10000,
  });

  const mutation = useMutation({
    mutationFn: triggerDetection,
    onSuccess: (result) => {
      setLastResult(result);
      toast.success(result.detected
        ? `✅ ${result.species.species} terdeteksi!`
        : '🔍 Tidak ada kepiting', { duration: 3000 }
      );
      queryClient.invalidateQueries({ queryKey: ['statistics'] });
      queryClient.invalidateQueries({ queryKey: ['crabs'] });
    },
    onError: () => toast.error('Deteksi gagal'),
  });

  React.useEffect(() => {
    if (!autoDetect) return;
    const interval = setInterval(() => mutation.mutate(), 3000);
    return () => clearInterval(interval);
  }, [autoDetect]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Controls */}
      <div className="glass-card" style={{ padding: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: '#f1f5f9' }}>Kontrol Deteksi</h2>
            <p style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
              Jalankan AI pipeline secara manual atau otomatis
            </p>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button
              onClick={() => setAutoDetect(v => !v)}
              style={{
                padding: '8px 16px', borderRadius: 8, fontSize: 13, fontWeight: 600,
                cursor: 'pointer', border: '1px solid rgba(99,102,241,0.3)',
                background: autoDetect ? 'rgba(99,102,241,0.3)' : 'rgba(99,102,241,0.08)',
                color: autoDetect ? '#a5b4fc' : '#94a3b8',
              }}
            >
              {autoDetect ? '⏸ Stop Auto' : '▶️ Auto Detect'}
            </button>
            <button
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 6,
                padding: '8px 20px', borderRadius: 8, fontSize: 13, fontWeight: 700,
                cursor: 'pointer', border: 'none',
                background: mutation.isPending
                  ? 'rgba(99,102,241,0.4)'
                  : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                color: '#fff', boxShadow: '0 4px 15px rgba(99,102,241,0.3)',
              }}
            >
              <Zap size={14} />
              {mutation.isPending ? 'Mendeteksi...' : 'Deteksi Sekarang'}
            </button>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Camera feeds */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {[1, 2].map(id => (
            <div key={id} className="glass-card" style={{ overflow: 'hidden' }}>
              <div className="camera-feed" style={{ height: 220 }}>
                <img
                  src={getCameraStreamUrl(id)}
                  alt={`Camera ${id}`}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
                <div className="camera-overlay">
                  <div className="camera-badge"><div className="live-dot" />LIVE</div>
                  <div className="camera-badge">
                    <Camera size={10} />
                    {id === 1 ? 'Tampak Atas' : 'Tampak Samping'}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Result Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {lastResult ? (
            <DetectionResultPanel result={lastResult} />
          ) : (
            <div className="glass-card" style={{
              padding: 40, display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center', gap: 12, height: '100%',
            }}>
              <span style={{ fontSize: 48 }}>🎯</span>
              <div style={{ color: '#64748b', fontSize: 14, textAlign: 'center' }}>
                Tekan tombol "Deteksi Sekarang" untuk memulai analisis
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Model Status */}
      {status && <ModelStatusPanel status={status} />}
    </div>
  );
}

function DetectionResultPanel({ result }) {
  const detected = result.detected;
  return (
    <div className={`glass-card ${detected ? 'detection-active' : ''}`} style={{ padding: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
        <span style={{ fontSize: 24 }}>{detected ? '🦀' : '❌'}</span>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#f1f5f9' }}>
            {detected ? 'Kepiting Terdeteksi!' : 'Tidak Ada Kepiting'}
          </div>
          <div style={{ fontSize: 11, color: '#64748b', display: 'flex', gap: 6, alignItems: 'center' }}>
            <Clock size={10} />
            {new Date(result.timestamp).toLocaleString('id-ID')}
          </div>
        </div>
      </div>

      {detected && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <ResultRow icon="🔬" label="Spesies" value={result.species.species} conf={result.species.confidence} />
          <ResultRow icon={result.gender.gender === 'Jantan' ? '♂️' : '♀️'} label="Jenis Kelamin" value={result.gender.gender} conf={result.gender.confidence} />
          <ResultRow icon="❤️" label="Kesehatan" value={result.health.health_status} conf={result.health.confidence} />
          <div style={{ borderTop: '1px solid rgba(99,102,241,0.1)', paddingTop: 12, marginTop: 4 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#94a3b8', marginBottom: 8 }}>PENGUKURAN</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
              <MeasureBox label="Panjang" value={result.measurements.length_cm} unit="cm" />
              <MeasureBox label="Lebar" value={result.measurements.width_cm} unit="cm" />
              <MeasureBox label="Berat" value={result.measurements.estimated_weight_g} unit="g" />
            </div>
          </div>
          <div style={{ borderTop: '1px solid rgba(99,102,241,0.1)', paddingTop: 12 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#94a3b8', marginBottom: 8 }}>KELENGKAPAN ORGAN</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
              <OrganStatus label="Capit Kiri" ok={result.body_parts.left_claw} />
              <OrganStatus label="Capit Kanan" ok={result.body_parts.right_claw} />
              <OrganStatus label="Kaki Lengkap" ok={result.body_parts.legs_complete} />
              <OrganStatus label="Cangkang" ok={!result.body_parts.shell_damage} okLabel="Normal" failLabel="Rusak" />
            </div>
          </div>
          <div style={{ fontSize: 11, color: '#475569', textAlign: 'right' }}>
            Inference: {result.inference_time_ms?.toFixed(1)}ms |
            Total: {result.total_processing_time_ms?.toFixed(1)}ms
          </div>
        </div>
      )}
    </div>
  );
}

function ResultRow({ icon, label, value, conf }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <span>{icon}</span>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 11, color: '#64748b' }}>{label}</div>
        <div style={{ fontSize: 14, fontWeight: 700, color: '#f1f5f9' }}>{value}</div>
      </div>
      <div style={{ textAlign: 'right' }}>
        <div style={{ fontSize: 11, color: '#94a3b8' }}>Confidence</div>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#6366f1' }}>{conf?.toFixed(1)}%</div>
      </div>
    </div>
  );
}

function MeasureBox({ label, value, unit }) {
  return (
    <div style={{
      background: 'rgba(99,102,241,0.08)', borderRadius: 8,
      padding: '8px 10px', textAlign: 'center',
      border: '1px solid rgba(99,102,241,0.15)',
    }}>
      <div style={{ fontSize: 10, color: '#64748b', marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 800, color: '#a5b4fc' }}>
        {value != null ? `${value}${unit}` : '—'}
      </div>
    </div>
  );
}

function OrganStatus({ label, ok, okLabel = 'Ada', failLabel = 'Tidak Ada' }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6, fontSize: 12,
      color: ok ? '#4ade80' : '#f87171',
    }}>
      <span>{ok ? '✅' : '❌'}</span>
      <span>{label}: <strong>{ok ? okLabel : failLabel}</strong></span>
    </div>
  );
}

function ModelStatusPanel({ status }) {
  return (
    <div className="glass-card" style={{ padding: 20 }}>
      <h3 style={{ fontSize: 14, fontWeight: 700, color: '#f1f5f9', marginBottom: 14 }}>
        🤖 Status AI Models
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 10 }}>
        {Object.entries(status.models || {}).map(([model, stat]) => (
          <div key={model} style={{
            padding: '10px 12px', borderRadius: 8,
            background: stat === 'loaded' ? 'rgba(34,197,94,0.08)' : 'rgba(99,102,241,0.08)',
            border: `1px solid ${stat === 'loaded' ? 'rgba(34,197,94,0.2)' : 'rgba(99,102,241,0.15)'}`,
          }}>
            <div style={{ fontSize: 10, color: '#64748b', marginBottom: 2 }}>
              {model.replace(/_/g, ' ').toUpperCase()}
            </div>
            <div style={{ fontSize: 12, fontWeight: 700, color: stat === 'loaded' ? '#4ade80' : '#818cf8' }}>
              {stat === 'loaded' ? '✅ Loaded' : '🔧 Mock Mode'}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
