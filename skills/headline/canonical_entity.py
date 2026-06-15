"""Canonical entity extraction (Plan v3 §3.4).

Maps signal author_name to a canonical (primary_org, primary_person) pair
so that same-day same-company merge and cross-day suppression work.

Rules (in order):
1. Hard-coded company normalizer (officially-known accounts) → primary_org direct.
2. Whitelist lookup by record_id → use "组织" field as primary_org.
3. Whitelist lookup by name → use "组织" field.
4. Heuristic fallback: lowercase author_name; if Twitter handle-like, use that.

The canonical_event_key is constructed by classifier later from event_type +
primary_org + significant tokens. This module only handles entity normalization.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Hard-coded company name → canonical primary_org (lowercase)
COMPANY_CANONICAL_MAP: dict[str, str] = {
    # OpenAI
    "OpenAI": "openai",
    "OpenAI Developers": "openai",
    "Sam Altman": "openai",
    "Greg Brockman": "openai",
    "Mira Murati": "openai",
    "Jakub Pachocki": "openai",
    "Karina Nguyen": "openai",
    "Noam Brown": "openai",
    "Bob McGrew": "openai",
    "Shunyu Yao": "openai",
    "Cheng Lu": "openai",
    "Hyung Won Chung": "openai",
    "Jason Wei": "openai",
    # Anthropic
    "Anthropic": "anthropic",
    "Dario Amodei": "anthropic",
    "Daniela Amodei": "anthropic",
    "Chris Olah": "anthropic",
    "Jerry Wei": "anthropic",
    "John Schulman": "anthropic",
    # Google / GDM
    "Google": "google",
    "GoogleAI": "google",
    "Google AI Developers": "google",
    "Google Deepmind": "google-deepmind",
    "Google DeepMind": "google-deepmind",
    "Demis Hassabis": "google-deepmind",
    "Jeff Dean": "google",
    "Steven Johnson": "google",
    "Denny Zhou": "google-deepmind",
    "Neel Nanda": "google-deepmind",
    "Jon Barron": "google-deepmind",
    "Songyou Peng": "google-deepmind",
    "Fuzhao Xue": "google",
    "Mostafa Dehghani": "google",
    "Yi Tay": "google",  # bio says formerly Google now Reka co-founder; map to google for past works
    "TensorFlow": "google",
    # Meta
    "Meta": "meta",
    "AIatMeta": "meta",
    "Reality Labs at Meta": "meta",
    "Yann LeCun": "meta",
    "Mark Zuckerberg": "meta",
    "Jason Weston": "meta",
    "Ishan Misra": "meta",
    "Armen Aghajanyan": "meta",
    "Soumith Chintala": "meta",
    "Saining Xie": "nyu",  # NYU but Meta collab
    # xAI
    "xAI": "xai",
    "Elon Musk": "xai",
    "Hieu Pham": "xai",
    "Lianmin Zheng": "xai",
    "Greg Yang": "xai",
    "Yuhuai (Tony) Wu": "xai",
    # Microsoft
    "Microsoft": "microsoft",
    "MSR": "microsoft",
    "Microsoft Research": "microsoft",
    "Jianfeng Gao": "microsoft",
    "Dylan Foster": "microsoft",
    "Can Xu": "microsoft",
    "Chunyuan Li": "microsoft",
    # NVIDIA
    "NVIDIA": "nvidia",
    "NVIDIA AI": "nvidia",
    "NVIDIA AI Developer": "nvidia",
    "Jim Fan": "nvidia",
    "Peng Xu": "nvidia",
    # Apple
    "Apple": "apple",
    "Jiatao Gu": "apple",
    # DeepSeek
    "Deepseek": "deepseek",
    "DeepSeek": "deepseek",
    # Mistral
    "Mistral AI": "mistral",
    # Alibaba
    "Alibaba Cloud": "alibaba",
    "Alibaba": "alibaba",
    # 创业公司 (拆细对应)
    "Andrej Karpathy": "eureka-labs",
    "hardmaru": "sakana-ai",
    "Jiaming Song": "luma-ai",
    "Brett Adcock": "figure-ai",
    "Daniel Han": "unsloth-ai",
    "Kyle Corbitt": "openpipe-ai",
    "François Chollet": "arc-prize",
    "Andrew Ng": "deeplearning-ai",
    "Junnan Li": "rhymes-ai",
    "Ross Taylor": "ross-taylor-new-co",  # TBD
    # Perplexity / Together / Sakana / others P0+
    "Perplexity": "perplexity",
    "Together AI": "together-ai",
    "Sakana AI": "sakana-ai",
    "Figure AI": "figure-ai",
    "Unitree": "unitree",
    "Hugging Face": "huggingface",
    "ElevenLabs": "elevenlabs",
    # 国产 P0
    "Alibaba Cloud": "alibaba",
    "MiniMax": "minimax",
    "Junxian He": "minimax",
    "Wenhu Chen": "waterloo",  # has dual: Waterloo + GDM
    # Robotics / 单条 P0+
    "World Labs": "world-labs",
    "Physical Intelligence": "physical-intelligence",
    "Scale AI": "scale-ai",
    "Liquid AI": "liquid-ai",
    "Genmo": "genmo",
    "Isomorphic Labs": "isomorphic-labs",
    "EleutherAI": "eleutherai",
    "AGI House": "agi-house",
    # 学界 (用 university 作为 primary_org)
    "Fei-Fei Li": "stanford",
    "Percy Liang": "stanford",
    "Chelsea Finn": "stanford",
    "Tengyu Ma": "stanford",
    "Jiajun Wu": "stanford",
    "Song Han": "mit",
    "Tri Dao": "princeton",
    "Sergey Levine": "ucb",
    "Pieter Abbeel": "ucb",
    "Albert Gu": "cmu",
    "Beidi Chen": "cmu",
    "Xiang Yue": "cmu",
    "Ziwei Liu": "ntu",
    "Yejin Choi": "uw",
    "Ilya Sutskever": "ssi",  # founded SSI
    # 媒体 (P1)
    "TechCrunch": "techcrunch",
    "Hacker News Bot": "hackernews",
    "Dwarkesh Patel": "dwarkesh",
    # Other commonly seen
    "Rohan Paul": "independent",
}

# Strip prefix patterns from author_name to find canonical
_X_HANDLE_RE = re.compile(r"^@?([A-Za-z0-9_]+)$")


@dataclass(frozen=True)
class CanonicalEntity:
    primary_org: str            # lowercase canonical org, e.g. "openai"
    primary_person: str | None  # lowercase canonical person, e.g. "sam-altman"

    @property
    def merge_key(self) -> str:
        """Key used for same-day same-company merge.
        For person signals from a P0 company, merge on company; otherwise person.
        """
        return self.primary_org


def canonicalize(author_name: str, organization: str | None = None) -> CanonicalEntity:
    """Map author_name (and optional org from whitelist) to CanonicalEntity.

    Args:
        author_name: from Signal.author_name (e.g. "Sam Altman")
        organization: optional, from Bitable whitelist "组织" field
                      (e.g. "OpenAI") for fallback when not in map

    Returns:
        CanonicalEntity with primary_org always set, primary_person if name was person.
    """
    if not author_name:
        return CanonicalEntity(primary_org="unknown", primary_person=None)

    name = author_name.strip()

    # 1. Direct map hit
    if name in COMPANY_CANONICAL_MAP:
        org = COMPANY_CANONICAL_MAP[name]
        # If name has space → person; else → company-itself
        is_person = " " in name and not _looks_like_company_name(name)
        person = _person_slug(name) if is_person else None
        return CanonicalEntity(primary_org=org, primary_person=person)

    # 2. Organization fallback
    if organization:
        org_normalized = _normalize_org(organization)
        is_person = " " in name and not _looks_like_company_name(name)
        person = _person_slug(name) if is_person else None
        return CanonicalEntity(primary_org=org_normalized, primary_person=person)

    # 3. Heuristic: name is org-like ("World Labs", "TechCrunch")
    if _looks_like_company_name(name):
        return CanonicalEntity(primary_org=_normalize_org(name), primary_person=None)

    # 4. Person without known company
    person = _person_slug(name)
    return CanonicalEntity(primary_org="unknown", primary_person=person)


def _looks_like_company_name(name: str) -> bool:
    """Heuristic: does this name look like a company/org rather than a person?"""
    keywords = (
        "AI", "Labs", "Lab", "Cloud", "Research", "Inc", "Corp",
        "Foundation", "Tech", "OpenAI", "DeepMind", "Anthropic", "Meta",
        "Google", "NVIDIA", "Apple", "Microsoft", "xAI", "Reality Labs",
        "Developers", "TensorFlow", "Hugging Face", "Robotics",
    )
    return any(k in name for k in keywords)


def _normalize_org(s: str) -> str:
    """Normalize organization string → canonical slug."""
    s = s.strip().lower()
    s = s.replace(" deepmind", "-deepmind")  # google deepmind → google-deepmind
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^a-z0-9\-]", "", s)
    return s or "unknown"


def _person_slug(name: str) -> str:
    """Convert person name to slug, e.g. 'Sam Altman' → 'sam-altman'."""
    slug = name.strip().lower()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    return slug or "unknown"


def build_event_key(
    entity: CanonicalEntity,
    event_type: str | None,
    significant_terms: list[str] | None = None,
    raw_text: str | None = None,
) -> str:
    """Build canonical_event_key from PRIMARY ENTITY IN RAW_TEXT + event_type + key terms.

    Product-level merge for ① events: if a flagship product name is found in
    raw_text (e.g. "Gemini 3.5 Flash" / "Qwen3.7-Max"), use it as the primary
    merge key, so two signals about the same product from different authors
    (Jeff Dean + Demis Hassabis) merge into one canonical_event_key.

    Org normalization: google / google-deepmind / google-ai are conflated for
    canonical purposes (they share product/event lines).

    Examples:
      - 'Gemini 3.5 Flash' (Jeff Dean)     → 'google:①:gemini-3.5-flash' (same)
      - 'Gemini 3.5 Flash' (Demis Hassabis) → 'google:①:gemini-3.5-flash' (same)
      - 'Huawei tau scaling law' (Rohan Paul) → 'huawei:③:scaling-law:tau'
    """
    # Prefer in-text primary entity over author entity
    text_org = _extract_primary_org_from_text(raw_text) if raw_text else None
    primary = text_org or entity.primary_org
    # Conflate google variants for merge purposes
    primary = _normalize_for_merge(primary)

    parts = [primary]
    if event_type:
        parts.append(event_type[0] if event_type else "?")

    # Try canonical concept extraction for ALL event types (was only ①).
    # This lets ③ hardware events (τ Scaling Law / LogicFolding) and others
    # share a stable key across days, enabling cross-day suppression.
    if raw_text:
        concept = _extract_canonical_product_name(raw_text)
        if concept:
            parts.append(concept)
            return ":".join(parts)

    if significant_terms:
        sorted_terms = sorted(set(t.lower().strip() for t in significant_terms if t))[:2]
        parts.extend(sorted_terms)
    return ":".join(parts)


def _normalize_for_merge(org_slug: str) -> str:
    """Conflate org variants that share product/event lines."""
    # Google family (google / google-deepmind / google-ai etc) → "google"
    if org_slug.startswith("google"):
        return "google"
    return org_slug


# Canonical product names → merge slugs (lowercase, dash-separated, no version
# tail differentiation when major-minor identical).
_PRODUCT_NAME_PATTERNS = [
    # OpenAI
    (re.compile(r"GPT-(\d+\.?\d*)\s*(Turbo|Pro|Ultra|o\d+)?", re.IGNORECASE),
     lambda m: f"gpt-{m.group(1)}"),
    (re.compile(r"\bSora\b", re.IGNORECASE), lambda m: "sora"),
    (re.compile(r"\bDALL-?E[-\s]?(\d+)?", re.IGNORECASE),
     lambda m: f"dall-e-{m.group(1)}" if m.group(1) else "dall-e"),
    # Anthropic
    (re.compile(r"Claude\s*(\d+(\.\d+)?)\s*(Opus|Sonnet|Haiku)?", re.IGNORECASE),
     lambda m: f"claude-{m.group(1)}" + (f"-{m.group(3).lower()}" if m.group(3) else "")),
    # Google - major version only (Flash/Pro/Ultra variants merge into same launch event)
    (re.compile(r"Gemini\s+(\d+(\.\d+)?)", re.IGNORECASE),
     lambda m: f"gemini-{m.group(1)}"),
    (re.compile(r"\bGemma\b", re.IGNORECASE), lambda m: "gemma"),
    # Meta
    (re.compile(r"Llama\s*(\d+(\.\d+)?)\s*(B|Instruct)?", re.IGNORECASE),
     lambda m: f"llama-{m.group(1)}"),
    # xAI
    (re.compile(r"Grok\s*(\d+(\.\d+)?)?", re.IGNORECASE),
     lambda m: f"grok-{m.group(1)}" if m.group(1) else "grok"),
    # Alibaba
    (re.compile(r"Qwen\s*[-\.]?\s*(\d+(\.\d+)?)\s*[-\.]?\s*(Max|Plus|Turbo)?",
                re.IGNORECASE),
     lambda m: f"qwen-{m.group(1)}" + (f"-{m.group(3).lower()}" if m.group(3) else "")),
    # DeepSeek
    (re.compile(r"DeepSeek\s*[-]?\s*([VRvr]\d+(\.\d+)?)", re.IGNORECASE),
     lambda m: f"deepseek-{m.group(1).lower()}"),
    # Mistral
    (re.compile(r"Mistral\s*(Large|Medium|Small)?\s*(\d+(\.\d+)?)?", re.IGNORECASE),
     lambda m: f"mistral-{(m.group(1) or m.group(2) or 'unknown').lower()}"),
    # MiniMax
    (re.compile(r"MiniMax[-\s]?M(\d+(\.\d+)?)", re.IGNORECASE),
     lambda m: f"minimax-m{m.group(1)}"),
    # NVIDIA
    (re.compile(r"\b(SANA-WM|LongLive-?\d+|DGX\s+\w+)\b", re.IGNORECASE),
     lambda m: m.group(1).lower().replace(" ", "-")),
    # ③ Hardware concepts (so 5-25 / 5-27 same event suppresses cross-day)
    (re.compile(r"(τ|Tau|tau)\s*[Ss]caling\s*Law", re.IGNORECASE),
     lambda m: "tau-scaling-law"),
    (re.compile(r"LogicFolding", re.IGNORECASE),
     lambda m: "logic-folding"),
    (re.compile(r"τ\s*\(?[Tt]au\)?\s*Scaling", re.IGNORECASE),
     lambda m: "tau-scaling-law"),
    # Common AI infra concepts
    (re.compile(r"\bHBM\d*\b", re.IGNORECASE), lambda m: "hbm"),
    (re.compile(r"\b(NVLink|TPU\s*v\d+|H100|B200|GB200)\b", re.IGNORECASE),
     lambda m: m.group(1).lower().replace(" ", "-")),
]


def _extract_canonical_product_name(text: str) -> str | None:
    """Extract first canonical product name from raw_text for merge key.

    Used by build_event_key for ALL event types (product/concept-level merge
    enables cross-day suppression for the same concept across different
    wordings, e.g. 'τ Scaling Law' vs 'Tau (τ) Scaling Law').

    Co-occurrence checks run FIRST so conceptual events (with related
    technologies like LogicFolding mentioned alongside) merge correctly.
    """
    # Co-occurrence FIRST (most specific): τ/Tau + Scaling Law in any order
    # (catches "τ Scaling Law (Her's Law)" AND "Tau (τ) Scaling Law" AND
    # "LogicFolding/τ Scaling Law" — all map to one concept)
    has_tau = bool(re.search(r"(τ|\bTau\b|\btau\b)", text))
    has_scaling_law = bool(re.search(r"[Ss]caling\s*[Ll]aw", text))
    if has_tau and has_scaling_law:
        return "tau-scaling-law"

    # Then iterate specific product/concept patterns
    for pat, slugger in _PRODUCT_NAME_PATTERNS:
        m = pat.search(text)
        if m:
            return slugger(m).lower()

    return None


# Common in-text entity markers → canonical org slug.
# Note: \b word boundaries don't work with CJK tokens (Python \b is
# ASCII-alphanumeric based), so use plain substring matching for Chinese.
_TEXT_ORG_PATTERNS = [
    # Huawei (English uses \b; Chinese 华为 uses plain substring)
    (re.compile(r"Huawei|华为", re.IGNORECASE), "huawei"),
    (re.compile(r"\bOpenAI\b", re.IGNORECASE), "openai"),
    (re.compile(r"\bAnthropic\b", re.IGNORECASE), "anthropic"),
    (re.compile(r"\bGoogle\s+DeepMind\b|\bDeepMind\b", re.IGNORECASE), "google-deepmind"),
    (re.compile(r"\bGoogle\b|谷歌", re.IGNORECASE), "google"),
    (re.compile(r"\bMeta\b", re.IGNORECASE), "meta"),
    (re.compile(r"\bMicrosoft\b|\bMSR\b|微软", re.IGNORECASE), "microsoft"),
    (re.compile(r"\bxAI\b", re.IGNORECASE), "xai"),
    (re.compile(r"\bNVIDIA\b|英伟达", re.IGNORECASE), "nvidia"),
    (re.compile(r"\bApple\b|苹果", re.IGNORECASE), "apple"),
    (re.compile(r"\bDeepSeek\b", re.IGNORECASE), "deepseek"),
    (re.compile(r"\bMistral\b", re.IGNORECASE), "mistral"),
    (re.compile(r"\bAlibaba\b|阿里|Qwen", re.IGNORECASE), "alibaba"),
    (re.compile(r"\bFigure\s+AI\b", re.IGNORECASE), "figure-ai"),
    (re.compile(r"\bCerebras\b", re.IGNORECASE), "cerebras"),
    (re.compile(r"\bSakana\b", re.IGNORECASE), "sakana-ai"),
    (re.compile(r"\bHark\b", re.IGNORECASE), "hark"),
    (re.compile(r"MiniMax", re.IGNORECASE), "minimax"),
]


def _extract_primary_org_from_text(text: str) -> str | None:
    """Return canonical org slug of first matched company in text, or None."""
    for pat, slug in _TEXT_ORG_PATTERNS:
        if pat.search(text):
            return slug
    return None
