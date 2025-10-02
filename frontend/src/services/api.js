import axios from 'axios';

// Get API URL based on environment
const getApiUrl = () => {
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // For local development - MUST include /api prefix
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:8000/api';  // ← Added /api here
  }
  
  // For production
  const currentUrl = window.location.origin;
  if (currentUrl.includes('localhost') || currentUrl.includes('127.0.0.1')) {
    return 'http://localhost:8000/api';  // ← Added /api here
  }
  
  // Production backend
  return `${currentUrl}/api`;
};

// Configure axios defaults
const api = axios.create({
  baseURL: 'http://localhost:8000/api',  // ← Must have /api
  timeout: 300000,
  withCredentials: true,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
    }
    
    return Promise.reject(error);
  }
);

// Data gathering functions
export const gatherCompanyData = async (companyName, affinityCompanyId) => {
  // This will call: http://localhost:8000/api/data/gather ✅
  const response = await api.post('/data/gather', {
    company_name: companyName,
    company_id: affinityCompanyId
  });
  return response.data;
};

export const getSourceData = async (sourceId) => {
  const response = await api.get(`/data/source/${sourceId}`);
  return response.data;
};

export const listSources = async () => {
  const response = await api.get('/data/sources');
  return response.data;
};

// Memo generation functions
export const generateMemo = async (sourceId) => {
  const response = await api.post('/memo/generate', {
    source_id: sourceId
  });
  return response.data;
};

export const getMemoStatus = async (memoId) => {
  const response = await api.get(`/memo/${memoId}`);
  return response.data;
};

export const getMemoSections = async (memoId) => {
  const response = await api.get(`/memo/${memoId}/sections`);
  return response.data;
};

export const generateDocument = async (memoId) => {
  const response = await api.post(`/memo/${memoId}/generate-document`);
  return response.data;
};

export const downloadDocument = async (memoId) => {
  const response = await api.get(`/memo/${memoId}/download`, {
    responseType: 'blob',
  });
  return response.data;
};

// Health check
export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;