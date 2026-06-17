import { useState, useEffect } from 'react';
import { api } from '../api.js';
import SkillGraph from './SkillGraph.jsx';
import LearningPath from './LearningPath.jsx';
import Resources from './Resources.jsx';
import Progress from './Progress.jsx';

const TABS = [
  { key: 'graph', label: 'Граф навыков' },
  { key: 'path', label: 'Путь обучения' },
  { key: 'resources', label: 'Ресурсы' },
  { key: 'progress', label: 'Прогресс' },
];

export default function Dashboard({ onLogout }) {
  const [activeTab, setActiveTab] = useState('graph');
  const [skills, setSkills] = useState([]);
  const [skillsLoading, setSkillsLoading] = useState(true);
  const username = localStorage.getItem('skillpath_user') || 'Пользователь';

  useEffect(() => {
    api.skills.list()
      .then(data => setSkills(data.results || []))
      .catch(() => setSkills([]))
      .finally(() => setSkillsLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🗺️</span>
            <span className="text-lg font-bold text-gray-900">SkillPath Navigator</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">👤 {username}</span>
            <button
              onClick={onLogout}
              className="text-sm text-gray-500 hover:text-red-600 transition-colors px-3 py-1.5 rounded-lg hover:bg-red-50"
            >
              Выйти
            </button>
          </div>
        </div>
      </header>

      {/* Tab bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex gap-0">
            {TABS.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-5 py-4 text-sm font-medium transition-colors ${
                  activeTab === tab.key
                    ? 'border-b-2 border-indigo-600 text-indigo-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {skillsLoading ? (
          <div className="flex justify-center items-center h-64">
            <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <>
            {activeTab === 'graph' && <SkillGraph skills={skills} />}
            {activeTab === 'path' && <LearningPath skills={skills} />}
            {activeTab === 'resources' && <Resources skills={skills} />}
            {activeTab === 'progress' && <Progress skills={skills} />}
          </>
        )}
      </main>
    </div>
  );
}
