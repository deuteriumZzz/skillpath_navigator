import { useEffect, useRef, useState } from 'react';
import { Network, DataSet } from 'vis-network/standalone';
import { api } from '../api.js';

const LEVEL_COLORS = {
  beginner:     { background: '#bbf7d0', border: '#16a34a', highlight: { background: '#86efac', border: '#15803d' } },
  intermediate: { background: '#bfdbfe', border: '#2563eb', highlight: { background: '#93c5fd', border: '#1d4ed8' } },
  advanced:     { background: '#fde68a', border: '#d97706', highlight: { background: '#fcd34d', border: '#b45309' } },
  expert:       { background: '#e9d5ff', border: '#7c3aed', highlight: { background: '#d8b4fe', border: '#6d28d9' } },
};

const LEGEND = [
  { level: 'beginner',     label: 'Начинающий',     bg: 'bg-green-100',  text: 'text-green-800' },
  { level: 'intermediate', label: 'Средний',         bg: 'bg-blue-100',   text: 'text-blue-800'  },
  { level: 'advanced',     label: 'Продвинутый',     bg: 'bg-amber-100',  text: 'text-amber-800' },
  { level: 'expert',       label: 'Эксперт',         bg: 'bg-purple-100', text: 'text-purple-800'},
];

export default function SkillGraph({ skills }) {
  const containerRef = useRef(null);
  const networkRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [empty, setEmpty] = useState(false);

  useEffect(() => {
    let cancelled = false;

    api.skills.graph()
      .then(data => {
        if (cancelled) return;

        const { nodes: rawNodes, edges: rawEdges } = data;

        if (!rawNodes || rawNodes.length === 0) {
          setEmpty(true);
          setLoading(false);
          return;
        }

        const nodes = new DataSet(
          rawNodes.map(n => ({
            id: n.id,
            label: n.name,
            shape: 'box',
            color: LEVEL_COLORS[n.level] || LEVEL_COLORS.beginner,
            font: { size: 13 },
          }))
        );

        const edges = new DataSet(
          rawEdges.map((e, i) => ({
            id: i,
            from: e.from,
            to: e.to,
            arrows: 'to',
            smooth: { type: 'cubicBezier', forceDirection: 'horizontal', roundness: 0.4 },
          }))
        );

        const options = {
          layout: {
            hierarchical: {
              direction: 'LR',
              sortMethod: 'directed',
              levelSeparation: 200,
              nodeSpacing: 100,
            },
          },
          physics: { enabled: false },
          interaction: { hover: true, tooltipDelay: 200 },
          edges: {
            color: { color: '#94a3b8', highlight: '#6366f1' },
            width: 1.5,
          },
          nodes: {
            borderWidth: 2,
            borderWidthSelected: 3,
          },
        };

        if (containerRef.current) {
          networkRef.current = new Network(containerRef.current, { nodes, edges }, options);
        }

        setLoading(false);
      })
      .catch(() => {
        if (!cancelled) {
          setEmpty(true);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, []);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Граф навыков</h2>

      {loading && (
        <div className="flex justify-center items-center" style={{ height: '550px' }}>
          <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {!loading && empty && (
        <div className="flex flex-col items-center justify-center text-gray-500" style={{ height: '550px' }}>
          <div className="text-5xl mb-4">🕸️</div>
          <p className="text-lg font-medium text-gray-700">Граф пуст.</p>
          <p className="text-sm mt-1 font-mono bg-gray-100 px-3 py-1.5 rounded-lg">
            python manage.py seed_skills
          </p>
        </div>
      )}

      {!loading && !empty && (
        <div ref={containerRef} style={{ height: '550px', width: '100%' }} />
      )}

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-3">
        {LEGEND.map(({ level, label, bg, text }) => (
          <span key={level} className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${bg} ${text}`}>
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: LEVEL_COLORS[level]?.border }} />
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
