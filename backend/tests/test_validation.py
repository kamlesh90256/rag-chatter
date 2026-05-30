import pytest
from fastapi import HTTPException

from backend.ingest.validator import validate_video_url


def test_validate_youtube_url() -> None:
    assert (
        validate_video_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "youtube"
    )


def test_validate_instagram_reel_url() -> None:
    assert validate_video_url("https://www.instagram.com/reel/abc123/") == "instagram"


def test_validate_unsupported_url() -> None:
    with pytest.raises(HTTPException):
        validate_video_url("https://example.com/video")
