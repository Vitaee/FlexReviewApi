from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from typing import Optional, Dict, List
from app.database.models import ReviewApproval
from app.core.logging_config import get_logger


logger = get_logger(__name__)


class ReviewApprovalService:
    """Service for managing review approval status"""
    
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
            Approval status (True/False) or None if not set
        """
        result = await db.execute(
            select(ReviewApproval).where(ReviewApproval.review_id == review_id)
        )
        approval = result.scalar_one_or_none()
        return approval.is_approved if approval else None
    
    @staticmethod
    async def get_bulk_approval_status(
        db: AsyncSession,
        review_ids: List[int]
    ) -> Dict[int, bool]:
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
        
        result = await db.execute(
            select(ReviewApproval).where(ReviewApproval.review_id.in_(review_ids))
        )
        approvals = result.scalars().all()
        
        return {approval.review_id: approval.is_approved for approval in approvals}
    
    @staticmethod
    async def set_approval_status(
        db: AsyncSession,
        review_id: int,
        is_approved: bool,
        listing_id: Optional[str] = None
    ) -> ReviewApproval:
        """
        Set approval status for a review.
        
        Args:
            db: Database session
            review_id: Review ID
            is_approved: Approval status
            listing_id: Optional listing ID for indexing
            
        Returns:
            ReviewApproval object
        """
        # Try to update existing record
        result = await db.execute(
            select(ReviewApproval).where(ReviewApproval.review_id == review_id)
        )
        approval = result.scalar_one_or_none()
        
        if approval:
            approval.is_approved = is_approved
            approval.approved_at = datetime.utcnow() if is_approved else None
            if listing_id:
                approval.listing_id = listing_id
        else:
            # Create new record
            approval = ReviewApproval(
                review_id=review_id,
                listing_id=listing_id,
                is_approved=is_approved,
                approved_at=datetime.utcnow() if is_approved else None
            )
            db.add(approval)
        
        await db.commit()
        await db.refresh(approval)
        
        logger.info(f"Set approval status for review {review_id}: {is_approved}")
        return approval
    
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
            listing_id: Optional listing ID
            
        Returns:
            Number of reviews updated
        """
        approved_at = datetime.utcnow() if is_approved else None
        
        # Update existing records
        await db.execute(
            update(ReviewApproval)
            .where(ReviewApproval.review_id.in_(review_ids))
            .values(
                is_approved=is_approved,
                approved_at=approved_at,
                listing_id=listing_id
            )
        )
        
        # Get existing review IDs
        result = await db.execute(
            select(ReviewApproval.review_id).where(ReviewApproval.review_id.in_(review_ids))
        )
        existing_ids = set(result.scalars().all())
        
        # Create new records for reviews that don't exist
        new_approvals = [
            ReviewApproval(
                review_id=rid,
                listing_id=listing_id,
                is_approved=is_approved,
                approved_at=approved_at
            )
            for rid in review_ids
            if rid not in existing_ids
        ]
        
        if new_approvals:
            db.add_all(new_approvals)
        
        await db.commit()
        
        logger.info(f"Bulk set approval status for {len(review_ids)} reviews: {is_approved}")
        return len(review_ids)
    
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
        query = select(ReviewApproval.review_id).where(ReviewApproval.is_approved == True)
        
        if listing_id:
            query = query.where(ReviewApproval.listing_id == listing_id)
        
        result = await db.execute(query)
        return list(result.scalars().all())

