export interface Organization {
  id: string;
  name: string;
  aliases: string[];
  org_type: string;
  website_url?: string;
  description?: string;
  country?: string;
  created_at: string;
  updated_at: string;
}

export interface SourceAccount {
  id: string;
  platform: string;
  handle?: string;
  url: string;
  is_primary: boolean;
  is_active: boolean;
}

export interface Tag {
  id: string;
  name: string;
  tag_type: string;
}

export interface SourceTag {
  tag_id: string;
  confidence: number;
  assigned_by: string;
  tag?: Tag;
}

export interface SourceCreate {
  name: string;
  source_type?: string;
  organization_id?: string;
  affiliation_type?: string;
  activity_status?: string;
  importance_score?: number;
  reliability_score?: number;
  is_active?: boolean;
}

export interface Source {
  id: string;
  name: string;
  source_type: string;
  organization_id?: string;
  affiliation_type?: string;
  role_title?: string;
  description?: string;
  activity_status: string;
  importance_score: number;
  reliability_score: number;
  is_active: boolean;
  organization?: Organization;
  accounts: SourceAccount[];
  source_tags: SourceTag[];
  created_at: string;
  updated_at: string;
}

export interface SignalAnalysis {
  id: string;
  tldr?: string;
  summary?: string;
  why_it_matters?: string;
  technical_points: string[];
  limitations?: string;
  topic_tags: string[];
  entities: string[];
  importance_score: number;
  novelty_score: number;
  relevance_score: number;
  confidence_score: number;
  reading_priority?: string;
  model_name?: string;
  analyzed_at: string;
}

export interface Signal {
  id: string;
  title: string;
  url: string;
  signal_type: string;
  source_id?: string;
  organization_id?: string;
  abstract?: string;
  content?: string;
  published_at?: string;
  collected_at: string;
  language: string;
  status: string;
  raw_metadata: Record<string, unknown>;
  analysis?: SignalAnalysis;
  created_at: string;
  updated_at: string;
}

export interface EntityAlias {
  id: string;
  alias: string;
  alias_type: string;
}

export interface Entity {
  id: string;
  name: string;
  canonical_name: string;
  entity_type: string;
  description?: string;
  homepage_url?: string;
  metadata: Record<string, unknown>;
  aliases: EntityAlias[];
  created_at: string;
  updated_at: string;
}

export interface EntityRelation {
  id: string;
  subject_entity_id: string;
  relation_type: string;
  object_entity_id: string;
  source_signal_id?: string;
  confidence: number;
  extracted_by?: string;
  created_at: string;
  subject?: Entity;
  object_entity?: Entity;
}

export interface PipelineRun {
  id: string;
  run_type: string;
  status: string;
  started_at: string;
  finished_at?: string;
  total_items: number;
  success_items: number;
  failed_items: number;
  error_message?: string;
}

export interface DashboardStats {
  total_sources: number;
  total_signals: number;
  total_entities: number;
  total_relations: number;
}

export interface SearchResults {
  sources: Source[];
  signals: Signal[];
  entities: Entity[];
}

export interface WikiEntityProfile {
  entity: Entity;
  aliases: EntityAlias[];
  related_signals: Signal[];
  outgoing_relations: EntityRelation[];
  incoming_relations: EntityRelation[];
  related_entities: Entity[];
}
