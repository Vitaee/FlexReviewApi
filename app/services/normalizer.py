from datetime import datetime
from typing import Dict, List
from app.models import HostawayReviewRaw, NormalizedReview, ReviewCategory


class ReviewNormalizer:
    """Service responsible for normalizing review data from various sources"""
    
    @staticmethod
    def normalize_hostaway_review(raw_review: HostawayReviewRaw) -> NormalizedReview:
        """
        Normalize a Hostaway review into the unified format matching frontend structure.
        
        Args:
            raw_review: Raw Hostaway review data
            
        Returns:
            Normalized review object matching frontend HostawayReview type
        """
        # Convert reviewCategory list to dictionary
        category_ratings = ReviewNormalizer._extract_category_ratings(
            raw_review.reviewCategory
        )
        
        # Calculate overall rating if not provided
        overall_rating = ReviewNormalizer._calculate_overall_rating(
            raw_review.rating,
            category_ratings
        )
        
        # Normalize submittedAt to ISO 8601 format
        submitted_at_iso = ReviewNormalizer._normalize_datetime_to_iso(raw_review.submittedAt)
        
        # Determine channel (use provided or default to "hostaway")
        channel = raw_review.channel or "hostaway"
        
        return NormalizedReview(
            id=raw_review.id,
            listingId=raw_review.listingId,
            listingName=raw_review.listingName,
            listingLocation=raw_review.listingLocation,
            channel=channel,
            type=raw_review.type,
            status=raw_review.status,
            rating=overall_rating,
            overallRating=overall_rating,
            categoryRatings=category_ratings,
            publicReview=raw_review.publicReview,
            privateNote=raw_review.privateNote,
            guestName=raw_review.guestName,
            submittedAt=submitted_at_iso,
            stayDate=raw_review.stayDate,
            stayLength=raw_review.stayLength,
            isApproved=False  # Default to False, managed by frontend/dashboard
        )
    
    @staticmethod
    def _extract_category_ratings(categories: List[ReviewCategory]) -> Dict[str, int]:
        """
        Extract category ratings into a dictionary.
        
        Args:
            categories: List of ReviewCategory objects
            
        Returns:
            Dictionary mapping category names to ratings
        """
        return {
            category.category: category.rating
            for category in categories
        }
    
    @staticmethod
    def _calculate_overall_rating(
        provided_rating: int | None,
        category_ratings: Dict[str, int]
    ) -> float | None:
        """
        Calculate overall rating from provided rating or category averages.
        
        Args:
            provided_rating: Direct rating if available
            category_ratings: Dictionary of category ratings
            
        Returns:
            Overall rating as float, or None if cannot be determined
        """
        if provided_rating is not None:
            return float(provided_rating)
        
        if not category_ratings:
            return None
        
        # Calculate average from category ratings
        ratings = list(category_ratings.values())
        if ratings:
            return round(sum(ratings) / len(ratings), 2)
        
        return None
    
    @staticmethod
    def _parse_datetime(date_string: str) -> datetime:
        """
        Parse datetime string from Hostaway format.
        
        Args:
            date_string: Datetime string in format "YYYY-MM-DD HH:MM:SS" or ISO 8601
            
        Returns:
            Parsed datetime object
            
        Raises:
            ValueError: If date string cannot be parsed
        """
        try:
            # Try ISO format first
            if 'T' in date_string or date_string.endswith('Z'):
                return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            # Fall back to Hostaway format: "2020-08-21 22:45:14"
            return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            raise ValueError(f"Invalid date format: {date_string}") from e
    
    @staticmethod
    def _normalize_datetime_to_iso(date_string: str) -> str:
        """
        Normalize datetime string to ISO 8601 format.
        
        Args:
            date_string: Datetime string in various formats
            
        Returns:
            ISO 8601 formatted string (e.g., "2024-08-21T22:45:14Z")
        """
        try:
            # If already ISO format, return as-is (with Z if missing)
            if 'T' in date_string:
                if date_string.endswith('Z'):
                    return date_string
                return date_string + 'Z'
            
            # Parse Hostaway format and convert to ISO
            dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            # If parsing fails, try to return as-is
            return date_string

