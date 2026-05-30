from datetime import datetime

from pydantic import BaseModel, field_validator


class IngestRequest(BaseModel):
    youtube_url: str
    instagram_url: str

    @field_validator("youtube_url", "instagram_url")
    @classmethod
    def strip_url(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("URL cannot be empty")
        return cleaned


class ChatRequest(BaseModel):
    question: str
    thread_id: str = "default"
    video_ids: list[str] | None = None
    stream: bool = True

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Question cannot be empty")
        return cleaned


class ChatResponse(BaseModel):
    answer: str
    citations: list[dict[str, str | int | None]]
    thread_id: str


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
