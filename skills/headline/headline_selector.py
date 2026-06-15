"""v8.0 Headline selector (vendored from HH-Research daily-digest, Plan v3 §6.1).

Takes a list of already-classified signals and decides:
  - which go to auto_headline (constraint_pass = True)
  - which go to edge_case (constraint_pass = False but m1+..+m5 >= threshold)
  - the rest stays as body signals

Also handles same-day-same-company merge: when multiple signals share
``canonical_event_key``, keep only the strongest (highest m-sum + constraint_pass).

Imports rewired to the local vendored ``schemas`` + stdlib logging.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass

from .schemas import Signal

log = logging.getLogger("headline_selector")

EDGE_CASE_THRESHOLD = 2  # sum of m1-m5 >= this AND not constraint_pass
MAX_AUTO_HEADLINES_PER_DAY = 2  # safety cap per Plan v3 §3 design


@dataclass
class SelectionResult:
    auto_headlines: list[Signal]              # constraint_pass=True, deduped, ranked
    edge_cases: list[Signal]                  # candidates for review, ranked
    body_signals: list[Signal]                # rest, unchanged
    suppressed: list[tuple[Signal, str]]      # (signal, reason) for audit


class HeadlineSelector:
    def __init__(
        self,
        edge_case_threshold: int = EDGE_CASE_THRESHOLD,
        max_auto_per_day: int = MAX_AUTO_HEADLINES_PER_DAY,
    ) -> None:
        self.edge_case_threshold = edge_case_threshold
        self.max_auto_per_day = max_auto_per_day

    @staticmethod
    def _m_sum(s: Signal) -> int:
        return sum(filter(None, [s.m1_score, s.m2_score, s.m3_score, s.m4_score, s.m5_score]))

    def select(self, signals: list[Signal]) -> SelectionResult:
        # 1. Group by canonical_event_key for same-day merge
        groups: dict[str, list[Signal]] = defaultdict(list)
        for s in signals:
            key = s.canonical_event_key or f"_solo:{s.source_id}"
            groups[key].append(s)

        suppressed: list[tuple[Signal, str]] = []
        winners: list[Signal] = []
        for key, group in groups.items():
            if len(group) == 1:
                winners.append(group[0])
                continue
            group_sorted = sorted(
                group,
                key=lambda s: (s.constraint_pass, self._m_sum(s)),
                reverse=True,
            )
            winners.append(group_sorted[0])
            for loser in group_sorted[1:]:
                suppressed.append((loser, f"merged with {group_sorted[0].source_id}"))

        # 2. Split into auto / edge / body
        auto: list[Signal] = []
        edge: list[Signal] = []
        body: list[Signal] = []

        winners_sorted = sorted(
            winners, key=lambda s: (s.constraint_pass, self._m_sum(s)), reverse=True
        )

        for s in winners_sorted:
            if s.constraint_pass and len(auto) < self.max_auto_per_day:
                s.auto_headline = True
                auto.append(s)
            elif s.constraint_pass:
                s.auto_headline = False
                s.edge_case = True
                edge.append(s)
                suppressed.append((s, f"auto cap {self.max_auto_per_day} reached, demoted to edge"))
            elif self._m_sum(s) >= self.edge_case_threshold:
                s.edge_case = True
                edge.append(s)
            else:
                body.append(s)

        log.info(
            "selected: %d auto, %d edge, %d body, %d suppressed",
            len(auto), len(edge), len(body), len(suppressed),
        )
        return SelectionResult(
            auto_headlines=auto, edge_cases=edge,
            body_signals=body, suppressed=suppressed,
        )


__all__ = ["HeadlineSelector", "SelectionResult", "EDGE_CASE_THRESHOLD",
           "MAX_AUTO_HEADLINES_PER_DAY"]
