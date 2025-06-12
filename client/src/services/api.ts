// src/services/api.ts
import axios from 'axios';
import type { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env
  .VITE_API_BASE_URL /* e.g. "http://localhost:8000" */
  ? import.meta.env.VITE_API_BASE_URL
  : 'http://localhost:8000';

  
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
});

// For any request, if we have a token in localStorage, add it to Authorization header:
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;
