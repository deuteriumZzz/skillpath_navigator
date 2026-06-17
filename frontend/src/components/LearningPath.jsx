import { useState } from 'react';
import { api } from '../api.js';

const LEVEL_BADGE = {
  beginner:     'bg-green-100 text-green-800',
  intermediate: 'bg-blue-100 text-blue-800',
  advanced:     'bg-amber-100 text-amber-800',
  expert:       'bg-purple-100 text-purple-800',
};

export default function LearningPath({ skills }) {
  const [selectedSkillId, setSelectedSkillId] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleBuild() {
    if (!selectedSkillId) return;
    const skill = skills.find(s => String(s.id) === selectedSkillId);
    if (!skill) return;

    setError('');
    setResult(null);
    setLoading(true);
    try {
      const data = await api.path.build([skill.name]);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Ошибка построения пути');
    } finally {
      setLoading(false);
    }
  }

  // Extract path steps from response
  const planItems = result?.plan || [];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-6">Путь обучения</h2>

      <div className="flex gap-3 mb-6">
        <select
          value={selectedSkillId}
          onChange={e => setSelectedSkillId(e.target.value)}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">Выберите целевой навык...</option>
          {skills.map(skill => (
            <option key={skill.id} value={skill.id}>
              {skill.name}
            </option>
          ))}
        </select>
        <button
          onClick={handleBuild}
          disabled={!selectedSkillId || loading}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-60 whitespace-nowrap"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Построение...
            </span>
          ) : (
            'Построить путь'
          )}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {planItems.length > 0 && planItems.map((item, idx) => {
        const pathData = item.path;
        const pathSteps = pathData?.path || [];
        const pathLevels = pathData?.levels || [];
        const distance = pathData?.distance;

        return (
          <div key={idx} className="mb-8">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">
              Цель: <span className="text-indigo-600">{item.target}</span>
            </h3>

            {pathSteps.length === 0 ? (
              <p className="text-gray-500 text-sm">Путь не найден</p>
            ) : (
              <>
                {/* Stepper */}
                <div className="flex flex-wrap items-center gap-2">
                  {pathSteps.map((step, stepIdx) => {
                    const level = pathLevels[stepIdx] || 'beginner';
                    const badgeClass = LEVEL_BADGE[level] || LEVEL_BADGE.beginner;
                    return (
                      <div key={stepIdx} className="flex items-center gap-2">
                        <span className={`inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium ${badgeClass}`}>
                          <span className="w-5 h-5 rounded-full bg-white bg-opacity-60 flex items-center justify-center text-xs font-bold mr-1.5">
                            {stepIdx + 1}
                          </span>
                          {step}
                        </span>
                        {stepIdx < pathSteps.length - 1 && (
                          <span className="text-gray-400 text-lg">→</span>
                        )}
                      </div>
                    );
                  })}
                </div>

                {distance !== undefined && (
                  <p className="mt-3 text-sm text-gray-500">
                    Расстояние: <span className="font-semibold text-gray-700">{Math.round(distance)} шагов</span>
                  </p>
                )}
              </>
            )}
          </div>
        );
      })}

      {result && planItems.length === 0 && (
        <p className="text-gray-500 text-sm">Путь не найден для выбранного навыка</p>
      )}
    </div>
  );
}
