"""
Seed script — populates the database with example data.
Run: python seed.py
"""
import asyncio
import uuid
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import get_settings
from app.models import (
    Organization, Source, SourceAccount, Tag, SourceTag,
    Signal, SignalAnalysis, Entity, EntityAlias, EntityRelation,
    SignalEntity, PipelineRun,
)

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False)
AsyncSession_ = async_sessionmaker(engine, expire_on_commit=False)


def uid() -> str:
    return str(uuid.uuid4())


async def seed(db: AsyncSession) -> None:
    # ── Organizations ─────────────────────────────────────────────────────────
    orgs: dict[str, Organization] = {}
    for org_data in [
        {"name": "xAI", "org_type": "company", "country": "US", "website_url": "https://x.ai", "description": "Elon Musk's AI company building Grok."},
        {"name": "Meta", "org_type": "company", "country": "US", "website_url": "https://ai.meta.com", "description": "Meta AI research, Llama series."},
        {"name": "OpenAI", "org_type": "company", "country": "US", "website_url": "https://openai.com", "description": "Maker of GPT and ChatGPT."},
        {"name": "Google DeepMind", "org_type": "lab", "country": "US", "website_url": "https://deepmind.google", "description": "DeepMind and Google Brain merged AI lab."},
        {"name": "NVIDIA", "org_type": "company", "country": "US", "website_url": "https://nvidia.com", "description": "GPU computing and AI infrastructure."},
    ]:
        obj = Organization(id=uid(), **org_data)
        db.add(obj)
        orgs[org_data["name"]] = obj

    await db.flush()

    # ── Tags ─────────────────────────────────────────────────────────────────
    tags: dict[str, Tag] = {}
    for tag_name in ["MLSys", "Reasoning", "Multimodal", "Efficient LLM", "Generative AI",
                     "Theory", "RL", "Pretrain", "AI Agents", "AI Safety", "RAG"]:
        obj = Tag(id=uid(), name=tag_name, tag_type="topic")
        db.add(obj)
        tags[tag_name] = obj

    await db.flush()

    # ── Sources ──────────────────────────────────────────────────────────────
    sources: dict[str, Source] = {}

    def make_source(name, source_type, org_name, affiliation, activity="active", importance=0.8) -> Source:
        return Source(
            id=uid(),
            name=name,
            source_type=source_type,
            organization_id=orgs[org_name].id if org_name else None,
            affiliation_type=affiliation,
            activity_status=activity,
            importance_score=importance,
            reliability_score=0.8,
        )

    src_xai = make_source("xAI", "organization", "xAI", "industry")
    src_hieu = make_source("Hieu Pham", "person", "xAI", "industry", importance=0.85)
    src_liam = make_source("Liam Zheng", "person", "xAI", "industry")
    src_qian = make_source("Qian Huang", "person", "xAI", "industry")
    src_greg = make_source("Greg Yang", "person", "xAI", "industry")
    src_meta = make_source("Meta", "organization", "Meta", "industry")
    src_rl = make_source("Reality Labs at Meta", "organization", "Meta", "industry")
    src_yi = make_source("Yi Wan", "person", "Meta", "industry")
    src_mike = make_source("Mike Lewis", "person", "Meta", "industry")

    for src in [src_xai, src_hieu, src_liam, src_qian, src_greg, src_meta, src_rl, src_yi, src_mike]:
        db.add(src)
    sources.update({s.name: s for s in [src_xai, src_hieu, src_liam, src_qian, src_greg, src_meta, src_rl, src_yi, src_mike]})
    await db.flush()

    # Source accounts
    accounts = [
        SourceAccount(id=uid(), source_id=src_hieu.id, platform="x", handle="hyhieu226", url="https://x.com/hyhieu226", is_primary=True),
        SourceAccount(id=uid(), source_id=src_liam.id, platform="x", handle="lm_zheng", url="https://x.com/lm_zheng", is_primary=True),
        SourceAccount(id=uid(), source_id=src_qian.id, platform="x", handle="qhwang3", url="https://x.com/qhwang3", is_primary=True),
        SourceAccount(id=uid(), source_id=src_greg.id, platform="x", handle="TheGregYang", url="https://x.com/TheGregYang", is_primary=True),
    ]
    for acc in accounts:
        db.add(acc)

    # Source tags
    st_pairs = [
        (src_hieu, "MLSys"), (src_liam, "MLSys"),
        (src_qian, "Reasoning"), (src_greg, "Theory"),
        (src_yi, "RL"), (src_mike, "Pretrain"),
        (src_rl, "Multimodal"),
    ]
    for src, tag_name in st_pairs:
        db.add(SourceTag(source_id=src.id, tag_id=tags[tag_name].id, assigned_by="manual"))

    await db.flush()

    # ── Entities ─────────────────────────────────────────────────────────────
    entities: dict[str, Entity] = {}
    entity_data = [
        ("xAI", "xAI", "organization", "Elon Musk's AI company.", "https://x.ai"),
        ("Meta", "Meta", "organization", "Meta AI research.", "https://ai.meta.com"),
        ("Grok", "Grok", "model", "Large language model by xAI.", None),
        ("Llama", "Llama", "model", "Open-weight LLM series by Meta.", None),
        ("KV Cache", "KV Cache", "method", "Key-value caching technique for transformer inference.", None),
        ("MLSys", "MLSys", "topic", "Machine Learning Systems research area.", None),
        ("Reasoning", "Reasoning", "topic", "Logical and mathematical reasoning in LLMs.", None),
        ("Hieu Pham", "Hieu Pham", "person", "ML researcher at xAI.", None),
    ]
    for name, canonical, etype, desc, url in entity_data:
        obj = Entity(id=uid(), name=name, canonical_name=canonical, entity_type=etype,
                     description=desc, homepage_url=url, metadata_={})
        db.add(obj)
        entities[name] = obj

    await db.flush()

    # Entity aliases
    db.add(EntityAlias(id=uid(), entity_id=entities["Llama"].id, alias="LLaMA", alias_type="old_name"))
    db.add(EntityAlias(id=uid(), entity_id=entities["KV Cache"].id, alias="Key-Value Cache", alias_type="full_name"))

    # ── Signals ───────────────────────────────────────────────────────────────
    from datetime import datetime, timezone

    signals: dict[str, Signal] = {}

    sig_paper = Signal(
        id=uid(), source_id=src_hieu.id, organization_id=orgs["xAI"].id,
        title="FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision",
        url="https://arxiv.org/abs/2407.08608",
        signal_type="paper",
        abstract="We develop FlashAttention-3 that leverages new hardware features on Hopper GPUs.",
        published_at=datetime(2024, 7, 11, tzinfo=timezone.utc),
        status="processed",
    )
    sig_blog = Signal(
        id=uid(), source_id=src_meta.id, organization_id=orgs["Meta"].id,
        title="Introducing Llama 3: The Most Capable Openly Available LLM",
        url="https://ai.meta.com/blog/meta-llama-3/",
        signal_type="blog",
        abstract="Meta releases Llama 3 with 8B and 70B parameter models.",
        published_at=datetime(2024, 4, 18, tzinfo=timezone.utc),
        status="processed",
    )
    sig_tweet = Signal(
        id=uid(), source_id=src_greg.id,
        title="Greg Yang on Tensor Programs and scaling theory",
        url="https://x.com/TheGregYang/status/1234567890",
        signal_type="tweet",
        content="New results on infinite-width limits and feature learning...",
        published_at=datetime(2024, 3, 1, tzinfo=timezone.utc),
        status="collected",
    )
    sig_model = Signal(
        id=uid(), source_id=src_xai.id, organization_id=orgs["xAI"].id,
        title="Grok-1.5 Release",
        url="https://x.ai/blog/grok-1.5",
        signal_type="model_release",
        abstract="xAI releases Grok-1.5 with improved reasoning capabilities.",
        published_at=datetime(2024, 3, 28, tzinfo=timezone.utc),
        status="processed",
    )

    for sig in [sig_paper, sig_blog, sig_tweet, sig_model]:
        db.add(sig)
        signals[sig.title[:20]] = sig

    await db.flush()

    # Signal analysis
    db.add(SignalAnalysis(
        id=uid(), signal_id=sig_paper.id,
        tldr="FlashAttention-3 achieves up to 740 TFLOPs/s on H100 GPUs.",
        summary="Leverages async execution and low-precision math for faster attention.",
        why_it_matters="Directly reduces LLM training and inference cost.",
        technical_points=["Warp specialization", "Pingpong scheduling", "FP8 quantization"],
        importance_score=0.95, novelty_score=0.9, relevance_score=0.9, confidence_score=0.95,
        reading_priority="must_read", topic_tags=["MLSys", "Efficient LLM"],
        entities=["FlashAttention", "xAI", "Hieu Pham"], metadata_={},
    ))
    db.add(SignalAnalysis(
        id=uid(), signal_id=sig_model.id,
        tldr="Grok-1.5 shows strong performance on MATH and HumanEval.",
        summary="xAI's latest model with enhanced reasoning.",
        importance_score=0.85, novelty_score=0.7, relevance_score=0.85, confidence_score=0.9,
        reading_priority="recommended", topic_tags=["Reasoning", "Generative AI"],
        entities=["Grok", "xAI"], metadata_={},
    ))

    await db.flush()

    # Signal entities
    se_data = [
        (sig_paper.id, entities["KV Cache"].id, "method"),
        (sig_paper.id, entities["MLSys"].id, "topic"),
        (sig_paper.id, entities["Hieu Pham"].id, "author"),
        (sig_paper.id, entities["xAI"].id, "publisher"),
        (sig_blog.id, entities["Llama"].id, "main_subject"),
        (sig_blog.id, entities["Meta"].id, "publisher"),
        (sig_model.id, entities["Grok"].id, "main_subject"),
        (sig_model.id, entities["xAI"].id, "publisher"),
        (sig_tweet.id, entities["Hieu Pham"].id, "author"),
    ]
    for sig_id, ent_id, role in se_data:
        db.add(SignalEntity(signal_id=sig_id, entity_id=ent_id, role=role, confidence=1.0, extracted_by="manual"))

    await db.flush()

    # ── Entity Relations ──────────────────────────────────────────────────────
    rel_data = [
        (entities["Hieu Pham"].id, "WORKS_AT", entities["xAI"].id),
        (entities["xAI"].id, "RELEASED", entities["Grok"].id),
        (entities["Meta"].id, "RELEASED", entities["Llama"].id),
        (entities["KV Cache"].id, "RELATED_TO", entities["MLSys"].id),
        (entities["Grok"].id, "FOCUSES_ON", entities["Reasoning"].id),
    ]
    for subj, rtype, obj in rel_data:
        db.add(EntityRelation(id=uid(), subject_entity_id=subj, relation_type=rtype, object_entity_id=obj, confidence=1.0, extracted_by="manual"))

    # ── Pipeline Runs ─────────────────────────────────────────────────────────
    db.add(PipelineRun(
        id=uid(), run_type="collect", status="success",
        total_items=4, success_items=4, failed_items=0, metadata_={"source": "seed"},
    ))

    await db.commit()
    print("✓ Seed data inserted successfully.")


async def main():
    async with AsyncSession_() as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
