"""Collector base class. All data-source collectors implement this interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterable

from ..storage.schemas import Signal, WhitelistEntry


class CollectorBase(ABC):
    """Abstract collector. One per upstream data source (X, arXiv, ...)."""

    source_name: str = ""  # e.g. "x" or "arxiv"

    @abstractmethod
    def collect(
        self,
        whitelist: list[WhitelistEntry],
        since: datetime,
        until: datetime,
    ) -> Iterable[Signal]:
        """Yield Signal instances for items in [since, until) authored by whitelist entries.

        Implementations should:
        - Respect rate limits of the upstream API.
        - Set `source`, `source_id`, `author_name`, `url`, `raw_text`, `created_at`, `fetched_at`.
        - Leave `author_record_id` as None unless the implementation matches internally;
          the pipeline will later resolve author_record_id against the whitelist.
        - NOT deduplicate: dedup is handled by the pipeline via DedupStore.
        """
        raise NotImplementedError
