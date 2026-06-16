// Shared color palette for entity types — used by the knowledge graph,
// legend, and wiki ego-graph so colors stay consistent everywhere.

export const ENTITY_COLORS: Record<string, string> = {
  person: '#3b82f6',        // blue
  organization: '#10b981',  // emerald
  paper: '#f59e0b',         // amber
  model: '#8b5cf6',         // violet
  method: '#ec4899',        // pink
  dataset: '#06b6d4',       // cyan
  benchmark: '#14b8a6',     // teal
  topic: '#64748b',         // slate
  project: '#f97316',       // orange
  system: '#6366f1',        // indigo
  event: '#ef4444',         // red
};

export const DEFAULT_ENTITY_COLOR = '#94a3b8';

export function entityColor(type: string | undefined): string {
  if (!type) return DEFAULT_ENTITY_COLOR;
  return ENTITY_COLORS[type] ?? DEFAULT_ENTITY_COLOR;
}

export const ENTITY_TYPES = Object.keys(ENTITY_COLORS);

// Human-readable labels so the graph shows e.g. "AI 模型" instead of the raw
// `model` enum value, which is ambiguous to end users.
const ENTITY_TYPE_LABELS: Record<string, { zh: string; en: string }> = {
  person:       { zh: '人物',     en: 'Person' },
  organization: { zh: '机构',     en: 'Organization' },
  paper:        { zh: '论文',     en: 'Paper' },
  model:        { zh: 'AI 模型',  en: 'AI Model' },
  method:       { zh: '方法',     en: 'Method' },
  dataset:      { zh: '数据集',   en: 'Dataset' },
  benchmark:    { zh: '基准',     en: 'Benchmark' },
  topic:        { zh: '研究领域', en: 'Topic' },
  project:      { zh: '项目',     en: 'Project' },
  system:       { zh: '系统',     en: 'System' },
  event:        { zh: '事件',     en: 'Event' },
};

export function entityTypeLabel(type: string | undefined, lang: 'zh' | 'en' = 'zh'): string {
  if (!type) return '';
  return ENTITY_TYPE_LABELS[type]?.[lang] ?? type;
}
