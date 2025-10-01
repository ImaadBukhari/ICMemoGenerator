import React, { createContext, useContext } from 'react';
import config from '../config/environment';

const ApiContext = createContext();

export const useApi = () => {
  const context = useContext(ApiContext);
  if (!context) {
    throw new Error('useApi must be used within an ApiProvider');
  }
  return context;
};

export const ApiProvider = ({ children }) => {
  const API_BASE_URL = config.API_URL;

  const apiCall = async (endpoint, options = {}) => {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    };

    const mergedOptions = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, mergedOptions);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`API call failed for ${endpoint}:`, error);
      throw error;
    }
  };

  // ... rest of your existing methods remain the same
  const gatherCompanyData = async (companyName, affinityCompanyId) => {
    return apiCall('/data/gather', {
      method: 'POST',
      body: JSON.stringify({
        company_name: companyName,
        affinity_company_id: affinityCompanyId
      }),
    });
  };

  // ... (keep all your existing API methods)

  const value = {
    gatherCompanyData,
    // ... (all your existing methods)
  };

  return (
    <ApiContext.Provider value={value}>
      {children}
    </ApiContext.Provider>
  );
};