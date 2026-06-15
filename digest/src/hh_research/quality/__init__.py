"""Quality gates for HH Research generated digest XML."""

from .digest_rules import (
    EXPLAIN_MAX_CHARS,
    INSIGHTS_MAX_CHARS,
    INSIGHTS_MIN_CHARS,
    ReviewIssue,
    ReviewReport,
    ReviewSeverity,
    review_xml_text,
    text_len_zh,
)

__all__ = [
    "EXPLAIN_MAX_CHARS",
    "INSIGHTS_MAX_CHARS",
    "INSIGHTS_MIN_CHARS",
    "ReviewIssue",
    "ReviewReport",
    "ReviewSeverity",
    "review_xml_text",
    "text_len_zh",
]
