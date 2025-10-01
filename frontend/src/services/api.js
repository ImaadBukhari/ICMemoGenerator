import axios from 'axios';

// Get API URL based on environment
const getApiUrl = () => {
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // For local development
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:8000/api';
  }
  
  // For production, try to detect backend URL
  const currentUrl = window.location.origin;
  if (currentUrl.includes('localhost') || currentUrl.includes('127.0.0.1')) {
    return 'http://localhost:8000/api';
  }
  
  // Assume backend is at same domain with /api prefix in production
  return `${currentUrl}/api`;
};

// Configure axios defaults
const api = axios.create({
  baseURL: getApiUrl(),
  timeout: 300000, // 5 minutes for long-running operations
  withCredentials: true, // Important for CORS with credentials
});

// Add request interceptor for auth if needed
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
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

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    
    // Handle specific error cases
    if (error.response?.status === 401) {
      // Handle unauthorized - maybe redirect to login
      localStorage.removeItem('auth_token');
    }
    
    return Promise.reject(error);
  }
);

// Data gathering functions
export const gatherCompanyData = async (companyName, affinityCompanyId) => {
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