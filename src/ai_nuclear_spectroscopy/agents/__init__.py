"""Model-independent scientific-agent protocol."""

from .protocol import (
    ScientificStage,
    build_agent_iteration_trace,
    build_agent_reviews,
    require_human_approval,
    select_review_candidate,
)

__all__ = [
    "ScientificStage",
    "build_agent_iteration_trace",
    "build_agent_reviews",
    "require_human_approval",
    "select_review_candidate",
]
