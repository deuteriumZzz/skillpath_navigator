const BASE = '/api/v1';

function getToken() {
  return localStorage.getItem('skillpath_token');
}

async function request(method, path, body) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

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
