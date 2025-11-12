from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, JSON, Index, Text
from sqlalchemy.sql import func
from app.database.base import Base


class Review(Base):
    """
    Stores review data in the database.
    Matches the NormalizedReview structure from models.py
    """
    __tablename__ = "reviews"
    
    # Primary identifier
    id = Column(Integer, primary_key=True, index=True, unique=True)
    
    # Listing information
    listing_id = Column(String, nullable=True, index=True)
    listing_name = Column(String, nullable=False, index=True)
    listing_location = Column(String, nullable=True)
    
    # Review metadata
    channel = Column(String, nullable=False, default="hostaway", index=True)
    type = Column(String, nullable=False, index=True)  # host-to-guest, guest-to-host
    status = Column(String, nullable=False, index=True)  # published, draft, etc.
    
    # Ratings
    rating = Column(Float, nullable=True)
    overall_rating = Column(Float, nullable=True)
    category_ratings = Column(JSON, nullable=False, default=dict)  # Store as JSON: {"cleanliness": 10, ...}
    
    # Review content
    public_review = Column(Text, nullable=True)
    private_note = Column(Text, nullable=True)
    guest_name = Column(String, nullable=True)
    
    # Dates
    submitted_at = Column(DateTime(timezone=True), nullable=False, index=True)
    stay_date = Column(String, nullable=True)  # YYYY-MM-DD format
    stay_length = Column(Integer, nullable=True)
    
    # Approval status (merged from ReviewApproval for simplicity)
    is_approved = Column(Boolean, default=False, nullable=False, index=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_review_listing_approved', 'listing_id', 'is_approved'),
        Index('idx_review_channel_status', 'channel', 'status'),
        Index('idx_review_submitted_at', 'submitted_at'),
        Index('idx_review_approved', 'is_approved'),
    )
    
    def __repr__(self):
        return f"<Review(id={self.id}, listing_name={self.listing_name}, is_approved={self.is_approved})>"

