import re
from datetime import datetime
from typing import Any

from yt_dlp import YoutubeDL

HASHTAG_PATTERN = re.compile(r"#(\w+)")


def extract_metadata(url: str, platform: str) -> dict[str, Any]:
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        "noplaylist": True,
    }
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
    hashtags = _extract_hashtags(info)
    return {
        "platform": platform,
        "url": url,
        "title": info.get("title") or "Untitled video",
        "creator": info.get("uploader")
        or info.get("channel")
        or info.get("creator")
        or "Unknown creator",
        "views": int(info.get("view_count") or 0),
        "likes": int(info.get("like_count") or 0),
        "comments": int(info.get("comment_count") or 0),
        "upload_date": _parse_upload_date(info.get("upload_date")),
        "duration_seconds": int(info.get("duration") or 0) or None,
        "hashtags": hashtags,
        "follower_count": int(
            info.get("channel_follower_count") or info.get("follower_count") or 0
        )
        or None,
        "raw": info,
    }


def _parse_upload_date(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y%m%d")


def _extract_hashtags(info: dict[str, Any]) -> list[str]:
    tokens: set[str] = set()
    for field in (info.get("title"), info.get("description")):
        if isinstance(field, str):
            tokens.update(
                match.group(1).lower() for match in HASHTAG_PATTERN.finditer(field)
            )
    categories = info.get("tags") or []
    if isinstance(categories, list):
        tokens.update(str(item).lower() for item in categories)
    return sorted(tokens)
