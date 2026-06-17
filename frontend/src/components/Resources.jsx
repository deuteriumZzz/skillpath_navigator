import { useState } from 'react';
import { api } from '../api.js';

export default function Resources({ skills }) {
  const [query, setQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [resources, setResources] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedSkill, setSelectedSkill] = useState(null);

  const suggestions = query.length > 0
    ? skills.filter(s => s.name.toLowerCase().includes(query.toLowerCase())).slice(0, 8)
    : [];

  function handleSelect(skill) {
    setQuery(skill.name);
    setSelectedSkill(skill);
    setShowSuggestions(false);
  }

  async function handleFind() {
    const skill = selectedSkill || skills.find(s => s.name.toLowerCase() === query.toLowerCase());
    if (!skill) {
      setError('Навык не найден. Выберите из списка.');
      return;
    }
    setError('');
    setResources(null);
    setLoading(true);
    try {
      const data = await api.skills.resources(skill.id);
      setResources(data);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки ресурсов');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-6">Ресурсы для изучения</h2>

      {/* Search */}
      <div className="flex gap-3 mb-6 relative">
        <div className="flex-1 relative">
          <input
            type="text"
            value={query}
            onChange={e => { setQuery(e.target.value); setSelectedSkill(null); setShowSuggestions(true); }}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
            placeholder="Введите название навыка..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          {showSuggestions && suggestions.length > 0 && (
            <ul className="absolute z-10 left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
              {suggestions.map(skill => (
                <li
                  key={skill.id}
                  onMouseDown={() => handleSelect(skill)}
                  className="px-3 py-2 text-sm hover:bg-indigo-50 cursor-pointer"
                >
                  {skill.name}
                </li>
              ))}
            </ul>
          )}
        </div>
        <button
          onClick={handleFind}
          disabled={!query || loading}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-60 whitespace-nowrap"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Загрузка...
            </span>
          ) : (
            'Найти ресурсы'
          )}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {resources && (
        <div className="space-y-8">
          {/* GitHub repos */}
          {resources.github_repos && resources.github_repos.length > 0 && (
            <section>
              <h3 className="text-base font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <span>🐙</span> GitHub репозитории
              </h3>
              <div className="grid gap-3 sm:grid-cols-2">
                {resources.github_repos.map((repo, i) => (
                  <a
                    key={i}
                    href={repo.url || repo.link || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block bg-white rounded-xl shadow-sm border border-gray-100 p-4 hover:border-indigo-300 hover:shadow-md transition-all"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-medium text-sm text-gray-900 break-all">{repo.name}</span>
                      {repo.stars !== undefined && (
                        <span className="text-xs text-amber-600 whitespace-nowrap">⭐ {repo.stars}</span>
                      )}
                    </div>
                    {repo.description && (
                      <p className="mt-1 text-xs text-gray-500 line-clamp-2">{repo.description}</p>
                    )}
                  </a>
                ))}
              </div>
            </section>
          )}

          {/* YouTube */}
          {resources.youtube_videos && resources.youtube_videos.length > 0 && (
            <section>
              <h3 className="text-base font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <span>▶️</span> YouTube видео
              </h3>
              <div className="grid gap-3 sm:grid-cols-2">
                {resources.youtube_videos.map((video, i) => (
                  <a
                    key={i}
                    href={video.url || video.link || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block bg-white rounded-xl shadow-sm border border-gray-100 p-4 hover:border-red-300 hover:shadow-md transition-all"
                  >
                    <span className="font-medium text-sm text-gray-900">{video.title}</span>
                  </a>
                ))}
              </div>
            </section>
          )}

          {/* Courses */}
          {resources.courses && resources.courses.length > 0 && (
            <section>
              <h3 className="text-base font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <span>📚</span> Курсы
              </h3>
              <div className="grid gap-3 sm:grid-cols-2">
                {resources.courses.map((course, i) => (
                  <a
                    key={i}
                    href={course.url || course.link || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block bg-white rounded-xl shadow-sm border border-gray-100 p-4 hover:border-green-300 hover:shadow-md transition-all"
                  >
                    <span className="font-medium text-sm text-gray-900">{course.title}</span>
                    {course.platform && (
                      <span className="ml-2 text-xs text-gray-400">{course.platform}</span>
                    )}
                  </a>
                ))}
              </div>
            </section>
          )}

          {!resources.github_repos?.length && !resources.youtube_videos?.length && !resources.courses?.length && (
            <p className="text-gray-500 text-sm">Ресурсы не найдены для этого навыка</p>
          )}
        </div>
      )}
    </div>
  );
}
