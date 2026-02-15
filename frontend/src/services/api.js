/**
 * API Service
 * Handles all communication with the backend API
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

/**
 * Request interceptor
 */
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Response interceptor
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * Device API methods
 */
export const deviceAPI = {
  /**
   * Get all devices
   */
  getAll: async () => {
    const response = await api.get('/api/devices');
    return response.data;
  },

  /**
   * Get device by ID
   */
  getById: async (deviceId) => {
    const response = await api.get(`/api/devices/${deviceId}`);
    return response.data;
  },

  /**
   * Register a new device
   */
  register: async (deviceData) => {
    const response = await api.post('/api/devices', deviceData);
    return response.data;
  },
};

/**
 * Metrics API methods
 */
export const metricsAPI = {
  /**
   * Submit metrics for a device
   */
  submit: async (deviceId, metrics) => {
    const response = await api.post(`/api/devices/${deviceId}/metrics`, {
      metrics,
    });
    return response.data;
  },

  /**
   * Get metrics for a device
   */
  get: async (deviceId, options = {}) => {
    const params = new URLSearchParams();

    if (options.dataType) params.append('data_type', options.dataType);
    if (options.limit) params.append('limit', options.limit);

    const response = await api.get(
      `/api/devices/${deviceId}/metrics?${params.toString()}`
    );
    return response.data;
  },
};

/**
 * Statistics API methods
 */
export const statsAPI = {
  /**
   * Get device statistics
   */
  getDeviceStats: async (deviceId) => {
    const response = await api.get(`/api/devices/${deviceId}/stats`);
    return response.data;
  },

  /**
   * Get aggregated statistics
   */
  getAggregatedStats: async (deviceId, dataType = 'temperature', period = 'hour') => {
    const response = await api.get(
      `/api/devices/${deviceId}/stats/aggregate?data_type=${dataType}&period=${period}`
    );
    return response.data;
  },
};

/**
 * AI/ML API methods
 */
export const aiAPI = {
  /**
   * Predict maintenance needs
   */
  predictMaintenance: async (deviceId, data) => {
    const response = await api.post(`/api/devices/${deviceId}/predict`, {
      data,
    });
    return response.data;
  },

  /**
   * Detect anomalies
   */
  detectAnomalies: async (deviceId, data) => {
    const response = await api.post(`/api/devices/${deviceId}/anomalies`, {
      data,
    });
    return response.data;
  },
};

/**
 * Rewards API methods
 */
export const rewardsAPI = {
  /**
   * Calculate rewards
   */
  calculate: async (deviceId, metrics, performanceData) => {
    const response = await api.post('/api/rewards/calculate', {
      device_id: deviceId,
      metrics,
      performance_data: performanceData,
    });
    return response.data;
  },

  /**
   * Get leaderboard
   */
  getLeaderboard: async (limit = 10) => {
    const response = await api.get(`/api/rewards/leaderboard?limit=${limit}`);
    return response.data;
  },
};

/**
 * Blockchain API methods
 */
export const blockchainAPI = {
  /**
   * Get blockchain statistics
   */
  getStats: async () => {
    const response = await api.get('/api/blockchain/stats');
    return response.data;
  },
};

/**
 * Health check
 */
export const healthAPI = {
  check: async () => {
    const response = await api.get('/api/health');
    return response.data;
  },
};

export default api;
