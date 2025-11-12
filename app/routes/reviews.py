from fastapi import APIRouter, HTTPException, Request, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
from app.models import NormalizedReview
from app.services.review_repository import ReviewRepository
from app.services.review_approval import ReviewApprovalService
from app.database.base import get_db
from app.core.logging_config import get_logger


router = APIRouter(prefix="/reviews", tags=["reviews"])
logger = get_logger(__name__)


class ApprovalRequest(BaseModel):
    """Request model for approval toggle"""
    review_id: int
    is_approved: bool


class BulkApprovalRequest(BaseModel):
    """Request model for bulk approval"""
    review_ids: List[int]
    is_approved: bool


@router.get(
    "/hostaway",
    response_model=List[NormalizedReview],
    summary="Get Hostaway reviews",
    description="Fetch all Hostaway reviews from database with approval status"
)
async def get_hostaway_reviews(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> List[NormalizedReview]:
    """
    Retrieve all Hostaway reviews from database.
    
    Returns:
        List of normalized review objects with approval status
        
    Raises:
        HTTPException: If data cannot be loaded or processed
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        logger.info(f"[{request_id}] Fetching Hostaway reviews from database")
        
        # Load reviews from database
        reviews = await ReviewRepository.get_all(db)
        logger.debug(f"[{request_id}] Loaded {len(reviews)} reviews from database")
        
        # Convert to NormalizedReview format
        normalized_reviews = [
            ReviewRepository.to_normalized_review(review)
            for review in reviews
        ]
        
        logger.info(f"[{request_id}] Successfully retrieved {len(normalized_reviews)} reviews")
        return normalized_reviews
        
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) from e


@router.patch(
    "/approve",
    summary="Toggle review approval",
    description="Approve or reject a single review for public display"
)
async def toggle_review_approval(
    request: Request,
    approval_request: ApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Toggle approval status for a review.
    
    Args:
        approval_request: Review ID and approval status
        db: Database session
        
    Returns:
        Success message with approval status
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        approval = await ReviewApprovalService.set_approval_status(
            db=db,
            review_id=approval_request.review_id,
            is_approved=approval_request.is_approved
        )
        
        logger.info(
            f"[{request_id}] Review {approval_request.review_id} "
            f"approval set to {approval_request.is_approved}"
        )
        
        return {
            "success": True,
            "review_id": approval.id,
            "is_approved": approval.is_approved,
            "message": f"Review {approval_request.review_id} {'approved' if approval_request.is_approved else 'rejected'}"
        }
        
    except Exception as e:
        logger.error(f"[{request_id}] Error updating approval: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating approval status: {str(e)}"
        ) from e


@router.patch(
    "/approve/bulk",
    summary="Bulk toggle review approvals",
    description="Approve or reject multiple reviews at once"
)
async def bulk_toggle_review_approval(
    request: Request,
    bulk_request: BulkApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk toggle approval status for multiple reviews.
    
    Args:
        bulk_request: List of review IDs and approval status
        db: Database session
        
    Returns:
        Success message with count of updated reviews
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        count = await ReviewApprovalService.bulk_set_approval_status(
            db=db,
            review_ids=bulk_request.review_ids,
            is_approved=bulk_request.is_approved
        )
        
        logger.info(
            f"[{request_id}] Bulk approval: {count} reviews set to {bulk_request.is_approved}"
        )
        
        return {
            "success": True,
            "updated_count": count,
            "is_approved": bulk_request.is_approved,
            "message": f"{count} reviews {'approved' if bulk_request.is_approved else 'rejected'}"
        }
        
    except Exception as e:
        logger.error(f"[{request_id}] Error bulk updating approvals: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error bulk updating approval status: {str(e)}"
        ) from e


@router.get(
    "/approved",
    response_model=List[NormalizedReview],
    summary="Get approved reviews",
    description="Get approved reviews for public display (with full review data)"
)
async def get_approved_reviews(
    request: Request,
    listing_id: str = None,
    db: AsyncSession = Depends(get_db)
) -> List[NormalizedReview]:
    """
    Get approved reviews for public display.
    
    Args:
        listing_id: Optional filter by listing ID
        db: Database session
        
    Returns:
        List of approved normalized review objects
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        approved_reviews = await ReviewRepository.get_approved(db, listing_id)
        
        normalized_reviews = [
            ReviewRepository.to_normalized_review(review)
            for review in approved_reviews
        ]
        
        logger.info(f"[{request_id}] Retrieved {len(normalized_reviews)} approved reviews")
        
        return normalized_reviews
        
    except Exception as e:
        logger.error(f"[{request_id}] Error getting approved reviews: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving approved reviews: {str(e)}"
        ) from e

