from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, JSON, Index
from sqlalchemy.sql import func
from app.database.base import Base


class ReviewApproval(Base):
    """
    Stores approval status for reviews.
    Maps review ID to approval status for persistence.
    """
    __tablename__ = "review_approvals"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, unique=True, nullable=False, index=True)
    listing_id = Column(String, nullable=True, index=True)
    is_approved = Column(Boolean, default=False, nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_review_approval_listing', 'listing_id', 'is_approved'),
        Index('idx_review_approval_status', 'is_approved'),
    )
    
    def __repr__(self):
        return f"<ReviewApproval(review_id={self.review_id}, is_approved={self.is_approved})>"

