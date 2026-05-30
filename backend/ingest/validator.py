from urllib.parse import urlparse

from fastapi import HTTPException, status

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
INSTAGRAM_HOSTS = {"instagram.com", "www.instagram.com", "m.instagram.com"}


def validate_video_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL"
        )
    host = parsed.netloc.lower()
    if host in YOUTUBE_HOSTS:
        return "youtube"
    if host in INSTAGRAM_HOSTS:
        if "/reel/" in parsed.path or "/reels/" in parsed.path or "/p/" in parsed.path:
            return "instagram"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instagram URL must point to a reel",
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported video platform"
    )
