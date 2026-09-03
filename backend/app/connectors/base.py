from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.schemas.product import TrueCostProduct

class BaseProviderConnector(ABC):
    """
    The Abstract Base Class that forces every provider (Zepto, Blinkit, etc.)
    to implement a standard parsing pipeline.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        """
        Takes raw JSON/HTML data from the Mobile Edge Scraper
        and returns cleanly mapped TrueCostProduct objects.
        """
        pass
