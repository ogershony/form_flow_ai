import axios from 'axios';
import { getAuth } from 'firebase/auth';

// Create axios instance
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000/api',
  timeout: 60000, // 60 second timeout for AI operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    const auth = getAuth();
    const user = auth.currentUser;

    if (user) {
      try {
        const token = await user.getIdToken();
        config.headers.Authorization = `Bearer ${token}`;
      } catch (err) {
        console.error('Error getting auth token:', err);
      }
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error
      const { status, data } = error.response;

      if (status === 401) {
        // Unauthorized - redirect to login
        window.location.href = '/login';
      }

      // Return error message from server
      const message = data.error || data.message || 'An error occurred';
      return Promise.reject(new Error(message));
    } else if (error.request) {
      // No response received
      return Promise.reject(new Error('Network error. Please check your connection.'));
    } else {
      // Request setup error
      return Promise.reject(error);
    }
  }
);

// API functions

// Forms
export const createForm = async (userQuery, documents = []) => {
  const response = await api.post('/forms/create', { userQuery, documents });
  return response.data;
};

export const getForm = async (formId) => {
  const response = await api.get(`/forms/${formId}`);
  return response.data;
};

export const listForms = async () => {
  const response = await api.get('/forms/');
  return response.data;
};

export const saveForm = async (formId, schema, changeDescription = '') => {
  const response = await api.post(`/forms/${formId}/save`, { schema, changeDescription });
  return response.data;
};

export const editForm = async (formId, userQuery, documents = []) => {
  const response = await api.post(`/forms/${formId}/edit`, { userQuery, documents });
  return response.data;
};

export const undoForm = async (formId) => {
  const response = await api.post(`/forms/${formId}/undo`);
  return response.data;
};

export const submitFormResponse = async (formId, answers) => {
  const response = await api.post(`/forms/${formId}/submit`, { answers });
  return response.data;
};

export const getFormResponses = async (formId) => {
  const response = await api.get(`/forms/${formId}/responses`);
  return response.data;
};

export const deleteForm = async (formId) => {
  const response = await api.delete(`/forms/${formId}`);
  return response.data;
};

// Auth
export const verifyAuth = async () => {
  const response = await api.post('/auth/verify');
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get('/auth/me');
  return response.data;
};

export default api;
