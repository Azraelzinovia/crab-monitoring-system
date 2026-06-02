import React, { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import toast from 'react-hot-toast';
import { Zap, RefreshCw } from 'lucide-react';
import { triggerDetection, getCameraStreamUrl } from '../api/client';
import { useStatistics, useCrabs } from '../hooks/useApi';

const SPECIES_COLORS = ['#6366f1', '#14b8a6', '#f97316', '#ec4899'];
const HEALTH_COLORS  = {
  'Sehat':'#22c55e','Kurang Sehat':'#eab308','Sakit':'#ef4444','Mati':'#64748b','Unknown':'#475569',
};

export default function DashboardPage() {
  const qc = useQueryClient();
  const { data: stats, isLoading: statsLoading } = useStatistics();
  const { data: crabsData, isLoading: crabsLoading } = useCrabs({ page:1, size:15 });

  const detectionMutation = useMutation({
    mutationFn: triggerDetection,
    onSuccess: (r) => {
      toast.success(r.detected
        ? `🦀 ${r.species.species} terdeteksi! (${r.species.confidence.toFixed(1)}%)`
        : '🔍 Tidak ada kepiting terdeteksi', { duration: 4000 });
      qc.invalidateQueries({ queryKey: ['statistics'] });
      qc.invalidateQueries({ queryKey: ['crabs'] });
    },
    onError: () => toast.error('Backend belum aktif — menampilkan data demo'),
  });

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:20 }}>
      {/* Demo banner */}
      <DemoBanner />

      {/* Action bar */}
      <div style={{ display:'flex', justifyContent:'flex-end', gap:10 }}>
        <button onClick={() => qc.invalidateQueries()} style={btn('secondary')}>
          <RefreshCw size={14}/> Refresh
        </button>
        <button onClick={() => detectionMutation.mutate()} disabled={detectionMutation.isPending} style={btn('primary')}>
          <Zap size={14}/>
          {detectionMutation.isPending ? 'Mendeteksi...' : 'Deteksi Sekarang'}
        </button>
      </div>

      {/* Stat cards */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(5,1fr)', gap:14 }}>
        {[
          { title:'Total Kepiting', value:stats?.dashboard?.total_crabs,     icon:'🦀', color:'accent'  },
          { title:'Jantan',         value:stats?.dashboard?.male_count,       icon:'♂️', color:'accent'  },
          { title:'Betina',         value:stats?.dashboard?.female_count,     icon:'♀️', color:'teal'    },
          { title:'Sehat',          value:stats?.dashboard?.healthy_count,    icon:'💚', color:'green'   },
          { title:'Sakit / Mati',   value:stats?.dashboard?.sick_count,       icon:'🔴', color:'red'     },
        ].map(c => <StatCard key={c.title} {...c} loading={statsLoading} />)}
      </div>

      {/* Camera feeds */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
        <CameraFeed id={1} label="Tampak Atas"    />
        <CameraFeed id={2} label="Tampak Samping" />
      </div>

      {/* Charts */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
        <WeightChart  data={stats?.weight_trend}         />
        <SpeciesChart data={stats?.species_distribution} />
      </div>
      <HealthChart data={stats?.health_distribution} />

      {/* Table */}
      <DetectionTable crabs={crabsData?.crabs || []} loading={crabsLoading} />
    </div>
  );
}

/* ── Demo Banner ──────────────────────────────────────────────────────────── */
function DemoBanner() {
  const [hidden, setHidden] = React.useState(false);
  if (hidden) return null;
  return (
    <div style={{
      padding:'12px 16px', borderRadius:10,
      background:'rgba(99,102,241,0.1)',
      border:'1px solid rgba(99,102,241,0.3)',
      display:'flex', alignItems:'center', justifyContent:'space-between', gap:12,
    }}>
      <div style={{ fontSize:13, color:'#a5b4fc' }}>
        <strong>🔧 Demo Mode</strong> — Dashboard menampilkan data contoh.
        Untuk data nyata, jalankan FastAPI backend &amp; sambungkan Raspberry Pi.
      </div>
      <button onClick={() => setHidden(true)}
        style={{ background:'none', border:'none', color:'#64748b', cursor:'pointer', fontSize:16 }}>✕</button>
    </div>
  );
}

/* ── Stat Card ────────────────────────────────────────────────────────────── */
function StatCard({ title, value, icon, color, loading }) {
  return (
    <div className={`stat-card ${color}`}>
      <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between' }}>
        <div>
          <div style={{ fontSize:11, color:'#64748b', fontWeight:600, textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:6 }}>{title}</div>
          {loading
            ? <div className="skeleton" style={{ width:60, height:32 }} />
            : <div style={{ fontSize:28, fontWeight:800, color:'#f1f5f9', lineHeight:1 }}>
                {typeof value === 'number' ? value.toLocaleString('id-ID') : '—'}
              </div>}
        </div>
        <span style={{ fontSize:24 }}>{icon}</span>
      </div>
    </div>
  );
}

/* ── Camera Feed ──────────────────────────────────────────────────────────── */
function CameraFeed({ id, label }) {
  const [err, setErr] = React.useState(false);
  return (
    <div className="glass-card" style={{ overflow:'hidden' }}>
      <div className="camera-feed" style={{ height:260 }}>
        {!err
          ? <img src={getCameraStreamUrl(id)} alt={`Cam${id}`}
              style={{ width:'100%', height:'100%', objectFit:'cover' }}
              onError={() => setErr(true)} />
          : <div style={{ height:'100%', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', background:'#050a14', gap:8, color:'#475569' }}>
              <span style={{ fontSize:40 }}>📷</span>
              <div style={{ fontSize:12 }}>Kamera {id} — Tidak Terhubung</div>
              <div style={{ fontSize:10, color:'#334155' }}>Backend belum aktif (Demo Mode)</div>
            </div>}
        <div className="camera-overlay">
          <div className="camera-badge"><div className="live-dot"/>LIVE</div>
          <div className="camera-badge">📷 {label}</div>
        </div>
      </div>
    </div>
  );
}

/* ── Charts ───────────────────────────────────────────────────────────────── */
function WeightChart({ data }) {
  return (
    <div className="glass-card" style={{ padding:20 }}>
      <h3 style={{ fontSize:14, fontWeight:700, color:'#f1f5f9', marginBottom:16 }}>📈 Tren Berat Rata-rata</h3>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data || []}>
          <defs>
            <linearGradient id="wg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3"/>
          <XAxis dataKey="date" tick={{ fontSize:9 }} tickFormatter={d=>d.slice(5)}/>
          <YAxis tick={{ fontSize:9 }} unit="g"/>
          <Tooltip formatter={v=>[`${v.toFixed(0)}g`,'Berat']}
            contentStyle={{ background:'#1e293b', border:'1px solid rgba(99,102,241,0.3)', borderRadius:8 }}/>
          <Area type="monotone" dataKey="avg_weight_g" stroke="#6366f1" fill="url(#wg)" strokeWidth={2}/>
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function SpeciesChart({ data }) {
  return (
    <div className="glass-card" style={{ padding:20 }}>
      <h3 style={{ fontSize:14, fontWeight:700, color:'#f1f5f9', marginBottom:16 }}>🥧 Distribusi Spesies</h3>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie data={data||[]} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="count" paddingAngle={3} nameKey="species">
            {(data||[]).map((_,i) => <Cell key={i} fill={SPECIES_COLORS[i%4]}/>)}
          </Pie>
          <Tooltip contentStyle={{ background:'#1e293b', border:'1px solid rgba(99,102,241,0.3)', borderRadius:8 }}/>
          <Legend formatter={v=><span style={{ fontSize:11,color:'#94a3b8' }}>{v}</span>}/>
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

function HealthChart({ data }) {
  return (
    <div className="glass-card" style={{ padding:20 }}>
      <h3 style={{ fontSize:14, fontWeight:700, color:'#f1f5f9', marginBottom:16 }}>❤️ Distribusi Kesehatan</h3>
      <ResponsiveContainer width="100%" height={150}>
        <BarChart data={data||[]} layout="vertical" barSize={18}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false}/>
          <XAxis type="number" tick={{ fontSize:10 }}/>
          <YAxis type="category" dataKey="health_status" tick={{ fontSize:11 }} width={100}/>
          <Tooltip contentStyle={{ background:'#1e293b', border:'1px solid rgba(99,102,241,0.3)', borderRadius:8 }}/>
          <Bar dataKey="count" radius={[0,4,4,0]}>
            {(data||[]).map((e,i)=><Cell key={i} fill={HEALTH_COLORS[e.health_status]||'#6366f1'}/>)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/* ── Detection Table ──────────────────────────────────────────────────────── */
function DetectionTable({ crabs, loading }) {
  const HC = { 'Sehat':'sehat','Kurang Sehat':'kurang-sehat','Sakit':'sakit','Mati':'mati' };
  const HE = { 'Sehat':'✅','Kurang Sehat':'⚠️','Sakit':'🔴','Mati':'⚫' };
  return (
    <div className="glass-card" style={{ overflow:'hidden' }}>
      <div style={{ padding:'16px 20px', borderBottom:'1px solid rgba(99,102,241,0.1)' }}>
        <h3 style={{ fontSize:14, fontWeight:700, color:'#f1f5f9' }}>📋 Tabel Deteksi Terbaru</h3>
      </div>
      <div style={{ overflowX:'auto', maxHeight:420, overflowY:'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th><th>Waktu</th><th>Spesies</th><th>Kelamin</th>
              <th>Kesehatan</th><th>Berat</th><th>Panjang</th><th>Lebar</th><th>Conf.</th>
            </tr>
          </thead>
          <tbody>
            {loading
              ? Array.from({length:5}).map((_,i)=>(
                  <tr key={i}>{Array.from({length:9}).map((_,j)=>(
                    <td key={j}><div className="skeleton" style={{height:14,width:'80%'}}/></td>
                  ))}</tr>))
              : crabs.length === 0
                ? <tr><td colSpan={9} style={{textAlign:'center',padding:40,color:'#64748b'}}>Belum ada data</td></tr>
                : crabs.map(c=>(
                  <tr key={c.id}>
                    <td style={{fontFamily:'monospace',color:'#818cf8'}}>#{c.id}</td>
                    <td style={{fontSize:11,color:'#64748b'}}>{new Date(c.timestamp).toLocaleString('id-ID')}</td>
                    <td style={{fontWeight:600}}>{c.species}</td>
                    <td>
                      <span className={`badge badge-${c.gender?.toLowerCase()}`}>
                        {c.gender==='Jantan'?'♂':'♀'} {c.gender}
                      </span>
                    </td>
                    <td><span className={`badge badge-${HC[c.health_status]||'mati'}`}>{HE[c.health_status]} {c.health_status}</span></td>
                    <td style={{fontFamily:'monospace'}}>{c.weight_g?`${c.weight_g}g`:'—'}</td>
                    <td style={{fontFamily:'monospace'}}>{c.length_cm?`${c.length_cm}cm`:'—'}</td>
                    <td style={{fontFamily:'monospace'}}>{c.width_cm?`${c.width_cm}cm`:'—'}</td>
                    <td>
                      <div style={{display:'flex',alignItems:'center',gap:5}}>
                        <div style={{width:40,height:4,background:'rgba(255,255,255,0.1)',borderRadius:2,overflow:'hidden'}}>
                          <div style={{height:'100%',width:`${c.detection_confidence*100}%`,
                            background: c.detection_confidence > 0.8 ? '#22c55e' : '#eab308',
                            borderRadius:2, transition:'width 0.5s'}}/>
                        </div>
                        <span style={{fontSize:10,fontFamily:'monospace',color:'#94a3b8'}}>
                          {(c.detection_confidence*100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                  </tr>
                ))
            }
          </tbody>
        </table>
      </div>
    </div>
  );
}

function btn(v) {
  const base = { display:'inline-flex', alignItems:'center', gap:6, padding:'8px 16px',
    borderRadius:8, fontSize:13, fontWeight:600, cursor:'pointer', border:'none' };
  return v==='primary'
    ? { ...base, background:'linear-gradient(135deg,#6366f1,#8b5cf6)', color:'#fff', boxShadow:'0 4px 15px rgba(99,102,241,0.3)' }
    : { ...base, background:'rgba(99,102,241,0.1)', color:'#94a3b8', border:'1px solid rgba(99,102,241,0.2)' };
}
