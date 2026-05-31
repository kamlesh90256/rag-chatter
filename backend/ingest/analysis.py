from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class EngagementResult:
    engagement_rate: float
    comparison_table: list[dict[str, Any]]
    winner: str


@dataclass
class HookResult:
    hook_score: int
    curiosity_score: int
    emotion_score: int
    retention_score: int
    cta_score: int
    reasoning: str


HOOK_WORDS = {
    "watch",
    "wait",
    "stop",
    "discover",
    "why",
    "how",
    "secret",
    "insane",
    "shocking",
    "before",
}
CTA_WORDS = {"follow", "subscribe", "comment", "save", "share", "link", "dm", "join"}
EMOTION_WORDS = {
    "amazing",
    "crazy",
    "funny",
    "surprised",
    "love",
    "angry",
    "excited",
    "shocked",
}


def calculate_engagement_rate(likes: int, comments: int, views: int) -> float:
    if views <= 0:
        return 0.0
    return round(((likes + comments) / views) * 100, 2)


def build_comparison_table(
    video_a: dict[str, Any], video_b: dict[str, Any]
) -> EngagementResult:
    likes_a = int(video_a.get("likes") or 0)
    comments_a = int(video_a.get("comments") or 0)
    views_a = int(video_a.get("views") or 0)
    likes_b = int(video_b.get("likes") or 0)
    comments_b = int(video_b.get("comments") or 0)
    views_b = int(video_b.get("views") or 0)
    engagement_a = calculate_engagement_rate(
        likes_a,
        comments_a,
        views_a,
    )
    engagement_b = calculate_engagement_rate(
        likes_b,
        comments_b,
        views_b,
    )
    winner = str(video_a.get("title") or "Video A") if engagement_a >= engagement_b else str(video_b.get("title") or "Video B")
    return EngagementResult(
        engagement_rate=max(engagement_a, engagement_b),
        comparison_table=[
            {
                "metric": "Views",
                "video_a": views_a,
                "video_b": views_b,
            },
            {
                "metric": "Likes",
                "video_a": likes_a,
                "video_b": likes_b,
            },
            {
                "metric": "Comments",
                "video_a": comments_a,
                "video_b": comments_b,
            },
            {
                "metric": "Engagement Rate %",
                "video_a": engagement_a,
                "video_b": engagement_b,
            },
        ],
        winner=winner,
    )


def analyze_hook(first_five_seconds: str, *, title: str = "") -> HookResult:
    text = first_five_seconds.lower()
    words = {token.strip(".,!?;:") for token in text.split()}
    hook_score = min(100, len(words.intersection(HOOK_WORDS)) * 15 + len(words) // 2)
    curiosity_score = min(
        100,
        len(words.intersection({"why", "what", "how", "secret", "inside"})) * 20
        + (20 if "?" in first_five_seconds else 0),
    )
    emotion_score = min(100, len(words.intersection(EMOTION_WORDS)) * 20)
    retention_score = min(100, 50 + len(words) * 2 + (10 if len(words) > 12 else 0))
    cta_score = min(100, len(words.intersection(CTA_WORDS)) * 20)
    reasoning = (
        f"Hook evaluated from the first five seconds of {title or 'the video'} using keyword density, curiosity triggers, \
"
        f"emotional phrasing, retention pacing, and CTA presence. Text sample: {first_five_seconds[:180]}"
    )
    return HookResult(
        hook_score=hook_score,
        curiosity_score=curiosity_score,
        emotion_score=emotion_score,
        retention_score=retention_score,
        cta_score=cta_score,
        reasoning=reasoning,
    )


def model_dump_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)
