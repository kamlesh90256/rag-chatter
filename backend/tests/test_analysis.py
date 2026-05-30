from backend.ingest.analysis import (
    analyze_hook,
    build_comparison_table,
    calculate_engagement_rate,
)


def test_engagement_rate_formula() -> None:
    assert calculate_engagement_rate(100, 50, 1000) == 15.0


def test_comparison_table_winner() -> None:
    result = build_comparison_table(
        {"title": "Video A", "likes": 100, "comments": 20, "views": 1000},
        {"title": "Video B", "likes": 50, "comments": 10, "views": 1000},
    )
    assert result.winner == "Video A"
    assert any(row["metric"] == "Engagement Rate %" for row in result.comparison_table)


def test_hook_analysis_scores_are_bounded() -> None:
    result = analyze_hook(
        "Wait, discover the secret that changes everything. Follow for more.",
        title="Demo",
    )
    for score in [
        result.hook_score,
        result.curiosity_score,
        result.emotion_score,
        result.retention_score,
        result.cta_score,
    ]:
        assert 0 <= score <= 100
    assert "Demo" in result.reasoning
