const BASE = '/api/v1';
const TOKEN_KEY = 'skillpath_token';
const REFRESH_KEY = 'skillpath_refresh';

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY);
}

function clearTokens() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

async function refreshAccessToken() {
  const refresh = getRefreshToken();
  if (!refresh) throw new Error('No refresh token');

  const res = await fetch(`${BASE}/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });

  if (!res.ok) throw new Error('Refresh failed');

  const data = await res.json();
  localStorage.setItem(TOKEN_KEY, data.access);
  if (data.refresh) {
    localStorage.setItem(REFRESH_KEY, data.refresh);
  }
  return data.access;
}

async function request(method, path, body, { skipRefresh = false } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && !skipRefresh) {
    try {
      await refreshAccessToken();
      return request(method, path, body, { skipRefresh: true });
    } catch (_) {
      clearTokens();
      window.location.reload();
      return;
    }
  }

  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      message = data.detail || data.error || JSON.stringify(data);
    } catch (_) {}
    throw new Error(message);
  }

  return res.json();
}

async function pollTask(taskId, { intervalMs = 2000, maxAttempts = 30 } = {}) {
  for (let i = 0; i < maxAttempts; i++) {
    const data = await request('GET', `/tasks/${taskId}/`);
    if (data.state === 'SUCCESS') return data.result;
    if (data.state === 'FAILURE') throw new Error(data.error || 'Task failed');
    await new Promise(r => setTimeout(r, intervalMs));
  }
  throw new Error('Task timed out');
}

export const api = {
  login(username, password) {
    return request('POST', '/auth/token/', { username, password });
  },

  register(username, email, password) {
    return request('POST', '/auth/register/', { username, email, password });
  },

  skills: {
    list() {
      return request('GET', '/skills/?page_size=100');
    },
    graph() {
      return request('GET', '/skills/graph/');
    },
    resources(id) {
      return request('GET', `/skills/${id}/resources/`);
    },
    async fromText(text) {
      const { task_id } = await request('POST', '/skills/from-text/', { text });
      return pollTask(task_id);
    },
  },

  path: {
    build(target_skills) {
      return request('POST', '/learning-path/', { target_skills });
    },
  },

  progress: {
    update(skill_id, completion_percent) {
      return request('POST', '/progress/update/', { skill_id, completion_percent });
    },
    userPath(userId) {
      return request('GET', `/users/${userId}/path/`);
    },
  },
};
