export interface Entity {
  id: string;
  name: string;
  canonical_name: string;
  entity_type: string;
  introduction?: string | null;
  homepage_url?: string | null;
  metadata?: Record<string, unknown>;
}

export interface EntityRelation {
  id: string;
  subject_entity_id: string;
  object_entity_id: string;
  relation_type: string;
  subject?: Entity;
  object_entity?: Entity;
}

export interface KbSource {
  object_type: string;
  object_id: string;
  name: string;
  description?: string | null;
  score?: number | null;
  wiki_url?: string | null;
}

export interface ResearchScope {
  topic_ids?: string[];
  lane_ids?: string[];
  paper_ids?: string[];
  person_ids?: string[];
  org_ids?: string[];
  core_people?: CorePerson[];
  route_categories?: Array<{ key: string; label: string }>;
  paper_categories?: Record<string, string>;
  topic_catalog?: Array<{
    id: string;
    name: string;
    level?: string;
    lane_key?: string;
    row_key?: string;
    color?: string;
  }>;
}

export interface CorePerson {
  id: string;
  name: string;
  org?: string;
  wiki_url?: string;
}

export interface PersonSignal {
  person_id?: string;
  person?: string;
  title?: string;
  summary?: string;
  url?: string;
  date?: string;
  wiki_url?: string;
}

export interface CapitalEvent {
  person_id?: string;
  person?: string;
  target?: string;
  round?: string;
  amount?: string;
  investors?: string;
  url?: string;
  date?: string;
  wiki_url?: string;
}

export interface FundingItem {
  person_id?: string;
  person?: string;
  company?: string;
  round?: string;
  amount?: string;
  url?: string;
  date?: string;
  wiki_url?: string;
}

export interface IndustryData {
  core_people?: CorePerson[];
  tech_signals?: Array<{ title: string; summary: string }>;
  impact_md?: string;
  person_signals?: PersonSignal[];
  capital?: CapitalEvent[];
  funding?: FundingItem[];
  sources?: Array<{ title: string; url: string }>;
}

export interface ResearchSession {
  id: string;
  question: string;
  status: 'running' | 'done' | 'failed';
  phase?: string | null;
  pct: number;
  brief?: string | null;
  subtopics?: string[];
  report?: string | null;
  sources?: Array<{ title: string; url: string }>;
  kb_sources?: KbSource[];
  scope?: ResearchScope | null;
  industry?: IndustryData | null;
  error?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResearchSessionListItem {
  id: string;
  question: string;
  status: string;
  phase?: string | null;
  pct: number;
  created_at: string;
  updated_at: string;
}

export interface FundingEvent {
  id: string;
  company_name: string;
  round?: string | null;
  amount_usd?: number | null;
  amount_raw?: string | null;
  sector?: string | null;
  announced_at?: string | null;
  source_url?: string | null;
  description?: string | null;
}

export interface Signal {
  id: string;
  title: string;
  url?: string | null;
  signal_type: string;
  published_at?: string | null;
  summary?: string | null;
}
