from apps.core.search.base import BaseSearchConfig

class UserSearchConfig(BaseSearchConfig):
    INDEX_NAME = 'users'
    SEARCH_FIELDS = ['username', 'email', 'full_name']
    SUGGEST_FIELDS = ['username', 'email', 'full_name'] 