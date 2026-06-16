"""Idempotent bootstrap of the initial user accounts on startup.

Parses ``settings.seed_users`` ("user:pass,user2:pass2") and inserts any
usernames that don't exist yet. Existing accounts are left untouched so an
operator can change passwords without them being reset on the next deploy.
"""
import logging

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.models import User

logger = logging.getLogger(__name__)


def _parse_seed_users(raw: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for chunk in (raw or "").split(","):
        chunk = chunk.strip()
        if not chunk or ":" not in chunk:
            continue
        username, password = chunk.split(":", 1)
        username, password = username.strip(), password.strip()
        if username and password:
            pairs.append((username, password))
    return pairs


async def seed_users() -> None:
    settings = get_settings()
    pairs = _parse_seed_users(settings.seed_users)
    if not pairs:
        return
    async with AsyncSessionLocal() as db:
        existing = set(
            (await db.execute(select(User.username))).scalars().all()
        )
        created = 0
        for username, password in pairs:
            if username in existing:
                continue
            db.add(User(
                username=username,
                password_hash=hash_password(password),
                display_name=username,
            ))
            created += 1
        if created:
            await db.commit()
            logger.info("Seeded %d initial user(s)", created)
