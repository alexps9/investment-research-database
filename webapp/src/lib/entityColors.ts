export const ENTITY_COLORS: Record<string, string> = {
  person: '#3b82f6',
  organization: '#10b981',
  paper: '#f59e0b',
  model: '#8b5cf6',
  method: '#ec4899',
  dataset: '#06b6d4',
  benchmark: '#14b8a6',
  topic: '#64748b',
  project: '#f97316',
  system: '#6366f1',
  event: '#ef4444',
};

export const LANE_COLORS: Record<string, string> = {
  video_gen: '#2563EB',
  rl_based: '#059669',
  latent_space: '#7C3AED',
  vla: '#EA580C',
};

export const DEFAULT_ENTITY_COLOR = '#94a3b8';

export function entityColor(type: string | undefined): string {
  if (!type) return DEFAULT_ENTITY_COLOR;
  return ENTITY_COLORS[type] ?? DEFAULT_ENTITY_COLOR;
}

export function laneColor(laneKey: string | undefined): string {
  if (!laneKey) return DEFAULT_ENTITY_COLOR;
  return LANE_COLORS[laneKey] ?? DEFAULT_ENTITY_COLOR;
}
