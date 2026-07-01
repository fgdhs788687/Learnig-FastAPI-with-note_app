from sqlalchemy import Column, String
from .database import Base
import uuid

class Notes(Base):
    __tablename__ = "notes"

    # Automatically generate a unique uuid for each note:
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)