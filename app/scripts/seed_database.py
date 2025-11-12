"""Database seeding script - populates database with mock review data"""
import asyncio
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import AsyncSessionLocal
from app.services.hostaway import HostawayService
from app.services.normalizer import ReviewNormalizer
from app.services.review_repository import ReviewRepository
from app.core.logging_config import get_logger
from app.core.config import settings


logger = get_logger(__name__)


async def seed_database() -> None:
    """
    Seed the database with mock review data.
    Only seeds if database is empty.
    """
    async with AsyncSessionLocal() as db:
        try:
            # Check if reviews already exist
            existing_reviews = await ReviewRepository.get_all(db)
            if existing_reviews:
                logger.info(f"Database already contains {len(existing_reviews)} reviews. Skipping seed.")
                return
            
            logger.info("Starting database seed...")
            
            # Load mock data
            hostaway_service = HostawayService()
            normalizer = ReviewNormalizer()
            
            raw_reviews = hostaway_service.get_reviews()
            logger.info(f"Loaded {len(raw_reviews)} raw reviews from mock data")
            
            # Normalize reviews
            normalized_reviews = [
                normalizer.normalize_hostaway_review(review)
                for review in raw_reviews
            ]
            
            # Save to database
            count = await ReviewRepository.bulk_create_or_update(db, normalized_reviews)
            
            logger.info(f"Successfully seeded {count} reviews into database")
            
        except Exception as e:
            logger.error(f"Error seeding database: {e}", exc_info=True)
            raise


async def main():
    """Main entry point for seeding"""
    await seed_database()


if __name__ == "__main__":
    asyncio.run(main())

