from datetime import datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class Transcript(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    video_id: str = Field(index=True, foreign_key="video.id")
    source_type: str
    language: str = "en"
    text: str
    is_fallback: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
