import React, { useState } from 'react';
import { useCrabs } from '../hooks/useApi';

const HEALTH_THEME = {
  'Sehat':        { bg:'rgba(34,197,94,0.08)',   border:'rgba(34,197,94,0.25)',   text:'#4ade80', emoji:'✅' },
  'Kurang Sehat': { bg:'rgba(234,179,8,0.08)',   border:'rgba(234,179,8,0.25)',   text:'#facc15', emoji:'⚠️' },
  'Sakit':        { bg:'rgba(239,68,68,0.08)',   border:'rgba(239,68,68,0.25)',   text:'#f87171', emoji:'🔴' },
  'Mati':         { bg:'rgba(100,116,139,0.08)', border:'rgba(100,116,139,0.25)',text:'#94a3b8', emoji:'⚫' },
};

const FILTERS = [
  { value:'all',           label:'Semua',        color:'#6366f1' },
  { value:'Sehat',         label:'✅ Sehat',      color:'#22c55e' },
  { value:'Kurang Sehat',  label:'⚠️ Kurang Sehat', color:'#eab308' },
  { value:'Sakit',         label:'🔴 Sakit',     color:'#ef4444' },
  { value:'Mati',          label:'⚫ Mati',      color:'#64748b' },
];

export default function HealthPage() {
  const [filter, setFilter] = useState('all');
  const healthFilter = filter !== 'all' ? filter : undefined;

  const { data, isLoading } = useCrabs({ page:1, size:60, health_status: healthFilter });
  const crabs = data?.crabs || [];

  // Hitung summary dari data yang ada
  const all = data?.crabs || [];
  const summary = {
    total:   all.length,
    sehat:   all.filter(c=>c.health_status==='Sehat').length,
    kurang:  all.filter(c=>c.health_status==='Kurang Sehat').length,
    sakit:   all.filter(c=>c.health_status==='Sakit').length,
    mati:    all.filter(c=>c.health_status==='Mati').length,
  };

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:20 }}>
      {/* Header */}
      <div className="glass-card" style={{ padding:20 }}>
        <h2 style={{ fontSize:16, fontWeight:700, color:'#f1f5f9', marginBottom:4 }}>
          ❤️ Monitoring Kesehatan Kepiting
        </h2>
        <p style={{ fontSize:12, color:'#64748b' }}>Pantau kondisi kesehatan seluruh kepiting secara real-time</p>
      </div>

      {/* Quick stats */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(5,1fr)', gap:10 }}>
        {[
          ['Total',       summary.total,  '#6366f1'],
          ['Sehat',       summary.sehat,  '#22c55e'],
          ['Kurang Sehat',summary.kurang, '#eab308'],
          ['Sakit',       summary.sakit,  '#ef4444'],
          ['Mati',        summary.mati,   '#64748b'],
        ].map(([label,count,color])=>(
          <div key={label} style={{ padding:'14px 16px', borderRadius:12,
            background:`${color}10`, border:`1px solid ${color}30`, textAlign:'center' }}>
            <div style={{ fontSize:22, fontWeight:800, color }}>{count}</div>
            <div style={{ fontSize:11, color:'#64748b', marginTop:2 }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
        {FILTERS.map(f=>(
          <button key={f.value} onClick={()=>setFilter(f.value)} style={{
            padding:'7px 16px', borderRadius:20, fontSize:12, fontWeight:600,
            cursor:'pointer',
            border:`1px solid ${filter===f.value ? f.color : 'rgba(255,255,255,0.1)'}`,
            background: filter===f.value ? `${f.color}20` : 'rgba(99,102,241,0.05)',
            color: filter===f.value ? f.color : '#64748b',
            transition:'all 0.2s',
          }}>{f.label} {filter===f.value && crabs.length > 0 ? `(${crabs.length})` : ''}</button>
        ))}
      </div>

      {/* Cards grid */}
      {isLoading ? (
        <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:14 }}>
          {[...Array(6)].map((_,i)=>(
            <div key={i} className="glass-card" style={{ padding:20 }}>
              <div className="skeleton" style={{ height:160 }}/>
            </div>
          ))}
        </div>
      ) : crabs.length === 0 ? (
        <div className="glass-card" style={{ padding:60, textAlign:'center', color:'#64748b' }}>
          <div style={{ fontSize:40, marginBottom:12 }}>🦀</div>
          <div>Tidak ada kepiting dengan status "{filter}"</div>
        </div>
      ) : (
        <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:14 }}>
          {crabs.map(crab => <HealthCard key={crab.id} crab={crab}/>)}
        </div>
      )}
    </div>
  );
}

function HealthCard({ crab }) {
  const t = HEALTH_THEME[crab.health_status] || HEALTH_THEME['Mati'];
  return (
    <div style={{ background:t.bg, border:`1px solid ${t.border}`, borderRadius:14, padding:18,
      transition:'transform 0.2s, box-shadow 0.2s' }}
      onMouseEnter={e=>{e.currentTarget.style.transform='translateY(-2px)';e.currentTarget.style.boxShadow='0 8px 24px rgba(0,0,0,0.3)'}}
      onMouseLeave={e=>{e.currentTarget.style.transform='none';e.currentTarget.style.boxShadow='none'}}>

      {/* Header */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:10 }}>
        <div>
          <div style={{ fontSize:10, fontFamily:'monospace', color:'#64748b' }}>#{crab.id}</div>
          <div style={{ fontSize:14, fontWeight:700, color:'#f1f5f9', marginTop:2 }}>{crab.species}</div>
        </div>
        <span style={{ fontSize:22 }}>{t.emoji}</span>
      </div>

      {/* Health status */}
      <div style={{ marginBottom:12 }}>
        <span style={{ fontSize:13, fontWeight:700, color:t.text }}>{crab.health_status}</span>
        {crab.health_confidence > 0 && (
          <span style={{ fontSize:11, color:'#64748b', marginLeft:6 }}>
            ({crab.health_confidence.toFixed(1)}%)
          </span>
        )}
        {/* Confidence bar */}
        <div style={{ height:3, background:'rgba(255,255,255,0.08)', borderRadius:2, marginTop:4, overflow:'hidden' }}>
          <div style={{ height:'100%', borderRadius:2, background:t.text,
            width:`${crab.health_confidence||0}%`, transition:'width 0.5s' }}/>
        </div>
      </div>

      {/* Details grid */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:5 }}>
        {[
          ['Kelamin',    crab.gender],
          ['Berat',      crab.weight_g ? `${crab.weight_g}g` : '—'],
          ['Panjang',    crab.length_cm ? `${crab.length_cm}cm` : '—'],
          ['Capit Kiri', crab.left_claw ? '✅' : '❌'],
          ['Capit Kanan',crab.right_claw ? '✅' : '❌'],
          ['Cangkang',   crab.shell_damage ? '❌ Rusak' : '✅ Normal'],
        ].map(([label,value])=>(
          <div key={label} style={{ background:'rgba(0,0,0,0.15)', borderRadius:6, padding:'5px 8px' }}>
            <div style={{ fontSize:9, color:'#64748b', textTransform:'uppercase' }}>{label}</div>
            <div style={{ fontSize:12, fontWeight:600, color:'#cbd5e1', marginTop:1 }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Timestamp */}
      <div style={{ fontSize:10, color:'#475569', marginTop:10, textAlign:'right' }}>
        {new Date(crab.timestamp).toLocaleString('id-ID',{dateStyle:'short',timeStyle:'short'})}
      </div>
    </div>
  );
}
