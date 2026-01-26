import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON, Uuid
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.tag import recipe_tags


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    title = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=True)
    ingredients = Column(JSON, nullable=False, default=list)
    instructions = Column(JSON, nullable=False, default=list)
    prep_time_minutes = Column(Integer, nullable=True)
    cook_time_minutes = Column(Integer, nullable=True)
    servings = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    category_id = Column(Uuid, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    category = relationship("Category", back_populates="recipes")
    user = relationship("User", back_populates="recipes")
    tags = relationship("Tag", secondary=recipe_tags, backref="recipes")
