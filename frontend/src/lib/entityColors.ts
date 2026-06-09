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
