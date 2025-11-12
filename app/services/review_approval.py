"""Review approval service - handles approval status persistence"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.services.review_repository import ReviewRepository
from app.core.logging_config import get_logger


logger = get_logger(__name__)


class ReviewApprovalService:
    """Service for managing review approval status - uses Review table"""
    
    @staticmethod
    async def get_approval_status(
        db: AsyncSession,
        review_id: int
    ) -> Optional[bool]:
        """
        Get approval status for a review.
        
        Args:
            db: Database session
            review_id: Review ID
            
        Returns:
            Approval status (True/False) or None if not found
        """
        review = await ReviewRepository.get_by_id(db, review_id)
        return review.is_approved if review else None
    
    @staticmethod
    async def get_bulk_approval_status(
        db: AsyncSession,
        review_ids: List[int]
    ) -> dict[int, bool]:
        """
        Get approval status for multiple reviews.
        
        Args:
            db: Database session
            review_ids: List of review IDs
            
        Returns:
            Dictionary mapping review_id to approval status
        """
        if not review_ids:
            return {}
        
        reviews = await ReviewRepository.get_all(db)
        return {review.id: review.is_approved for review in reviews if review.id in review_ids}
    
    @staticmethod
    async def set_approval_status(
        db: AsyncSession,
        review_id: int,
        is_approved: bool,
        listing_id: Optional[str] = None
    ):
        """
        Set approval status for a review.
        
        Args:
            db: Database session
            review_id: Review ID
            is_approved: Approval status
            listing_id: Optional listing ID (for logging)
            
        Returns:
            Updated Review object
        """
        review = await ReviewRepository.set_approval_status(db, review_id, is_approved)
        
        if review:
            logger.info(f"Set approval status for review {review_id}: {is_approved}")
        else:
            logger.warning(f"Review {review_id} not found")
        
        return review
    
    @staticmethod
    async def bulk_set_approval_status(
        db: AsyncSession,
        review_ids: List[int],
        is_approved: bool,
        listing_id: Optional[str] = None
    ) -> int:
        """
        Set approval status for multiple reviews.
        
        Args:
            db: Database session
            review_ids: List of review IDs
            is_approved: Approval status
            listing_id: Optional listing ID (for logging)
            
        Returns:
            Number of reviews updated
        """
        count = await ReviewRepository.bulk_set_approval_status(db, review_ids, is_approved)
        logger.info(f"Bulk set approval status for {count} reviews: {is_approved}")
        return count
    
    @staticmethod
    async def get_approved_reviews(
        db: AsyncSession,
        listing_id: Optional[str] = None
    ) -> List[int]:
        """
        Get list of approved review IDs.
        
        Args:
            db: Database session
            listing_id: Optional filter by listing ID
            
        Returns:
            List of approved review IDs
        """
        approved_reviews = await ReviewRepository.get_approved(db, listing_id)
        return [review.id for review in approved_reviews]
