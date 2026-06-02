import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSystemHealth, useSystemResources, getMockStatistics } from '../hooks/useApi';

export default function SettingsPage() {
  const { data: health }     = useSystemHealth();
  const { data: resources }  = useSystemResources();

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:20 }}>
      <div className="glass-card" style={{ padding:20 }}>
        <h2 style={{ fontSize:16, fontWeight:700, color:'#f1f5f9' }}>⚙️ Pengaturan &amp; Status Sistem</h2>
        <p style={{ fontSize:12, color:'#64748b', marginTop:4 }}>
          Monitor resource Raspberry Pi 5 dan konfigurasi sistem
        </p>
      </div>

      {/* Resource Gauges */}
      {resources && (
        <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:14 }}>
          <ResourceGauge label="CPU" icon="🖥️"
            percent={resources.cpu?.percent}
            sub1={`${resources.cpu?.cores} cores`}
            sub2={resources.cpu?.temperature_c ? `🌡️ ${resources.cpu.temperature_c}°C` : null}/>
          <ResourceGauge label="RAM" icon="💾"
            percent={resources.memory?.percent}
            sub1={`${resources.memory?.used_gb?.toFixed(1)} / ${resources.memory?.total_gb?.toFixed(1)} GB`}/>
          <ResourceGauge label="Disk" icon="💿"
            percent={resources.disk?.percent}
            sub1={`${resources.disk?.free_gb?.toFixed(1)} GB tersisa`}/>
        </div>
      )}

      {/* System Status */}
      {health && (
        <div className="glass-card" style={{ padding:20 }}>
          <h3 style={{ fontSize:14, fontWeight:700, color:'#f1f5f9', marginBottom:14 }}>🔍 Status Komponen</h3>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8 }}>
            <StatusRow label="Database"   value={health.database}/>
            <StatusRow label="System"     value={health.status}/>
            {health.ai_models && Object.entries(health.ai_models).map(([k,v])=>(
              <StatusRow key={k} label={k.replace(/_/g,' ')} value={v}/>
            ))}
          </div>
          {health.uptime_seconds > 0 && (
            <div style={{ marginTop:12, fontSize:12, color:'#64748b' }}>
              ⏱ Uptime: {Math.floor(health.uptime_seconds/3600)}j {Math.floor((health.uptime_seconds%3600)/60)}m
            </div>
          )}
        </div>
      )}

      {/* Demo Stats */}
      <DemoStats />

      {/* API Reference */}
      <div className="glass-card" style={{ padding:20 }}>
        <h3 style={{ fontSize:14, fontWeight:700, color:'#f1f5f9', marginBottom:14 }}>🔗 REST API Endpoints</h3>
        <div style={{ display:'flex', flexDirection:'column', gap:6 }}>
          {[
            ['GET',  '/api/v1/crabs',              'List kepiting + filter + pagination'],
            ['GET',  '/api/v1/crabs/{id}',         'Detail kepiting by ID'],
            ['POST', '/api/v1/detect',             'Trigger AI detection pipeline'],
            ['GET',  '/api/v1/statistics',         'Data agregat dashboard'],
            ['GET',  '/api/v1/stream/cam1',        'MJPEG live stream kamera 1'],
            ['GET',  '/api/v1/stream/cam2',        'MJPEG live stream kamera 2'],
            ['WS',   '/api/v1/stream/ws/{id}',     'WebSocket binary stream'],
            ['GET',  '/api/v1/health',             'System health check'],
            ['GET',  '/api/v1/health/system',      'CPU / RAM / Disk usage'],
            ['GET',  '/api/v1/species',            'Database spesies kepiting'],
            ['GET',  '/docs',                      '📖 Swagger UI Documentation'],
          ].map(([m,p,d])=>(
            <div key={p} style={{ display:'flex', alignItems:'center', gap:10, padding:'7px 12px',
              borderRadius:8, background:'rgba(99,102,241,0.05)', border:'1px solid rgba(99,102,241,0.1)' }}>
              <span style={{ fontSize:10, fontWeight:800, padding:'2px 6px', borderRadius:4, fontFamily:'monospace',
                background: m==='GET'?'rgba(34,197,94,0.15)':m==='POST'?'rgba(99,102,241,0.2)':'rgba(6,182,212,0.15)',
                color: m==='GET'?'#4ade80':m==='POST'?'#a5b4fc':'#67e8f9' }}>
                {m}
              </span>
              <code style={{ fontSize:12, color:'#e2e8f0', flex:1 }}>{p}</code>
              <span style={{ fontSize:11, color:'#64748b' }}>{d}</span>
            </div>
          ))}
        </div>
        <div style={{ marginTop:14, display:'flex', gap:10 }}>
          <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" style={{
            display:'inline-flex', alignItems:'center', gap:6, padding:'8px 16px', borderRadius:8,
            fontSize:13, fontWeight:600, background:'linear-gradient(135deg,#6366f1,#8b5cf6)',
            color:'#fff', textDecoration:'none' }}>
            📖 Swagger UI
          </a>
          <a href="https://github.com/Azraelzinovia/crab-monitoring-system" target="_blank" rel="noopener noreferrer" style={{
            display:'inline-flex', alignItems:'center', gap:6, padding:'8px 16px', borderRadius:8,
            fontSize:13, fontWeight:600, background:'rgba(99,102,241,0.1)', color:'#94a3b8',
            textDecoration:'none', border:'1px solid rgba(99,102,241,0.2)' }}>
            ⭐ GitHub Repository
          </a>
        </div>
      </div>
    </div>
  );
}

function ResourceGauge({ label, icon, percent, sub1, sub2 }) {
  const pct   = percent || 0;
  const color = pct > 85 ? '#ef4444' : pct > 65 ? '#eab308' : '#22c55e';
  const dash  = pct * 1.26;
  return (
    <div className="glass-card" style={{ padding:20, textAlign:'center' }}>
      <div style={{ fontSize:12, fontWeight:700, color:'#94a3b8', marginBottom:8 }}>{icon} {label}</div>
      <div style={{ position:'relative', marginBottom:8 }}>
        <svg viewBox="0 0 100 55" style={{ width:'100%' }}>
          <path d="M10 50 A40 40 0 0 1 90 50" stroke="rgba(255,255,255,0.06)" strokeWidth="10" fill="none"/>
          <path d="M10 50 A40 40 0 0 1 90 50" stroke={color} strokeWidth="10" fill="none"
            strokeDasharray={`${dash} 126`} strokeLinecap="round"
            style={{ transition:'stroke-dasharray 0.8s ease' }}/>
        </svg>
        <div style={{ position:'absolute', bottom:0, width:'100%', textAlign:'center' }}>
          <div style={{ fontSize:24, fontWeight:800, color, lineHeight:1 }}>{pct.toFixed(0)}%</div>
        </div>
      </div>
      {sub1 && <div style={{ fontSize:11, color:'#64748b' }}>{sub1}</div>}
      {sub2 && <div style={{ fontSize:11, color:'#f97316', marginTop:2 }}>{sub2}</div>}
    </div>
  );
}

function StatusRow({ label, value }) {
  const good  = ['connected','loaded','healthy','demo'].includes(value);
  const color = good ? '#4ade80' : value==='demo' ? '#818cf8' : '#f97316';
  const emoji = good ? '✅' : value==='demo' ? '🔧' : '⚠️';
  return (
    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center',
      padding:'8px 12px', borderRadius:8, background:'rgba(99,102,241,0.04)',
      border:'1px solid rgba(99,102,241,0.08)' }}>
      <span style={{ fontSize:12, color:'#94a3b8', textTransform:'capitalize' }}>{label}</span>
      <span style={{ fontSize:12, fontWeight:700, color }}>{emoji} {value}</span>
    </div>
  );
}

function DemoStats() {
  const stats = getMockStatistics().dashboard;
  return (
    <div className="glass-card" style={{ padding:20 }}>
      <h3 style={{ fontSize:14, fontWeight:700, color:'#f1f5f9', marginBottom:14 }}>
        📊 Contoh Data Akumulasi
      </h3>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:10 }}>
        {[
          ['Total Deteksi', stats.total_crabs, '🦀'],
          ['Rata-rata Berat', `${stats.avg_weight_g}g`, '⚖️'],
          ['Rate/Jam', stats.detection_rate_per_hour, '⏱️'],
          ['Hari Ini', stats.today_count, '📅'],
        ].map(([l,v,e])=>(
          <div key={l} style={{ textAlign:'center', padding:'12px 8px',
            background:'rgba(99,102,241,0.06)', borderRadius:10,
            border:'1px solid rgba(99,102,241,0.12)' }}>
            <div style={{ fontSize:20, marginBottom:4 }}>{e}</div>
            <div style={{ fontSize:18, fontWeight:800, color:'#a5b4fc' }}>{v}</div>
            <div style={{ fontSize:10, color:'#64748b', marginTop:2 }}>{l}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
