import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Table, ForeignKey, Uuid

from app.database import Base


recipe_tags = Table(
    "recipe_tags",
    Base.metadata,
    Column("recipe_id", Uuid, ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Uuid, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
