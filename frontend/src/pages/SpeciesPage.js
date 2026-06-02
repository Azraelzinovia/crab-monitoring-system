import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSpecies } from '../hooks/useApi';

const SPECIES_GRADIENTS = {
  'Kepiting Bakau':    'linear-gradient(135deg,rgba(99,102,241,0.2),rgba(139,92,246,0.1))',
  'Kepiting Rajungan': 'linear-gradient(135deg,rgba(20,184,166,0.2),rgba(6,182,212,0.1))',
  'Kepiting Lumpur':   'linear-gradient(135deg,rgba(249,115,22,0.2),rgba(234,88,12,0.1))',
  'Kepiting Batu':     'linear-gradient(135deg,rgba(236,72,153,0.2),rgba(219,39,119,0.1))',
};

export default function SpeciesPage() {
  const { data: speciesList = [], isLoading } = useSpecies();

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:20 }}>
      <div className="glass-card" style={{ padding:20 }}>
        <h2 style={{ fontSize:16, fontWeight:700, color:'#f1f5f9', marginBottom:4 }}>
          📚 Database Referensi Spesies Kepiting
        </h2>
        <p style={{ fontSize:12, color:'#64748b' }}>
          Data dikumpulkan dari GBIF, FAO, WoRMS, dan Wikipedia. Klik kartu untuk detail lengkap.
        </p>
      </div>

      {isLoading ? (
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
          {[1,2,3,4].map(i=>(
            <div key={i} className="glass-card" style={{ padding:20 }}>
              <div className="skeleton" style={{ height:200 }}/>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
          {speciesList.map(s => <SpeciesCard key={s.id} species={s} />)}
        </div>
      )}

      {/* Comparison table */}
      {speciesList.length > 0 && <ComparisonTable species={speciesList} />}
    </div>
  );
}

function SpeciesCard({ species: s }) {
  const [expanded, setExpanded] = React.useState(false);
  const gradient = SPECIES_GRADIENTS[s.species_name] || SPECIES_GRADIENTS['Kepiting Bakau'];

  return (
    <div className="glass-card" style={{ padding:20, background:gradient, cursor:'pointer' }}
      onClick={() => setExpanded(v=>!v)}>
      {/* Header */}
      <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom:14 }}>
        <div>
          <div style={{ fontSize:18, fontWeight:800, color:'#f1f5f9' }}>🦀 {s.species_name}</div>
          {s.scientific_name && (
            <div style={{ fontSize:12, fontStyle:'italic', color:'#94a3b8', marginTop:2 }}>{s.scientific_name}</div>
          )}
          {s.family && (
            <div style={{ fontSize:11, color:'#64748b' }}>Famili: {s.family}</div>
          )}
        </div>
        <span style={{ fontSize:16, color:'#64748b', transition:'transform 0.2s',
          transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)' }}>▼</span>
      </div>

      {/* Measurement range */}
      {(s.average_weight_min_g || s.average_length_min_cm) && (
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8, marginBottom:14 }}>
          {s.average_weight_min_g && (
            <RangeBox label="Berat" min={s.average_weight_min_g} max={s.average_weight_max_g} unit="g"/>
          )}
          {s.average_length_min_cm && (
            <RangeBox label="Panjang" min={s.average_length_min_cm} max={s.average_length_max_cm} unit="cm"/>
          )}
        </div>
      )}

      {/* Always visible */}
      {s.habitat && <InfoBlock icon="🏞️" label="Habitat" text={s.habitat} truncate={!expanded}/>}

      {/* Expanded content */}
      {expanded && (
        <div style={{ marginTop:12, borderTop:'1px solid rgba(255,255,255,0.08)', paddingTop:12,
          display:'flex', flexDirection:'column', gap:10 }}>
          {s.characteristics && <InfoBlock icon="📝" label="Karakteristik" text={s.characteristics}/>}
          {s.distribution && <InfoBlock icon="🗺️" label="Distribusi" text={s.distribution}/>}
          {s.common_diseases && <InfoBlock icon="⚠️" label="Penyakit Umum" text={s.common_diseases}/>}
          {s.source_url && (
            <a href={s.source_url} target="_blank" rel="noopener noreferrer"
              onClick={e=>e.stopPropagation()}
              style={{ fontSize:11, color:'#818cf8', textDecoration:'none', display:'inline-flex', gap:4 }}>
              🔗 Sumber Data
            </a>
          )}
          {s.created_at && (
            <div style={{ fontSize:10, color:'#475569' }}>
              Diperbarui: {new Date(s.created_at).toLocaleDateString('id-ID')}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function InfoBlock({ icon, label, text, truncate }) {
  const display = truncate && text?.length > 100 ? text.slice(0,100) + '…' : text;
  return (
    <div>
      <div style={{ fontSize:10, fontWeight:600, color:'#64748b', textTransform:'uppercase',
        letterSpacing:'0.05em', marginBottom:3 }}>{icon} {label}</div>
      <div style={{ fontSize:12, color:'#cbd5e1', lineHeight:1.6 }}>{display || '—'}</div>
    </div>
  );
}

function RangeBox({ label, min, max, unit }) {
  return (
    <div style={{ background:'rgba(0,0,0,0.2)', borderRadius:8, padding:'8px 10px',
      border:'1px solid rgba(255,255,255,0.05)' }}>
      <div style={{ fontSize:9, color:'#64748b', marginBottom:2, textTransform:'uppercase' }}>{label}</div>
      <div style={{ fontSize:13, fontWeight:700, color:'#a5b4fc' }}>{min}–{max} {unit}</div>
    </div>
  );
}

function ComparisonTable({ species }) {
  return (
    <div className="glass-card" style={{ overflow:'hidden' }}>
      <div style={{ padding:'14px 20px', borderBottom:'1px solid rgba(99,102,241,0.1)' }}>
        <h3 style={{ fontSize:14, fontWeight:700, color:'#f1f5f9' }}>📊 Perbandingan Spesies</h3>
      </div>
      <div style={{ overflowX:'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Spesies</th>
              <th>Nama Ilmiah</th>
              <th>Berat (g)</th>
              <th>Panjang (cm)</th>
              <th>Habitat</th>
            </tr>
          </thead>
          <tbody>
            {species.map(s=>(
              <tr key={s.id}>
                <td style={{ fontWeight:600 }}>🦀 {s.species_name}</td>
                <td style={{ fontStyle:'italic', color:'#94a3b8', fontSize:12 }}>{s.scientific_name||'—'}</td>
                <td style={{ fontFamily:'monospace' }}>
                  {s.average_weight_min_g ? `${s.average_weight_min_g}–${s.average_weight_max_g}` : '—'}
                </td>
                <td style={{ fontFamily:'monospace' }}>
                  {s.average_length_min_cm ? `${s.average_length_min_cm}–${s.average_length_max_cm}` : '—'}
                </td>
                <td style={{ fontSize:11, color:'#94a3b8', maxWidth:200 }}>
                  {s.habitat ? s.habitat.slice(0,80)+'…' : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
