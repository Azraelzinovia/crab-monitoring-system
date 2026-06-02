import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
export const BASE_URL = `${API_URL}/api/v1`;
export const STREAM_URL = API_URL;

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Response interceptor — centralized error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const msg = error.response?.data?.detail || error.message || 'Request failed';
    console.error('API Error:', msg);
    return Promise.reject(error);
  }
);

// ── API Functions ────────────────────────────────────────────────────────────

export const fetchStatistics = async () => {
  const { data } = await api.get('/statistics');
  return data;
};

export const fetchCrabs = async ({ page = 1, size = 20, species, gender, health_status } = {}) => {
  const params = { page, size };
  if (species) params.species = species;
  if (gender) params.gender = gender;
  if (health_status) params.health_status = health_status;
  const { data } = await api.get('/crabs', { params });
  return data;
};

export const fetchCrab = async (id) => {
  const { data } = await api.get(`/crabs/${id}`);
  return data;
};

export const deleteCrab = async (id) => {
  await api.delete(`/crabs/${id}`);
};

export const triggerDetection = async () => {
  const { data } = await api.post('/detect', { save_images: true, run_all_analysis: true });
  return data;
};

export const fetchDetectionStatus = async () => {
  const { data } = await api.get('/detect/status');
  return data;
};

export const fetchSystemHealth = async () => {
  const { data } = await api.get('/health');
  return data;
};

export const fetchSystemResources = async () => {
  const { data } = await api.get('/health/system');
  return data;
};

export const fetchSpecies = async () => {
  const { data } = await api.get('/species');
  return data;
};

export const fetchHealthRecords = async (crabId) => {
  const { data } = await api.get(`/crabs/${crabId}/health-records`);
  return data;
};

export const getCameraStreamUrl = (cameraId) =>
  `${STREAM_URL}/api/v1/stream/cam${cameraId}`;

export const getSnapshotUrl = (cameraId) =>
  `${STREAM_URL}/api/v1/stream/snapshot/${cameraId}`;

export default api;
