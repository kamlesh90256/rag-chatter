from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlmodel import Field, SQLModel


class Video(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    platform: str
    url: str = Field(index=True)
    title: str
    creator: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    upload_date: datetime | None = None
    duration_seconds: int | None = None
    hashtags_json: str = "[]"
    follower_count: int | None = None
    metadata_json: str = "{}"
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    error_message: str | None = None

    @property
    def hashtags(self) -> list[str]:
        import json

        return json.loads(self.hashtags_json)

    def set_hashtags(self, hashtags: list[str]) -> None:
        import json

        self.hashtags_json = json.dumps(hashtags)

    def set_metadata(self, payload: dict[str, Any]) -> None:
        import json

        self.metadata_json = json.dumps(payload)
