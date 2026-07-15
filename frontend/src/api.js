import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8001',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach token if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Setup function to wire up logout handler when 401 Unauthorized occurs
export const setupAxiosInterceptors = (onLogout) => {
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      // If backend returns 401 Unauthorized, trigger logout immediately
      if (error.response && error.response.status === 401) {
        onLogout();
      }
      return Promise.reject(error);
    }
  );
};

export default api;
