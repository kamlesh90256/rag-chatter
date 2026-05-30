from datetime import datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class ChatHistory(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    thread_id: str = Field(index=True)
    role: str
    content: str
    sources_json: str = "[]"
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
