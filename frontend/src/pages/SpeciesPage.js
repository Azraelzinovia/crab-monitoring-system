import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchSpecies } from '../api/client';

export default function SpeciesPage() {
  const { data: speciesList = [], isLoading } = useQuery({
    queryKey: ['species'],
    queryFn: fetchSpecies,
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="glass-card" style={{ padding: 20 }}>
        <h2 style={{ fontSize: 16, fontWeight: 700, color: '#f1f5f9', marginBottom: 4 }}>
          📚 Database Referensi Spesies Kepiting
        </h2>
        <p style={{ fontSize: 12, color: '#64748b' }}>
          Data dikumpulkan secara otomatis dari GBIF, FAO, WoRMS, dan Wikipedia
        </p>
      </div>

      {isLoading ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {[1,2,3,4].map(i => (
            <div key={i} className="glass-card" style={{ padding: 20 }}>
              <div className="skeleton" style={{ height: 120 }} />
            </div>
          ))}
        </div>
      ) : speciesList.length === 0 ? (
        <div className="glass-card" style={{ padding: 60, textAlign: 'center' }}>
          <span style={{ fontSize: 48 }}>🔍</span>
          <div style={{ color: '#64748b', marginTop: 12 }}>
            Database kosong. Jalankan web scraper untuk mengisi data.
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {speciesList.map(species => (
            <SpeciesCard key={species.id} species={species} />
          ))}
        </div>
      )}
    </div>
  );
}

const SPECIES_GRADIENTS = {
  'Kepiting Bakau':   'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.1))',
  'Kepiting Rajungan': 'linear-gradient(135deg, rgba(20,184,166,0.2), rgba(6,182,212,0.1))',
  'Kepiting Lumpur':  'linear-gradient(135deg, rgba(249,115,22,0.2), rgba(234,88,12,0.1))',
  'Kepiting Batu':    'linear-gradient(135deg, rgba(236,72,153,0.2), rgba(219,39,119,0.1))',
};

function SpeciesCard({ species }) {
  const gradient = SPECIES_GRADIENTS[species.species_name] || SPECIES_GRADIENTS['Kepiting Bakau'];

  return (
    <div className="glass-card" style={{ padding: 20, background: gradient }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 14 }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#f1f5f9' }}>
            🦀 {species.species_name}
          </div>
          {species.scientific_name && (
            <div style={{ fontSize: 12, fontStyle: 'italic', color: '#94a3b8', marginTop: 2 }}>
              {species.scientific_name}
            </div>
          )}
          {species.family && (
            <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>
              Famili: {species.family}
            </div>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {species.habitat && (
          <InfoBlock icon="🏞️" label="Habitat" text={species.habitat} />
        )}
        {species.characteristics && (
          <InfoBlock icon="📝" label="Karakteristik" text={species.characteristics} />
        )}
        {species.distribution && (
          <InfoBlock icon="🗺️" label="Distribusi" text={species.distribution} />
        )}

        {/* Weight/Length Range */}
        {(species.average_weight_min_g || species.average_length_min_cm) && (
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 6,
          }}>
            {species.average_weight_min_g && (
              <RangeBox
                label="Berat"
                min={species.average_weight_min_g}
                max={species.average_weight_max_g}
                unit="g"
              />
            )}
            {species.average_length_min_cm && (
              <RangeBox
                label="Panjang"
                min={species.average_length_min_cm}
                max={species.average_length_max_cm}
                unit="cm"
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function InfoBlock({ icon, label, text }) {
  const truncated = text?.length > 120 ? text.slice(0, 120) + '...' : text;
  return (
    <div>
      <div style={{ fontSize: 10, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', marginBottom: 2 }}>
        {icon} {label}
      </div>
      <div style={{ fontSize: 12, color: '#cbd5e1', lineHeight: 1.5 }}>{truncated || '—'}</div>
    </div>
  );
}

function RangeBox({ label, min, max, unit }) {
  return (
    <div style={{
      background: 'rgba(0,0,0,0.2)', borderRadius: 8, padding: '8px 10px',
      border: '1px solid rgba(255,255,255,0.05)',
    }}>
      <div style={{ fontSize: 10, color: '#64748b', marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 13, fontWeight: 700, color: '#a5b4fc' }}>
        {min}–{max} {unit}
      </div>
    </div>
  );
}
