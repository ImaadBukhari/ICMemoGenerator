// src/api.js
import axios from "axios";
import { getAuth } from "firebase/auth";

const BASE_URL = "https://icmemo-backend-211323749133.us-central1.run.app/api"; 

// Create Axios instance
const api = axios.create({
  baseURL: BASE_URL,
});

// Automatically attach Firebase ID token
api.interceptors.request.use(async (config) => {
  const auth = getAuth();
  const user = auth.currentUser;
  if (user) {
    const token = await user.getIdToken();
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api; 
