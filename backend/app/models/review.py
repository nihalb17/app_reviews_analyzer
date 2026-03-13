from sqlalchemy import Column, String, Integer, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(String(255), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    cleaned_content = Column(Text)
    rating = Column(Integer, nullable=False)
    review_date = Column(DateTime, nullable=False)
    app_version = Column(String(50))
    thumbs_up = Column(Integer, default=0)
    content_hash = Column(String(64), unique=True, nullable=False)  # For deduplication
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<Review(review_id={self.review_id}, rating={self.rating})>"


class Trigger(Base):
    __tablename__ = "triggers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mode = Column(String(20), nullable=False)  # 'manual' or 'scheduler'
    review_count = Column(Integer)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    role = Column(String(50))
    receiver_email = Column(String(255))
    receiver_name = Column(String(255))
    status = Column(String(50), default='data_ingestion')
    current_phase = Column(String(50))
    pdf_path = Column(String(500))
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
