"""Generate seed data as plain SQL INSERT statements (no DB connection needed)."""
import uuid
from datetime import datetime, timezone

def uid():
    return str(uuid.uuid4())

lines = []

def sql(stmt):
    lines.append(stmt)

# ── Organizations ──────────────────────────────────────────────────────────────
org_ids = {}
orgs = [
    ("xAI",            "company", "US", "https://x.ai",           "Elon Musk's AI company building Grok."),
    ("Meta",           "company", "US", "https://ai.meta.com",    "Meta AI research, Llama series."),
    ("OpenAI",         "company", "US", "https://openai.com",     "Maker of GPT and ChatGPT."),
    ("Google DeepMind","lab",     "US", "https://deepmind.google","DeepMind and Google Brain merged AI lab."),
    ("NVIDIA",         "company", "US", "https://nvidia.com",     "GPU computing and AI infrastructure."),
]
for name, otype, country, url, desc in orgs:
    oid = uid()
    org_ids[name] = oid
    sql(f"INSERT INTO organizations (id, name, org_type, country, website_url, description) VALUES "
        f"('{oid}', $${name}$$, '{otype}', '{country}', '{url}', $${desc}$$);")

# ── Tags ───────────────────────────────────────────────────────────────────────
tag_ids = {}
for tag in ["MLSys","Reasoning","Multimodal","Efficient LLM","Generative AI",
            "Theory","RL","Pretrain","AI Agents","AI Safety","RAG"]:
    tid = uid()
    tag_ids[tag] = tid
    sql(f"INSERT INTO tags (id, name, tag_type) VALUES ('{tid}', $${tag}$$, 'topic');")

# ── Sources ────────────────────────────────────────────────────────────────────
src = {}
def make_src(name, stype, org, aff, importance=0.8):
    sid = uid()
    src[name] = sid
    org_val = f"'{org_ids[org]}'" if org else "NULL"
    sql(f"INSERT INTO sources (id, name, source_type, organization_id, affiliation_type, "
        f"activity_status, importance_score, reliability_score) VALUES "
        f"('{sid}', $${name}$$, '{stype}', {org_val}, '{aff}', 'active', {importance}, 0.8);")
    return sid

make_src("xAI",               "organization","xAI",  "industry")
make_src("Hieu Pham",         "person",      "xAI",  "industry", 0.85)
make_src("Liam Zheng",        "person",      "xAI",  "industry")
make_src("Qian Huang",        "person",      "xAI",  "industry")
make_src("Greg Yang",         "person",      "xAI",  "industry")
make_src("Meta",              "organization","Meta", "industry")
make_src("Reality Labs at Meta","organization","Meta","industry")
make_src("Yi Wan",            "person",      "Meta", "industry")
make_src("Mike Lewis",        "person",      "Meta", "industry")

# Source accounts
for handle, platform, url, sname in [
    ("hyhieu226",  "x","https://x.com/hyhieu226",  "Hieu Pham"),
    ("lm_zheng",   "x","https://x.com/lm_zheng",   "Liam Zheng"),
    ("qhwang3",    "x","https://x.com/qhwang3",     "Qian Huang"),
    ("TheGregYang","x","https://x.com/TheGregYang", "Greg Yang"),
]:
    sql(f"INSERT INTO source_accounts (id, source_id, platform, handle, url, is_primary) VALUES "
        f"('{uid()}', '{src[sname]}', '{platform}', '{handle}', '{url}', true);")

# Source tags
for sname, tname in [("Hieu Pham","MLSys"),("Liam Zheng","MLSys"),("Qian Huang","Reasoning"),
                     ("Greg Yang","Theory"),("Yi Wan","RL"),("Mike Lewis","Pretrain"),
                     ("Reality Labs at Meta","Multimodal")]:
    sql(f"INSERT INTO source_tags (source_id, tag_id, assigned_by) VALUES "
        f"('{src[sname]}', '{tag_ids[tname]}', 'manual');")

# ── Entities ──────────────────────────────────────────────────────────────────
ent = {}
for name, canonical, etype, desc, homepage in [
    ("xAI",       "xAI",       "organization","Elon Musk's AI company.",               "https://x.ai"),
    ("Meta",      "Meta",      "organization","Meta AI research.",                     "https://ai.meta.com"),
    ("Grok",      "Grok",      "model",       "Large language model by xAI.",          None),
    ("Llama",     "Llama",     "model",       "Open-weight LLM series by Meta.",       None),
    ("KV Cache",  "KV Cache",  "method",      "Key-value caching for transformer inference.", None),
    ("MLSys",     "MLSys",     "topic",       "Machine Learning Systems research.",    None),
    ("Reasoning", "Reasoning", "topic",       "Logical and mathematical reasoning in LLMs.", None),
    ("Hieu Pham", "Hieu Pham", "person",      "ML researcher at xAI.",                 None),
]:
    eid = uid()
    ent[name] = eid
    hp = f"'{homepage}'" if homepage else "NULL"
    sql(f"INSERT INTO entities (id, name, canonical_name, entity_type, description, homepage_url, metadata) VALUES "
        f"('{eid}', $${name}$$, $${canonical}$$, '{etype}', $${desc}$$, {hp}, '{{}}');")

# Entity aliases
llama_id = ent["Llama"]
kvcache_id = ent["KV Cache"]
sql(f"INSERT INTO entity_aliases (id, entity_id, alias, alias_type) VALUES "
    f"('{uid()}', '{llama_id}', 'LLaMA', 'old_name');")
sql(f"INSERT INTO entity_aliases (id, entity_id, alias, alias_type) VALUES "
    f"('{uid()}', '{kvcache_id}', 'Key-Value Cache', 'full_name');")

# ── Signals ───────────────────────────────────────────────────────────────────
sig = {}
def make_sig(key, source, org, title, url, stype, abstract, published, status="processed"):
    sid = uid()
    sig[key] = sid
    org_val = f"'{org_ids[org]}'" if org else "NULL"
    pub = f"'{published}'" if published else "NULL"
    abs_val = f"$${abstract}$$" if abstract else "NULL"
    sql(f"INSERT INTO signals (id, source_id, organization_id, title, url, signal_type, abstract, "
        f"published_at, status, raw_metadata) VALUES "
        f"('{sid}', '{src[source]}', {org_val}, $${title}$$, '{url}', '{stype}', "
        f"{abs_val}, {pub}, '{status}', '{{}}');")
    return sid

make_sig("paper","Hieu Pham","xAI",
         "FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision",
         "https://arxiv.org/abs/2407.08608","paper",
         "We develop FlashAttention-3 that leverages new hardware features on Hopper GPUs.",
         "2024-07-11T00:00:00+00:00")
make_sig("blog","Meta","Meta",
         "Introducing Llama 3: The Most Capable Openly Available LLM",
         "https://ai.meta.com/blog/meta-llama-3/","blog",
         "Meta releases Llama 3 with 8B and 70B parameter models.",
         "2024-04-18T00:00:00+00:00")
make_sig("tweet","Greg Yang",None,
         "Greg Yang on Tensor Programs and scaling theory",
         "https://x.com/TheGregYang/status/1234567890","tweet",
         "New results on infinite-width limits and feature learning...",
         "2024-03-01T00:00:00+00:00","collected")
make_sig("model","xAI","xAI",
         "Grok-1.5 Release","https://x.ai/blog/grok-1.5","model_release",
         "xAI releases Grok-1.5 with improved reasoning capabilities.",
         "2024-03-28T00:00:00+00:00")

# Signal analysis
paper_id = sig["paper"]
model_id = sig["model"]
sql(f"INSERT INTO signal_analysis (id, signal_id, tldr, summary, why_it_matters, "
    f"technical_points, importance_score, novelty_score, relevance_score, confidence_score, "
    f"reading_priority, topic_tags, entities, metadata) VALUES "
    f"('{uid()}', '{paper_id}', "
    f"$$FlashAttention-3 achieves up to 740 TFLOPs/s on H100 GPUs.$$, "
    f"$$Leverages async execution and low-precision math for faster attention.$$, "
    f"$$Directly reduces LLM training and inference cost.$$, "
    f"ARRAY['Warp specialization','Pingpong scheduling','FP8 quantization'], "
    f"0.95, 0.9, 0.9, 0.95, 'must_read', ARRAY['MLSys','Efficient LLM'], "
    f"ARRAY['FlashAttention','xAI','Hieu Pham'], '{{}}');")
sql(f"INSERT INTO signal_analysis (id, signal_id, tldr, summary, importance_score, "
    f"novelty_score, relevance_score, confidence_score, reading_priority, topic_tags, entities, metadata) VALUES "
    f"('{uid()}', '{model_id}', "
    f"$$Grok-1.5 shows strong performance on MATH and HumanEval.$$, "
    f"$$xAI latest model with enhanced reasoning.$$, "
    f"0.85, 0.7, 0.85, 0.9, 'recommended', ARRAY['Reasoning','Generative AI'], "
    f"ARRAY['Grok','xAI'], '{{}}');")

# Signal entities
for sk, ek, role in [
    ("paper","KV Cache","method"), ("paper","MLSys","topic"),
    ("paper","Hieu Pham","author"), ("paper","xAI","publisher"),
    ("blog","Llama","main_subject"), ("blog","Meta","publisher"),
    ("model","Grok","main_subject"), ("model","xAI","publisher"),
    ("tweet","Hieu Pham","author"),
]:
    sql(f"INSERT INTO signal_entities (signal_id, entity_id, role, confidence, extracted_by) VALUES "
        f"('{sig[sk]}', '{ent[ek]}', '{role}', 1.0, 'manual');")

# ── Entity Relations ───────────────────────────────────────────────────────────
for subj, rtype, obj in [
    ("Hieu Pham","WORKS_AT","xAI"),
    ("xAI","RELEASED","Grok"),
    ("Meta","RELEASED","Llama"),
    ("KV Cache","RELATED_TO","MLSys"),
    ("Grok","FOCUSES_ON","Reasoning"),
]:
    sql(f"INSERT INTO entity_relations (id, subject_entity_id, relation_type, object_entity_id, "
        f"confidence, extracted_by) VALUES "
        f"('{uid()}', '{ent[subj]}', '{rtype}', '{ent[obj]}', 1.0, 'manual');")

# ── Pipeline Run ───────────────────────────────────────────────────────────────
sql(f"INSERT INTO pipeline_runs (id, run_type, status, total_items, success_items, failed_items, metadata) VALUES "
    f"('{uid()}', 'collect', 'success', 4, 4, 0, '{{\"source\": \"seed\"}}');")

# Write output
output = "\n".join(lines)
with open("../seed_supabase.sql", "w", encoding="utf-8") as f:
    f.write(output)

print(f"Generated {len(lines)} INSERT statements → seed_supabase.sql")
