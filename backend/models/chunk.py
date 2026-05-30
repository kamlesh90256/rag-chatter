from datetime import datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class Chunk(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    video_id: str = Field(index=True, foreign_key="video.id")
    chunk_id: int = Field(index=True)
    text: str
    creator: str
    title: str
    url: str
    metadata_json: str = "{}"
    vector_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
