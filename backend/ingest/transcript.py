from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from openai import OpenAI
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)
from yt_dlp import YoutubeDL

from backend.utils.settings import get_settings


def extract_youtube_video_id(url: str) -> str:
    from urllib.parse import parse_qs, urlparse

    parsed = urlparse(url)
    if parsed.netloc.endswith("youtu.be"):
        return parsed.path.strip("/")
    if parsed.path.startswith("/watch"):
        query = parse_qs(parsed.query)
        return query.get("v", [""])[0]
    if "/shorts/" in parsed.path:
        return parsed.path.split("/shorts/")[-1].split("/")[0]
    return parsed.path.rstrip("/").split("/")[-1]


def extract_transcript(url: str, platform: str) -> dict[str, Any]:
    if platform == "youtube":
        return _extract_youtube_transcript(url)
    return _extract_yt_dlp_whisper_transcript(url, platform)


def _extract_youtube_transcript(url: str) -> dict[str, Any]:
    video_id = extract_youtube_video_id(url)
    try:
        items = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        text = " ".join(item["text"] for item in items)
        return {
            "text": text,
            "source_type": "youtube-transcript-api",
            "language": "en",
            "is_fallback": False,
        }
    except (NoTranscriptFound, TranscriptsDisabled, Exception):
        return _extract_yt_dlp_whisper_transcript(url, "youtube")


def _extract_yt_dlp_whisper_transcript(url: str, platform: str) -> dict[str, Any]:
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    with tempfile.TemporaryDirectory() as temp_dir:
        output_template = str(Path(temp_dir) / "audio.%(ext)s")
        ffmpeg_location = _resolve_ffmpeg_location()
        use_postprocessing = _has_full_ffmpeg_toolchain(ffmpeg_location)
        options = {
            "quiet": True,
            "no_warnings": True,
            "format": "bestaudio/best",
            "outtmpl": output_template,
        }
        if use_postprocessing and ffmpeg_location:
            options["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]
            options["ffmpeg_location"] = ffmpeg_location
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_path = ydl.prepare_filename(info)
        audio_path = Path(downloaded_path)
        if not audio_path.exists():
            raise RuntimeError(f"Audio download failed for {platform} video")
        with audio_path.open("rb") as audio_file:
            try:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file
                )
                return {
                    "text": transcript.text,
                    "source_type": "yt-dlp+whisper",
                    "language": "en",
                    "is_fallback": True,
                }
            except Exception:
                # If OpenAI Whisper fails (e.g., auth 401), fall back to metadata
                # text such as the description or title so downstream chunking
                # and embeddings can continue.
                try:
                    # attempt to re-query info without downloading to get description
                    with YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True}) as _ydl:
                        info_meta = _ydl.extract_info(url, download=False)
                except Exception:
                    info_meta = info if "info" in locals() else {}

                fallback_text = (
                    (info_meta.get("description") or info_meta.get("title") or "")
                    if isinstance(info_meta, dict)
                    else ""
                )
                return {
                    "text": fallback_text,
                    "source_type": "yt-dlp+fallback-description",
                    "language": "en",
                    "is_fallback": True,
                }


def _resolve_ffmpeg_location() -> str | None:
    env_location = os.environ.get("FFMPEG_LOCATION")
    if env_location:
        candidate = Path(env_location)
        if candidate.exists():
            return str(candidate)

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return str(Path(ffmpeg_path).parent)

    try:
        import imageio_ffmpeg

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_exe:
            candidate = Path(ffmpeg_exe)
            if candidate.exists():
                return str(candidate.parent)
    except Exception:
        return None

    return None


def _has_full_ffmpeg_toolchain(ffmpeg_location: str | None) -> bool:
    if not ffmpeg_location:
        return False

    location = Path(ffmpeg_location)
    ffmpeg_candidates = [location / "ffmpeg", location / "ffmpeg.exe"]
    ffprobe_candidates = [location / "ffprobe", location / "ffprobe.exe"]

    return any(candidate.exists() for candidate in ffmpeg_candidates) and any(
        candidate.exists() for candidate in ffprobe_candidates
    )
