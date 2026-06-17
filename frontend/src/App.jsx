import { useState } from 'react';
import Auth from './components/Auth.jsx';
import Dashboard from './components/Dashboard.jsx';

function decodeJwtUserId(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.user_id ?? null;
  } catch (_) {
    return null;
  }
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('skillpath_token'));
  const [userId, setUserId] = useState(() => {
    const stored = localStorage.getItem('skillpath_token');
    return stored ? decodeJwtUserId(stored) : null;
  });

  function handleLogin(newToken, refreshToken, username) {
    localStorage.setItem('skillpath_token', newToken);
    localStorage.setItem('skillpath_refresh', refreshToken);
    localStorage.setItem('skillpath_user', username);
    setToken(newToken);
    setUserId(decodeJwtUserId(newToken));
  }

  function handleLogout() {
    localStorage.removeItem('skillpath_token');
    localStorage.removeItem('skillpath_refresh');
    localStorage.removeItem('skillpath_user');
    setToken(null);
    setUserId(null);
  }

  if (!token) {
    return <Auth onLogin={handleLogin} />;
  }

  return <Dashboard onLogout={handleLogout} userId={userId} />;
}
