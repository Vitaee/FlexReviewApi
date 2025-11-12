import json
from pathlib import Path
from typing import List
from app.models import HostawayReviewRaw, HostawayApiResponse
from app.core.config import settings


class HostawayService:
    """Service responsible for loading and managing Hostaway review data"""
    
    def __init__(self, data_path: str | None = None):
        """
        Initialize Hostaway service.
        
        Args:
            data_path: Optional path to mock data file. Defaults to settings value.
        """
        self.data_path = Path(data_path or settings.mock_data_path)
    
    def load_mock_data(self) -> List[HostawayReviewRaw]:
        """
        Load mock review data from JSON file.
        
        Returns:
            List of raw Hostaway review objects
            
        Raises:
            FileNotFoundError: If mock data file doesn't exist
            ValueError: If data cannot be parsed or validated
        """
        if not self.data_path.exists():
            raise FileNotFoundError(
                f"Mock data file not found: {self.data_path}. "
                "Please ensure the file exists in the data directory."
            )
        
        try:
            with open(self.data_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            
            # Validate and parse API response structure
            api_response = HostawayApiResponse(**data)
            
            if api_response.status != "success":
                raise ValueError(f"API response status is not 'success': {api_response.status}")
            
            return api_response.result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in mock data file: {e}") from e
        except Exception as e:
            raise ValueError(f"Error loading mock data: {e}") from e
    
    def get_reviews(self) -> List[HostawayReviewRaw]:
        """
        Get all reviews from Hostaway (currently using mock data).
        
        Returns:
            List of raw Hostaway review objects
        """
        return self.load_mock_data()

