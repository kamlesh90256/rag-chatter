from datetime import datetime
from sqlmodel import Field, SQLModel


class EmbeddingCache(SQLModel, table=True):
    key: str = Field(primary_key=True)
    vector_json: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
