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
    api.post('/auth/login', new URLSearchParams({ username: username.trim(), password: password.trim() }), {
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

// ── Comments ──────────────────────────────────────────────────────────────────
export const commentsApi = {
  list: (taskId: number) => api.get(`/tasks/${taskId}/comments`),
  create: (taskId: number, content: string) =>
    api.post(`/tasks/${taskId}/comments`, { content }),
  delete: (commentId: number) => api.delete(`/comments/${commentId}`),
}

// ── Notifications ─────────────────────────────────────────────────────────────
export const notificationsApi = {
  list: () => api.get('/notifications'),
  markRead: (id: number) => api.patch(`/notifications/${id}/read`),
  markAllRead: () => api.patch('/notifications/read-all'),
  checkDeadlines: () => api.post('/notifications/check-deadlines'),
}

// ── Invites ───────────────────────────────────────────────────────────────────
export const invitesApi = {
  create:  (role: string)  => api.post('/invites', { role }),
  list:    ()              => api.get('/invites'),
  delete:  (id: number)   => api.delete(`/invites/${id}`),
  getInfo: (token: string) => api.get(`/invites/${token}/info`),
  accept:  (token: string, data: { username: string; password: string; full_name: string }) =>
    api.post(`/invites/${token}/accept`, data),
}

// ── Calendar ──────────────────────────────────────────────────────────────────
export const calendarApi = {
  myTasks:       () => api.get('/me/calendar'),
  getToken:      () => api.get('/me/calendar-token'),
  generateToken: () => api.post('/me/calendar-token'),
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

// ── Attachments ───────────────────────────────────────────────────────────────
export const attachmentsApi = {
  // Project attachments
  uploadProject: (projectId: number, file: File, visibility: string) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('visibility', visibility)
    return api.post(`/projects/${projectId}/attachments`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  listProject: (projectId: number) =>
    api.get(`/projects/${projectId}/attachments`),
  listAll: (projectId: number) =>
    api.get(`/projects/${projectId}/all-attachments`),
  deleteProject: (id: number) =>
    api.delete(`/project-attachments/${id}`),
  updateProjectVisibility: (id: number, visibility: string) =>
    api.patch(`/project-attachments/${id}/visibility`, null, { params: { visibility } }),

  // Task attachments
  uploadTask: (taskId: number, file: File, visibility: string) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('visibility', visibility)
    return api.post(`/tasks/${taskId}/attachments`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  listTask: (taskId: number) =>
    api.get(`/tasks/${taskId}/attachments`),
  deleteTask: (id: number) =>
    api.delete(`/task-attachments/${id}`),
  updateTaskVisibility: (id: number, visibility: string) =>
    api.patch(`/task-attachments/${id}/visibility`, null, { params: { visibility } }),
}
