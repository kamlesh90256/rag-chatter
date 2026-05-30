from datetime import datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class Analysis(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    video_a_id: str = Field(index=True, foreign_key="video.id")
    video_b_id: str = Field(index=True, foreign_key="video.id")
    engagement_json: str = "{}"
    hook_json: str = "{}"
    comparison_json: str = "{}"
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
