from fastapi import APIRouter, HTTPException, Request, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel, Field
from app.models import NormalizedReview
from app.services.review_repository import ReviewRepository
from app.services.review_approval import ReviewApprovalService
from app.database.base import get_db
from app.core.logging_config import get_logger


router = APIRouter(prefix="/reviews", tags=["reviews"])
logger = get_logger(__name__)


class ApprovalRequest(BaseModel):
    """
    Request model for single review approval toggle.
    
    Attributes:
        review_id: Unique identifier of the review to approve/reject
        is_approved: Approval status (true = approved, false = rejected/hidden)
    """
    review_id: int = Field(..., description="Unique review identifier", example=7453)
    is_approved: bool = Field(..., description="Approval status (true to approve, false to reject)", example=True)


class BulkApprovalRequest(BaseModel):
    """
    Request model for bulk review approval toggle.
    
    Attributes:
        review_ids: List of unique review identifiers to approve/reject
        is_approved: Approval status to apply to all specified reviews
    """
    review_ids: List[int] = Field(..., description="List of review IDs to update", example=[7453, 7454, 8101])
    is_approved: bool = Field(..., description="Approval status to apply to all reviews", example=True)


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
    description="""
    Approve or reject a single review for public display.
    
    This endpoint allows managers to control which reviews are visible on the public-facing review display page.
    Only approved reviews will be returned by the `/api/reviews/approved` endpoint.
    
    **Use Cases:**
    - Approve a review for public display
    - Reject/hide a review from public view
    - Toggle approval status for individual reviews
    
    **Example Request:**
    ```json
    {
        "review_id": 7453,
        "is_approved": true
    }
    ```
    
    **Example Response:**
    ```json
    {
        "success": true,
        "review_id": 7453,
        "is_approved": true,
        "message": "Review 7453 approved"
    }
    ```
    """,
    response_description="Approval status update confirmation",
    status_code=200,
    tags=["reviews", "approval"]
)
async def toggle_review_approval(
    request: Request,
    approval_request: ApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Toggle approval status for a single review.
    
    **Parameters:**
    - **review_id** (int): The unique identifier of the review to approve/reject
    - **is_approved** (bool): `true` to approve the review, `false` to reject/hide it
    
    **Returns:**
    - **success** (bool): Whether the operation was successful
    - **review_id** (int): The ID of the updated review
    - **is_approved** (bool): The new approval status
    - **message** (str): Human-readable confirmation message
    
    **Errors:**
    - `404 Not Found`: Review with the specified ID does not exist
    - `500 Internal Server Error`: Database or server error occurred
    
    **Notes:**
    - The review must exist in the database before approval status can be set
    - Setting `is_approved` to `true` sets the `approved_at` timestamp
    - Setting `is_approved` to `false` clears the `approved_at` timestamp
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
    description="""
    Approve or reject multiple reviews at once.
    
    This endpoint allows managers to efficiently update approval status for multiple reviews in a single operation.
    Useful for bulk operations like approving all reviews from a specific listing or channel.
    
    **Use Cases:**
    - Approve multiple reviews at once
    - Reject/hide multiple reviews simultaneously
    - Bulk update approval status for filtered review sets
    
    **Example Request:**
    ```json
    {
        "review_ids": [7453, 7454, 8101],
        "is_approved": true
    }
    ```
    
    **Example Response:**
    ```json
    {
        "success": true,
        "updated_count": 3,
        "is_approved": true,
        "message": "3 reviews approved"
    }
    ```
    
    **Performance:**
    - Processes all reviews in a single database transaction
    - More efficient than calling `/approve` multiple times
    - Returns count of successfully updated reviews
    """,
    response_description="Bulk approval status update confirmation",
    status_code=200,
    tags=["reviews", "approval", "bulk"]
)
async def bulk_toggle_review_approval(
    request: Request,
    bulk_request: BulkApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk toggle approval status for multiple reviews.
    
    **Parameters:**
    - **review_ids** (List[int]): Array of unique review identifiers to update
    - **is_approved** (bool): Approval status to apply to all specified reviews (`true` = approve, `false` = reject)
    
    **Returns:**
    - **success** (bool): Whether the operation was successful
    - **updated_count** (int): Number of reviews successfully updated
    - **is_approved** (bool): The approval status that was applied
    - **message** (str): Human-readable confirmation message with count
    
    **Errors:**
    - `400 Bad Request`: Empty review_ids array provided
    - `500 Internal Server Error`: Database or server error occurred
    
    **Notes:**
    - All reviews are updated in a single database transaction
    - Non-existent review IDs are silently skipped (not counted in updated_count)
    - The operation is atomic - either all updates succeed or none do
    - More efficient than multiple individual `/approve` calls
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
    description="""
    Get approved reviews for public display.
    
    Returns only reviews that have been approved by managers (`isApproved: true`).
    This endpoint is designed for public-facing review display pages.
    
    **Use Cases:**
    - Public review display page
    - Listing-specific review pages
    - Customer-facing review showcase
    
    **Query Parameters:**
    - **listing_id** (optional): Filter reviews by specific listing ID (e.g., "FLX-307")
    
    **Example Requests:**
    - Get all approved reviews: `GET /api/reviews/approved`
    - Get approved reviews for a listing: `GET /api/reviews/approved?listing_id=FLX-307`
    
    **Example Response:**
    ```json
    [
        {
            "id": 7453,
            "listingId": "FLX-307",
            "listingName": "Shoreditch Heights Duplex",
            "listingLocation": "London, UK",
            "channel": "airbnb",
            "type": "host-to-guest",
            "status": "published",
            "rating": 10.0,
            "overallRating": 10.0,
            "categoryRatings": {
                "cleanliness": 10,
                "communication": 10
            },
            "publicReview": "Shane and family are wonderful!",
            "privateNote": null,
            "guestName": "Shane Finkelstein",
            "submittedAt": "2024-08-21T22:45:14Z",
            "date": "2024-08-21T22:45:14+00:00",
            "stayDate": "2024-08-15",
            "stayLength": 5,
            "isApproved": true
        }
    ]
    ```
    
    **Security Note:**
    - Private notes are included but should be filtered out on the frontend for public display
    - Only approved reviews are returned
    """,
    response_description="List of approved reviews for public display",
    status_code=200,
    tags=["reviews", "public"]
)
async def get_approved_reviews(
    request: Request,
    listing_id: str = None,
    db: AsyncSession = Depends(get_db)
) -> List[NormalizedReview]:
    """
    Get approved reviews for public display.
    
    **Query Parameters:**
    - **listing_id** (str, optional): Filter reviews by listing identifier (e.g., "FLX-307", "FLX-509")
    
    **Returns:**
    - Array of `NormalizedReview` objects containing only approved reviews
    - Reviews are ordered by submission date (newest first)
    - If `listing_id` is provided, only approved reviews for that listing are returned
    
    **Errors:**
    - `500 Internal Server Error`: Database connection or query error
    
    **Notes:**
    - Only reviews with `isApproved: true` are returned
    - Use this endpoint for public-facing pages
    - Private notes may be included - filter them out on the frontend for public display
    - Empty array is returned if no approved reviews exist (or match the listing filter)
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

