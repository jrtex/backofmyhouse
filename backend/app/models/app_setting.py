import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Uuid, Text

from app.database import Base


class AppSetting(Base):
    __tablename__ = "app_settings"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    is_encrypted = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
