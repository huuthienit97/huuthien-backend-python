from django_filters import rest_framework as filters
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Q, F
from .models import User


class UserFilter(filters.FilterSet):
    """Filter cho User với các tính năng nâng cao"""
    search = filters.CharFilter(method='search_filter')
    username = filters.CharFilter(lookup_expr='icontains')
    email = filters.CharFilter(lookup_expr='icontains')
    is_active = filters.BooleanFilter()
    date_joined = filters.DateTimeFromToRangeFilter()
    last_login = filters.DateTimeFromToRangeFilter()
    role = filters.ChoiceFilter(choices=User.ROLE_CHOICES)
    has_custom_role = filters.BooleanFilter(method='filter_has_custom_role')
    
    class Meta:
        model = User
        fields = [
            'search', 'username', 'email', 'is_active',
            'date_joined', 'last_login', 'role'
        ]
    
    def search_filter(self, queryset, name, value):
        """
        Tìm kiếm mờ sử dụng full-text search của PostgreSQL
        Kết quả được sắp xếp theo độ phù hợp
        """
        if not value:
            return queryset
            
        # Tạo search query với các từ khóa
        search_query = SearchQuery(value, config='simple')
        
        # Tính toán độ phù hợp của kết quả
        queryset = queryset.annotate(
            rank=SearchRank(F('search_vector'), search_query)
        ).filter(
            Q(search_vector=search_query) |  # Full-text search
            Q(username__icontains=value) |   # Fallback tìm kiếm thông thường
            Q(email__icontains=value) |
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value)
        ).order_by('-rank', 'username')
        
        return queryset
    
    def filter_has_custom_role(self, queryset, name, value):
        """Filter user có custom role hay không"""
        if value is True:
            return queryset.filter(custom_roles__isnull=False).distinct()
        elif value is False:
            return queryset.filter(custom_roles__isnull=True)
        return queryset