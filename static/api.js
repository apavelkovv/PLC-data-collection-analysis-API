const API_URL = "/api/v1";

async function apiRequest(endpoint, method = 'GET', body = null, rawResponse = false) {
    const token = localStorage.getItem('access_token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const config = { method, headers };
    if (body) config.body = JSON.stringify(body);

    const response = await fetch(`${API_URL}${endpoint}`, config);

    if (response.status === 401) {
        if (!window.location.href.includes("login.html")) {
            window.location.href = "login.html";
        }
        return null;
    }

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Ошибка сервера' }));
        throw new Error(error.detail || 'Ошибка сервера');
    }

    if (rawResponse) return response;
    return response.status !== 204 ? response.json() : null;
}

const api = {
    // ─── Auth ───────────────────────────────────────────────────────────────
    login: async (username, password) => {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        const res = await fetch(`${API_URL}/auth/login`, { method: 'POST', body: formData });
        if (!res.ok) throw new Error('Неверный логин или пароль');
        const data = await res.json();
        if (data.access_token) {
            localStorage.setItem('access_token', data.access_token);
        }
        return data;
    },
    logout: () => {
        localStorage.removeItem('access_token');
        window.location.href = 'login.html';
    },
    getMe: () => apiRequest('/auth/me'),
    register: (username, email, password, role = 'student') =>
        apiRequest('/auth/register', 'POST', { username, email, password, role }),

    // ─── Users ──────────────────────────────────────────────────────────────
    getUsers: (skip = 0, limit = 100) =>
        apiRequest(`/users/?skip=${skip}&limit=${limit}`),
    getUser: (id) => apiRequest(`/users/${id}`),
    updateUser: (id, data) => apiRequest(`/users/${id}`, 'PATCH', data),
    deleteUser: (id) => apiRequest(`/users/${id}`, 'DELETE'),

    // ─── Stands ─────────────────────────────────────────────────────────────
    getStands: (skip = 0, limit = 100) =>
        apiRequest(`/stands/?skip=${skip}&limit=${limit}`),
    getStand: (id) => apiRequest(`/stands/${id}`),
    createStand: (data) => apiRequest('/stands/', 'POST', data),
    updateStand: (id, data) => apiRequest(`/stands/${id}`, 'PATCH', data),
    deleteStand: (id) => apiRequest(`/stands/${id}`, 'DELETE'),
    getThresholds: (standId) => apiRequest(`/stands/${standId}/thresholds`),
    createThreshold: (standId, data) =>
        apiRequest(`/stands/${standId}/thresholds`, 'POST', data),

    // ─── Experiments ────────────────────────────────────────────────────────
    getExperiments: (params = {}) => {
        const q = new URLSearchParams({ skip: 0, limit: 50, ...params }).toString();
        return apiRequest(`/experiments/?${q}`);
    },
    getExperiment: (id) => apiRequest(`/experiments/${id}`),
    createExperiment: (title, standId, description = '') =>
        apiRequest('/experiments/', 'POST', { title, stand_id: standId, description }),
    updateExperiment: (id, data) => apiRequest(`/experiments/${id}`, 'PATCH', data),
    startExperiment: (id) => apiRequest(`/experiments/${id}/start`, 'POST'),
    pauseExperiment: (id) => apiRequest(`/experiments/${id}/pause`, 'POST'),
    stopExperiment: (id) => apiRequest(`/experiments/${id}/stop`, 'POST'),

    // ─── Telemetry ──────────────────────────────────────────────────────────
    getTelemetry: (expId, params = {}) => {
        const q = new URLSearchParams({ limit: 100, ...params }).toString();
        return apiRequest(`/experiments/${expId}/telemetry?${q}`);
    },
    postTelemetry: (expId, parameterName, value, unit = null) =>
        apiRequest(`/experiments/${expId}/telemetry`, 'POST', { parameter_name: parameterName, value, unit }),
    exportCsv: async (expId) => {
        const response = await apiRequest(`/experiments/${expId}/export/csv`, 'GET', null, true);
        if (!response) return;
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `experiment_${expId}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    },

    // ─── Events / Logs ──────────────────────────────────────────────────────
    getExperimentEvents: (expId, skip = 0, limit = 200) =>
        apiRequest(`/experiments/${expId}/events?skip=${skip}&limit=${limit}`),
    getGlobalEvents: (params = {}) => {
        const q = new URLSearchParams({ skip: 0, limit: 200, ...params }).toString();
        return apiRequest(`/events/?${q}`);
    },
};