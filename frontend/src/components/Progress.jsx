import { useState, useEffect } from 'react';
import { api } from '../api.js';

const LEVEL_BADGE = {
  beginner:     'bg-green-100 text-green-800',
  intermediate: 'bg-blue-100 text-blue-800',
  advanced:     'bg-amber-100 text-amber-800',
  expert:       'bg-purple-100 text-purple-800',
};

export default function Progress({ skills }) {
  const [progressMap, setProgressMap] = useState({});
  const [sliders, setSliders] = useState({});
  const [toast, setToast] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const userId = localStorage.getItem('skillpath_uid');
  const visibleSkills = skills.slice(0, 20);

  useEffect(() => {
    if (!userId) {
      setLoading(false);
      return;
    }
    api.progress.userPath(Number(userId))
      .then(data => {
        const map = {};
        (data.progress || []).forEach(p => {
          map[p.skill_id ?? p.skill] = p.completion_percent;
        });
        setProgressMap(map);
        const initial = {};
        skills.slice(0, 20).forEach(s => {
          initial[s.id] = map[s.id] ?? 0;
        });
        setSliders(initial);
      })
      .catch(() => {
        const initial = {};
        skills.slice(0, 20).forEach(s => { initial[s.id] = 0; });
        setSliders(initial);
      })
      .finally(() => setLoading(false));
  }, [userId, skills]);

  async function handleUpdate(skill) {
    const percent = sliders[skill.id] ?? 0;
    try {
      await api.progress.update(skill.id, percent);
      setProgressMap(prev => ({ ...prev, [skill.id]: percent }));
      setToast(`Сохранено: ${skill.name} — ${percent}%`);
      setTimeout(() => setToast(''), 2500);
    } catch (err) {
      setError(err.message || 'Ошибка сохранения');
      setTimeout(() => setError(''), 3000);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-1">Мой прогресс</h2>
      <p className="text-sm text-gray-500 mb-6">Отметьте сколько процентов каждого навыка вы освоили</p>

      {toast && (
        <div className="fixed bottom-6 right-6 bg-green-600 text-white text-sm px-4 py-2.5 rounded-xl shadow-lg z-50">
          ✓ {toast}
        </div>
      )}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      <div className="space-y-4">
        {visibleSkills.map(skill => {
          const current = progressMap[skill.id] ?? 0;
          const slider = sliders[skill.id] ?? 0;
          const badgeClass = LEVEL_BADGE[skill.level] || 'bg-gray-100 text-gray-700';

          return (
            <div key={skill.id} className="border border-gray-100 rounded-xl p-4 hover:border-indigo-100 transition-colors">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 min-w-0">
                  <span className={`shrink-0 px-2.5 py-0.5 rounded-full text-xs font-medium ${badgeClass}`}>
                    {skill.level}
                  </span>
                  <span className="text-sm font-medium text-gray-800 truncate">{skill.name}</span>
                </div>
                <span className="text-sm font-semibold text-indigo-600 ml-3 shrink-0">{slider}%</span>
              </div>

              <div className="w-full bg-gray-100 rounded-full h-2 mb-3">
                <div
                  className="bg-indigo-500 h-2 rounded-full transition-all"
                  style={{ width: `${current}%` }}
                />
              </div>

              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={slider}
                  onChange={e => setSliders(prev => ({ ...prev, [skill.id]: Number(e.target.value) }))}
                  className="flex-1 accent-indigo-600"
                />
                <button
                  onClick={() => handleUpdate(skill)}
                  className="shrink-0 text-xs bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1.5 rounded-lg font-medium transition-colors"
                >
                  Сохранить
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {skills.length === 0 && (
        <p className="text-center text-gray-500 py-12">
          Навыки не найдены. Запустите{' '}
          <code className="bg-gray-100 px-1.5 py-0.5 rounded">python manage.py seed_skills</code>
        </p>
      )}
    </div>
  );
}
