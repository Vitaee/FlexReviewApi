"""Pydantic models for review data structures"""
from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, field_validator


class ReviewCategory(BaseModel):
    """Individual review category rating"""
    category: str
    rating: int = Field(..., ge=0, le=10)


class HostawayReviewRaw(BaseModel):
    """Raw Hostaway API review structure - supports both basic and extended formats"""
    id: int
    type: str
    status: str
    rating: Optional[float] = None
    publicReview: Optional[str] = None
    privateNote: Optional[str] = None
    reviewCategory: List[ReviewCategory] = Field(default_factory=list)
    submittedAt: str
    guestName: Optional[str] = None
    listingName: str
    listingId: Optional[str] = None
    listingLocation: Optional[str] = None
    channel: Optional[str] = None
    stayDate: Optional[str] = None
    stayLength: Optional[int] = None


class HostawayApiResponse(BaseModel):
    """Hostaway API response wrapper"""
    status: str
    result: List[HostawayReviewRaw]


class NormalizedReview(BaseModel):
    """Unified review model matching frontend structure"""
    id: int
    listingId: Optional[str] = Field(None, description="Listing identifier (e.g., 'FLX-307')")
    listingName: str
    listingLocation: Optional[str] = Field(None, description="Listing location (e.g., 'London, UK')")
    channel: str = Field(default="hostaway", description="Review source channel (airbnb, booking, direct, vrbo, hostaway)")
    type: str = Field(description="Review type (e.g., 'host-to-guest', 'guest-to-host')")
    status: str = Field(description="Review status (e.g., 'published')")
    rating: Optional[float] = Field(
        None, 
        description="Overall rating (0-10), calculated from categories if not provided"
    )
    overallRating: Optional[float] = Field(
        None, 
        description="Alias for rating - overall rating (0-10)"
    )
    categoryRatings: Dict[str, int] = Field(
        default_factory=dict,
        description="Dictionary of category ratings"
    )
    publicReview: Optional[str] = None
    privateNote: Optional[str] = Field(None, description="Private/internal notes about the review")
    guestName: Optional[str] = None
    submittedAt: str = Field(description="Review submission date in ISO 8601 format")
    date: Optional[datetime] = Field(None, description="Review submission date as datetime object")
    stayDate: Optional[str] = Field(None, description="Date of the stay (YYYY-MM-DD)")
    stayLength: Optional[int] = Field(None, description="Length of stay in days")
    isApproved: bool = Field(
        default=False,
        description="Whether review is approved for public display"
    )
    
    @field_validator('rating', 'overallRating')
    @classmethod
    def validate_rating(cls, v: Optional[float]) -> Optional[float]:
        """Validate rating is within valid range"""
        if v is not None and (v < 0 or v > 10):
            raise ValueError("Rating must be between 0 and 10")
        return v
    
    def model_post_init(self, __context) -> None:
        """Set overallRating as alias for rating and ensure date is set"""
        # Sync rating and overallRating
        if self.rating is not None and self.overallRating is None:
            object.__setattr__(self, 'overallRating', self.rating)
        elif self.overallRating is not None and self.rating is None:
            object.__setattr__(self, 'rating', self.overallRating)
        
        # Ensure date is set from submittedAt if not provided
        if self.date is None and self.submittedAt:
            try:
                # Handle ISO 8601 format with Z suffix (e.g., "2024-11-05T07:55:00Z")
                if self.submittedAt.endswith('Z'):
                    # Replace Z with +00:00 for fromisoformat
                    dt_str = self.submittedAt.replace('Z', '+00:00')
                    dt = datetime.fromisoformat(dt_str)
                elif 'T' in self.submittedAt:
                    # ISO format without Z
                    dt = datetime.fromisoformat(self.submittedAt)
                else:
                    # Fall back to Hostaway format
                    dt = datetime.strptime(self.submittedAt, "%Y-%m-%d %H:%M:%S")
                object.__setattr__(self, 'date', dt)
            except (ValueError, AttributeError) as e:
                # Log error but don't fail - date will remain None
                pass

