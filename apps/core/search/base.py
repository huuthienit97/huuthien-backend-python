from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseSearchConfig:
    """Config cơ bản cho search"""
    INDEX_NAME: Optional[str] = None
    SEARCH_FIELDS: List[str] = []
    SUGGEST_FIELDS: List[str] = []
    
    @classmethod
    def get_index_settings(cls) -> Dict:
        return {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'refresh_interval': '1s'
        }

class BaseSearchService(ABC):
    """Service cơ bản cho search operations"""
    
    @abstractmethod
    def search(self, query: str, **kwargs) -> Dict:
        """Tìm kiếm cơ bản"""
        pass
        
    @abstractmethod
    def suggest(self, query: str, **kwargs) -> List:
        """Gợi ý tìm kiếm"""
        pass 