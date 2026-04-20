import axios from 'axios'

// Dev: Vite proxy prepisuje /api → localhost:8000
// Prod: VITE_API_URL = https://your-app.railway.app
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Automaticky pridá Bearer token z localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 401 → presmeruj na login (ale NIE keď sme práve na login endpointe)
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const isLoginEndpoint = err.config?.url?.includes('/auth/login')
    if (err.response?.status === 401 && !isLoginEndpoint) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

// ── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  register: (data: { username: string; password: string; full_name: string; role?: string }) =>
    api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
  changePassword: (current_password: string, new_password: string) =>
    api.patch('/auth/me/password', { current_password, new_password }),
}

// ── Projects ─────────────────────────────────────────────────────────────────
export const projectsApi = {
  list: () => api.get('/projects/'),
  get: (id: number) => api.get(`/projects/${id}`),
  create: (data: { name: string; description?: string; status?: string }) =>
    api.post('/projects/', data),
  update: (id: number, data: { status?: string; name?: string }) =>
    api.patch(`/projects/${id}`, data),
  templates: () => api.get('/projects/templates/list'),
}

// ── Tasks ─────────────────────────────────────────────────────────────────────
export const tasksApi = {
  list: (projectId: number) => api.get(`/projects/${projectId}/tasks`),
  create: (projectId: number, data: object) =>
    api.post(`/projects/${projectId}/tasks`, data),
  update: (taskId: number, data: object) => api.patch(`/tasks/${taskId}`, data),
  delete: (taskId: number) => api.delete(`/tasks/${taskId}`),
  getDependencies: (taskId: number) => api.get(`/tasks/${taskId}/dependencies`),
  getProjectDependencies: (projectId: number) => api.get(`/projects/${projectId}/dependencies`),
  addDependency: (taskId: number, dependsOn: number) =>
    api.post(`/tasks/${taskId}/dependencies?depends_on=${dependsOn}`),
}

// ── Team ──────────────────────────────────────────────────────────────────────
export const teamApi = {
  myTeam: () => api.get('/team/'),
  all: () => api.get('/team/all'),
  tree: () => api.get('/team/tree'),
  workload: (userId: number) => api.get(`/team/${userId}/workload`),
  update: (userId: number, data: { role?: string; manager_id?: number | null }) =>
    api.patch(`/team/${userId}`, data),
}
