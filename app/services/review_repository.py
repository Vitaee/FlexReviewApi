"""Review repository service - handles database operations for reviews"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Dict
from datetime import datetime, timezone
from app.database.models import Review
from app.models import NormalizedReview
from app.core.logging_config import get_logger


logger = get_logger(__name__)


class ReviewRepository:
    """Repository for review database operations"""
    
    @staticmethod
    async def get_all(db: AsyncSession) -> List[Review]:
        """
        Get all reviews from database.
        
        Args:
            db: Database session
            
        Returns:
            List of Review objects
        """
        result = await db.execute(select(Review).order_by(Review.submitted_at.desc()))
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_id(db: AsyncSession, review_id: int) -> Optional[Review]:
        """
        Get review by ID.
        
        Args:
            db: Database session
            review_id: Review ID
            
        Returns:
            Review object or None
        """
        result = await db.execute(select(Review).where(Review.id == review_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_listing(db: AsyncSession, listing_id: str) -> List[Review]:
        """
        Get reviews by listing ID.
        
        Args:
            db: Database session
            listing_id: Listing identifier
            
        Returns:
            List of Review objects
        """
        result = await db.execute(
            select(Review)
            .where(Review.listing_id == listing_id)
            .order_by(Review.submitted_at.desc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_approved(db: AsyncSession, listing_id: Optional[str] = None) -> List[Review]:
        """
        Get approved reviews.
        
        Args:
            db: Database session
            listing_id: Optional filter by listing ID
            
        Returns:
            List of approved Review objects
        """
        query = select(Review).where(Review.is_approved == True)
        
        if listing_id:
            query = query.where(Review.listing_id == listing_id)
        
        query = query.order_by(Review.submitted_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def create_or_update(db: AsyncSession, normalized_review: NormalizedReview) -> Review:
        """
        Create or update review in database.
        
        Args:
            db: Database session
            normalized_review: NormalizedReview object
            
        Returns:
            Review database object
        """
        # Parse submittedAt to datetime
        submitted_at = ReviewRepository._parse_datetime(normalized_review.submittedAt)
        
        # Check if review exists
        existing = await ReviewRepository.get_by_id(db, normalized_review.id)
        
        if existing:
            # Update existing review
            existing.listing_id = normalized_review.listingId
            existing.listing_name = normalized_review.listingName
            existing.listing_location = normalized_review.listingLocation
            existing.channel = normalized_review.channel
            existing.type = normalized_review.type
            existing.status = normalized_review.status
            existing.rating = normalized_review.rating
            existing.overall_rating = normalized_review.overallRating
            existing.category_ratings = normalized_review.categoryRatings
            existing.public_review = normalized_review.publicReview
            existing.private_note = normalized_review.privateNote
            existing.guest_name = normalized_review.guestName
            existing.submitted_at = submitted_at
            existing.stay_date = normalized_review.stayDate
            existing.stay_length = normalized_review.stayLength
            # Don't update is_approved here - use approval service for that
            
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # Create new review
            review = Review(
                id=normalized_review.id,
                listing_id=normalized_review.listingId,
                listing_name=normalized_review.listingName,
                listing_location=normalized_review.listingLocation,
                channel=normalized_review.channel,
                type=normalized_review.type,
                status=normalized_review.status,
                rating=normalized_review.rating,
                overall_rating=normalized_review.overallRating,
                category_ratings=normalized_review.categoryRatings,
                public_review=normalized_review.publicReview,
                private_note=normalized_review.privateNote,
                guest_name=normalized_review.guestName,
                submitted_at=submitted_at,
                stay_date=normalized_review.stayDate,
                stay_length=normalized_review.stayLength,
                is_approved=normalized_review.isApproved
            )
            
            db.add(review)
            await db.commit()
            await db.refresh(review)
            return review
    
    @staticmethod
    async def bulk_create_or_update(
        db: AsyncSession,
        normalized_reviews: List[NormalizedReview]
    ) -> int:
        """
        Bulk create or update reviews.
        
        Args:
            db: Database session
            normalized_reviews: List of NormalizedReview objects
            
        Returns:
            Number of reviews processed
        """
        count = 0
        for normalized_review in normalized_reviews:
            try:
                await ReviewRepository.create_or_update(db, normalized_review)
                count += 1
            except Exception as e:
                logger.error(f"Error saving review {normalized_review.id}: {e}")
                await db.rollback()
        
        return count
    
    @staticmethod
    async def set_approval_status(
        db: AsyncSession,
        review_id: int,
        is_approved: bool
    ) -> Optional[Review]:
        """
        Set approval status for a review.
        
        Args:
            db: Database session
            review_id: Review ID
            is_approved: Approval status
            
        Returns:
            Updated Review object or None if not found
        """
        review = await ReviewRepository.get_by_id(db, review_id)
        if not review:
            return None
        
        review.is_approved = is_approved
        review.approved_at = datetime.utcnow() if is_approved else None
        
        await db.commit()
        await db.refresh(review)
        return review
    
    @staticmethod
    async def bulk_set_approval_status(
        db: AsyncSession,
        review_ids: List[int],
        is_approved: bool
    ) -> int:
        """
        Bulk set approval status.
        
        Args:
            db: Database session
            review_ids: List of review IDs
            is_approved: Approval status
            
        Returns:
            Number of reviews updated
        """
        approved_at = datetime.utcnow() if is_approved else None
        
        await db.execute(
            update(Review)
            .where(Review.id.in_(review_ids))
            .values(
                is_approved=is_approved,
                approved_at=approved_at
            )
        )
        
        await db.commit()
        
        # Get count of updated reviews
        result = await db.execute(
            select(Review.id).where(Review.id.in_(review_ids))
        )
        return len(list(result.scalars().all()))
    
    @staticmethod
    def to_normalized_review(review: Review) -> NormalizedReview:
        """
        Convert database Review to NormalizedReview Pydantic model.
        
        Args:
            review: Review database object
            
        Returns:
            NormalizedReview object
        """
        # Format submittedAt as ISO 8601 string (UTC with Z suffix)
        if review.submitted_at:
            # Convert to UTC if timezone-aware, otherwise assume UTC
            if review.submitted_at.tzinfo is not None:
                submitted_at_utc = review.submitted_at.astimezone(timezone.utc)
            else:
                submitted_at_utc = review.submitted_at.replace(tzinfo=timezone.utc)
            # Format as ISO 8601 with Z suffix (e.g., "2024-11-05T07:55:00Z")
            submitted_at_str = submitted_at_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            submitted_at_str = ""
        
        # Set date from submitted_at datetime
        date_value = review.submitted_at if review.submitted_at else None
        
        return NormalizedReview(
            id=review.id,
            listingId=review.listing_id,
            listingName=review.listing_name,
            listingLocation=review.listing_location,
            channel=review.channel,
            type=review.type,
            status=review.status,
            rating=review.rating,
            overallRating=review.overall_rating or review.rating,
            categoryRatings=review.category_ratings or {},
            publicReview=review.public_review,
            privateNote=review.private_note,
            guestName=review.guest_name,
            submittedAt=submitted_at_str,
            date=date_value,
            stayDate=review.stay_date,
            stayLength=review.stay_length,
            isApproved=review.is_approved
        )
    
    @staticmethod
    def _parse_datetime(date_string: str) -> datetime:
        """
        Parse datetime string to datetime object.
        
        Args:
            date_string: ISO 8601 or Hostaway format string
            
        Returns:
            Datetime object
        """
        try:
            # Try ISO format first
            if 'T' in date_string or date_string.endswith('Z'):
                return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            # Fall back to Hostaway format
            return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            raise ValueError(f"Invalid date format: {date_string}") from e

