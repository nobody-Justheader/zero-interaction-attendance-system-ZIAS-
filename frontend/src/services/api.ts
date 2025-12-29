import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add auth token to requests
api.interceptors.request.use((config: any) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// API methods
export const authAPI = {
    login: (username: string, password: string) =>
        api.post('/api/v1/auth/login', { username, password }),
};

export const attendanceAPI = {
    getRecords: (params?: any) =>
        api.get('/api/v1/attendance/records', { params }),
    getRealtimeOccupancy: (room: string) =>
        api.get(`/api/v1/attendance/realtime/${room}`),
    getSummary: (studentId: string, month?: number, year?: number) =>
        api.get(`/api/v1/attendance/summary/${studentId}`, { params: { month, year } }),
};

export const devicesAPI = {
    list: () => api.get('/api/v1/devices'),
    heartbeat: (deviceId: string, data: any) =>
        api.post(`/api/v1/devices/${deviceId}/heartbeat`, data),
};

export const studentsAPI = {
    list: () => api.get('/api/v1/students'),
    get: (id: string) => api.get(`/api/v1/students/${id}`),
    create: (data: any) => api.post('/api/v1/students', data),
};

export default api;
