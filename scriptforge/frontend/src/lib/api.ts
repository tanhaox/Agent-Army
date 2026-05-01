import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  // Send auth key from sessionStorage if configured
  const authKey = sessionStorage.getItem('sf_auth_key');
  if (authKey) {
    config.headers['X-API-Key'] = authKey;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error('API Error:', err?.response?.data || err.message);

    if (err.response && err.response.status === 401) {
      sessionStorage.removeItem('sf_auth_key');
      window.dispatchEvent(new CustomEvent('auth-required'));
    }

    // Auto-report 5xx errors to backend
    if (err.response && err.response.status >= 500) {
      try {
        axios.post('/api/logs/client', {
          message: err?.response?.data?.detail || err.message,
          url: window.location.href,
          userAgent: navigator.userAgent,
          stack: err.stack?.slice(0, 1000),
        }).catch(() => {});
      } catch {}
    }

    return Promise.reject(err);
  }
);

export default api;
