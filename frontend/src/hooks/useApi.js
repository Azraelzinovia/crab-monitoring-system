// src/hooks/useApi.js
// Custom React hooks untuk semua API calls dengan auto-retry dan error handling

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchStatistics, fetchCrabs, fetchCrab,
  triggerDetection, fetchSystemHealth, fetchSystemResources,
  fetchSpecies, fetchDetectionStatus,
} from '../api/client';

// ── Queries ───────────────────────────────────────────────────────────────────

export function useStatistics(options = {}) {
  return useQuery({
    queryKey: ['statistics'],
    queryFn: fetchStatistics,
    refetchInterval: 15_000,
    placeholderData: getMockStatistics(),
    ...options,
  });
}

export function useCrabs(params = {}, options = {}) {
  return useQuery({
    queryKey: ['crabs', params],
    queryFn: () => fetchCrabs(params),
    refetchInterval: 10_000,
    placeholderData: getMockCrabList(),
    ...options,
  });
}

export function useCrab(id, options = {}) {
  return useQuery({
    queryKey: ['crabs', id],
    queryFn: () => fetchCrab(id),
    enabled: !!id,
    ...options,
  });
}

export function useSystemHealth(options = {}) {
  return useQuery({
    queryKey: ['systemHealth'],
    queryFn: fetchSystemHealth,
    refetchInterval: 30_000,
    placeholderData: getMockSystemHealth(),
    ...options,
  });
}

export function useSystemResources(options = {}) {
  return useQuery({
    queryKey: ['systemResources'],
    queryFn: fetchSystemResources,
    refetchInterval: 5_000,
    placeholderData: getMockResources(),
    ...options,
  });
}

export function useSpecies(options = {}) {
  return useQuery({
    queryKey: ['species'],
    queryFn: fetchSpecies,
    staleTime: 300_000,    // 5 minutes — species data rarely changes
    placeholderData: getMockSpecies(),
    ...options,
  });
}

export function useDetectionStatus(options = {}) {
  return useQuery({
    queryKey: ['detectStatus'],
    queryFn: fetchDetectionStatus,
    refetchInterval: 10_000,
    ...options,
  });
}

// ── Mutations ─────────────────────────────────────────────────────────────────

export function useDetection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: triggerDetection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['statistics'] });
      queryClient.invalidateQueries({ queryKey: ['crabs'] });
    },
  });
}

// ── Mock Data (digunakan saat backend belum tersedia) ─────────────────────────

export function getMockStatistics() {
  return {
    dashboard: {
      total_crabs: 247,
      male_count: 134,
      female_count: 113,
      healthy_count: 198,
      sick_count: 23,
      today_count: 18,
      avg_weight_g: 342.5,
      detection_rate_per_hour: 7.2,
    },
    species_distribution: [
      { species: 'Kepiting Bakau',    count: 89,  percentage: 36.0 },
      { species: 'Kepiting Rajungan', count: 76,  percentage: 30.8 },
      { species: 'Kepiting Lumpur',   count: 52,  percentage: 21.1 },
      { species: 'Kepiting Batu',     count: 30,  percentage: 12.1 },
    ],
    health_distribution: [
      { health_status: 'Sehat',        count: 198, percentage: 80.2 },
      { health_status: 'Kurang Sehat', count: 26,  percentage: 10.5 },
      { health_status: 'Sakit',        count: 18,  percentage: 7.3  },
      { health_status: 'Mati',         count: 5,   percentage: 2.0  },
    ],
    weight_trend: Array.from({ length: 14 }, (_, i) => ({
      date: new Date(Date.now() - (13 - i) * 86400000).toISOString().slice(0, 10),
      avg_weight_g: 280 + Math.sin(i * 0.5) * 80 + Math.random() * 40,
      count: 15 + Math.floor(Math.random() * 10),
    })),
  };
}

export function getMockCrabList() {
  const species  = ['Kepiting Bakau', 'Kepiting Rajungan', 'Kepiting Lumpur', 'Kepiting Batu'];
  const genders  = ['Jantan', 'Betina'];
  const healths  = ['Sehat', 'Sehat', 'Sehat', 'Kurang Sehat', 'Sakit'];

  const crabs = Array.from({ length: 15 }, (_, i) => ({
    id: 200 + i,
    timestamp: new Date(Date.now() - i * 180000).toISOString(),
    species:  species[i % species.length],
    gender:   genders[i % 2],
    health_status: healths[i % healths.length],
    weight_g: +(200 + Math.random() * 600).toFixed(1),
    length_cm: +(8 + Math.random() * 12).toFixed(1),
    width_cm:  +(6 + Math.random() * 8).toFixed(1),
    species_confidence: +(85 + Math.random() * 14).toFixed(1),
    gender_confidence:  +(82 + Math.random() * 17).toFixed(1),
    health_confidence:  +(80 + Math.random() * 19).toFixed(1),
    detection_confidence: +(0.75 + Math.random() * 0.24).toFixed(3),
    left_claw:     Math.random() > 0.1,
    right_claw:    Math.random() > 0.1,
    legs_complete: Math.random() > 0.1,
    shell_damage:  Math.random() < 0.12,
    session_id: `demo-${(i % 3) + 1}`,
    track_id: 10 + i,
    image_cam1: null,
    image_cam2: null,
  }));

  return { total: 247, page: 1, size: 15, crabs };
}

export function getMockSystemHealth() {
  return {
    status: 'demo',
    database: 'demo-mode',
    cameras: {
      1: { active: false, fps: 0, frame_count: 0, error: 'Backend tidak berjalan (Demo Mode)' },
      2: { active: false, fps: 0, frame_count: 0, error: 'Backend tidak berjalan (Demo Mode)' },
    },
    ai_models: {
      yolo: 'demo', species_classifier: 'demo',
      gender_classifier: 'demo', health_classifier: 'demo',
    },
    storage: { accessible: true, free_gb: 0 },
    uptime_seconds: 0,
  };
}

export function getMockResources() {
  return {
    cpu:    { percent: 15 + Math.random() * 20, cores: 4, temperature_c: 45 },
    memory: { total_gb: 8, used_gb: 2.1, percent: 26 },
    disk:   { total_gb: 64, used_gb: 12, free_gb: 52, percent: 18 },
    uptime_seconds: 3600,
  };
}

export function getMockSpecies() {
  return [
    {
      id: 1, species_name: 'Kepiting Bakau', scientific_name: 'Scylla serrata',
      family: 'Portunidae',
      habitat: 'Hutan mangrove, estuari, dan perairan payau di sepanjang pesisir tropis.',
      characteristics: 'Cangkang keras berwarna hijau kecoklatan hingga coklat tua. Capit besar dan kuat. Dua duri tajam di setiap sisi cangkang.',
      average_weight_min_g: 100, average_weight_max_g: 1200,
      average_length_min_cm: 8, average_length_max_cm: 20,
      distribution: 'Indo-Pasifik Barat: Asia Tenggara, India, Afrika Timur, Australia',
      source_url: 'https://www.gbif.org/species/2225848',
      created_at: new Date().toISOString(),
    },
    {
      id: 2, species_name: 'Kepiting Rajungan', scientific_name: 'Portunus pelagicus',
      family: 'Portunidae',
      habitat: 'Perairan laut dangkal berpasir, padang lamun, dan terumbu karang.',
      characteristics: 'Cangkang biru kehijauan dengan bintik-bintik putih. Kaki belakang berbentuk dayung untuk berenang.',
      average_weight_min_g: 50, average_weight_max_g: 400,
      average_length_min_cm: 6, average_length_max_cm: 18,
      distribution: 'Indo-Pasifik: Jepang, Australia, India, Afrika Timur',
      source_url: 'https://www.gbif.org/species/2225952',
      created_at: new Date().toISOString(),
    },
    {
      id: 3, species_name: 'Kepiting Lumpur', scientific_name: 'Scylla olivacea',
      family: 'Portunidae',
      habitat: 'Lumpur estuari, tambak, dan kawasan mangrove bersubstrat lunak.',
      characteristics: 'Cangkang lebih kecil dari S. serrata, warna coklat kemerahan hingga zaitun.',
      average_weight_min_g: 80, average_weight_max_g: 600,
      average_length_min_cm: 6, average_length_max_cm: 15,
      distribution: 'Asia Tenggara: Indonesia, Malaysia, Filipina, Thailand',
      source_url: 'https://www.gbif.org/species/2225849',
      created_at: new Date().toISOString(),
    },
    {
      id: 4, species_name: 'Kepiting Batu', scientific_name: 'Charybdis feriata',
      family: 'Portunidae',
      habitat: 'Dasar berbatu dan berkarang di perairan laut dangkal hingga sedang.',
      characteristics: 'Cangkang keras dengan pola garis-garis khas. Warna coklat atau merah bata.',
      average_weight_min_g: 100, average_weight_max_g: 800,
      average_length_min_cm: 7, average_length_max_cm: 17,
      distribution: 'Indo-Pasifik: Asia Tenggara, India, Laut Merah, Jepang',
      source_url: 'https://www.gbif.org/species/2227058',
      created_at: new Date().toISOString(),
    },
  ];
}
