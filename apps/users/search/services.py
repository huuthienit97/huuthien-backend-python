from typing import List, Dict, Any
from elasticsearch_dsl import Q
from apps.core.search.base import BaseSearchService
from .documents import UserDocument
from .config import UserSearchConfig

class UserSearchService(BaseSearchService):
    def __init__(self):
        self.document = UserDocument
        self.config = UserSearchConfig
    
    def search(self, 
               query: str,
               page: int = 1,
               page_size: int = 10) -> Dict:
        """
        Tìm kiếm user với fuzzy matching và exact matching
        """
        try:
            s = self.document.search()
            
            if query:
                # Tạo multi-match query với fuzzy
                multi_match = Q('multi_match',
                            query=query,
                            fields=self.config.SEARCH_FIELDS,
                            fuzziness='AUTO')
                
                # Tạo exact match queries
                exact_matches = [
                    Q('term', **{f'{field}.raw': query})
                    for field in ['username', 'email']
                ]
                
                # Kết hợp các queries
                s = s.query('bool',
                        should=[multi_match] + exact_matches,
                        minimum_should_match=1)
            
            # Filter chỉ lấy active users
            s = s.filter('term', is_active=True)
            
            # Pagination
            start = (page - 1) * page_size
            s = s[start:start + page_size]
            
            response = s.execute()
            
            # Lấy tổng số kết quả một cách an toàn
            total_hits = getattr(response.hits, 'total', {})
            if isinstance(total_hits, dict):
                total = total_hits.get('value', 0)
            else:
                total = total_hits or 0
            
            return {
                'total': total,
                'results': [self._format_hit(hit) for hit in response],
                'page': page,
                'page_size': page_size
            }
        except Exception as e:
            return {
                'error': str(e),
                'total': 0,
                'results': [],
                'page': page,
                'page_size': page_size
            }
    
    def suggest(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Gợi ý tìm kiếm với completion suggester
        """
        try:
            if not query or len(query) < 2:
                return []
                
            s = self.document.search()
            s = s.suggest(
                'suggestions',
                query,
                completion={
                    'field': 'suggest',
                    'fuzzy': {
                        'fuzziness': 2,
                        'prefix_length': 1
                    },
                    'size': limit,
                    'skip_duplicates': True
                }
            )
            
            response = s.execute()
            
            return self._format_suggestions(response)
        except Exception as e:
            return []
    
    def _format_hit(self, hit) -> Dict:
        """Format kết quả search"""
        return {
            'id': hit.id,
            'username': hit.username,
            'email': hit.email,
            'full_name': hit.full_name,
            'date_joined': hit.date_joined,
            'score': hit.meta.score
        }
    
    def _format_suggestions(self, response) -> List[Dict]:
        """Format kết quả suggest"""
        suggestions = []
        if hasattr(response, 'suggest'):
            for option in response.suggest.suggestions[0].options:
                suggestions.append({
                    'text': option.text,
                    'score': option._score,
                    'type': self._get_suggestion_type(option.text)
                })
        return suggestions
    
    def _get_suggestion_type(self, text: str) -> str:
        """Xác định loại suggestion"""
        if '@' in text:
            return 'email'
        return 'username'