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

export interface SourceExperience {
  id: string;
  organization_id?: string;
  org_name_raw?: string;
  role_title?: string;
  start_date?: string;
  end_date?: string;
  is_current: boolean;
  organization?: Organization;
  created_at: string;
}

export type SourceExperienceCreate = Omit<SourceExperience, 'id' | 'organization' | 'created_at'>;

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

export interface SourceExtended {
  tier?: string;
  sector?: string;
  tier_reason?: string;
  notes?: string;
  source_authority?: string;
  last_tweet_at?: string;
  avg_interval_days?: number;
  arxiv_author_query?: string;
  affiliation_regex?: string;
  orcid?: string;
  twitter_url?: string;
  openalex_url?: string;
  scholar_url?: string;
  github_url?: string;
  personal_url?: string;
  arxiv_homepage_url?: string;
}

export interface SourceCreate extends SourceExtended {
  name: string;
  source_type?: string;
  organization_id?: string;
  affiliation_type?: string;
  role_title?: string;
  description?: string;
  activity_status?: string;
  importance_score?: number;
  reliability_score?: number;
  is_active?: boolean;
  /** When provided, atomically replaces all topic tags for the source. */
  tag_ids?: string[];
}

export type SourceUpdate = Partial<SourceCreate>;

export interface Source extends SourceExtended {
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
  experiences: SourceExperience[];
  created_at: string;
  updated_at: string;
}

export interface TagNode {
  id: string;
  name: string;
  tag_type: string;
  parent_id?: string;
  description?: string;
  children?: TagNode[];
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

export interface SignalUpdate {
  title?: string;
  url?: string;
  signal_type?: string;
  source_id?: string;
  organization_id?: string;
  abstract?: string;
  content?: string;
  published_at?: string;
  status?: string;
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
  introduction?: string;
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

export interface AIStatus {
  embeddings_enabled: boolean;
  chat_enabled: boolean;
  embedding_model: string;
  llm_model: string;
}

export interface SearchHit {
  object_type: string;
  object_id: string;
  name: string;
  description?: string;
  score: number;
}

export interface AskResponse {
  answer: string;
  sources: SearchHit[];
}

export interface DigestHighlight {
  signal_id?: string;
  title: string;
  url?: string;
  signal_type?: string;
  reason?: string;
}

export interface DailyDigest {
  id: string;
  digest_date: string;
  summary?: string;
  highlights: DigestHighlight[];
  signal_count: number;
  model_name?: string;
  created_at: string;
  updated_at: string;
}

export interface FundingEvent {
  id: string;
  company_name: string;
  organization_id?: string;
  round?: string;
  amount_usd?: number;
  amount_raw?: string;
  currency?: string;
  investors: string[];
  sector?: string;
  announced_at?: string;
  source_url?: string;
  description?: string;
  extracted_by?: string;
  created_at: string;
  updated_at: string;
}

export type FundingCreate = Omit<FundingEvent, 'id' | 'created_at' | 'updated_at'>;
export type FundingUpdate = Partial<FundingCreate>;

export interface FundingTrendBucket {
  count: number;
  amount_usd: number;
}

export interface FundingTrends {
  total_count: number;
  total_amount_usd: number;
  by_month: (FundingTrendBucket & { month: string })[];
  by_round: (FundingTrendBucket & { round: string })[];
  by_sector: (FundingTrendBucket & { sector: string })[];
}
