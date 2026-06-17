import { useState } from 'react';
import Auth from './components/Auth.jsx';
import Dashboard from './components/Dashboard.jsx';

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('skillpath_token'));

  function handleLogin(newToken) {
    setToken(newToken);
  }

  function handleLogout() {
    localStorage.removeItem('skillpath_token');
    localStorage.removeItem('skillpath_user');
    localStorage.removeItem('skillpath_uid');
    setToken(null);
  }

  if (!token) {
    return <Auth onLogin={handleLogin} />;
  }

  return <Dashboard onLogout={handleLogout} />;
}
